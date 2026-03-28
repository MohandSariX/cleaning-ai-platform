"""
Agent de qualification IA — Dialogue avec les prospects par email
Utilise Ollama/phi3:mini en local pour comprendre et qualifier les besoins
Persistance PostgreSQL via ConversationStore
"""

import requests
import json
import re
from datetime import datetime
from app.core.database import SessionLocal
from app.models.prospect import Prospect
from app.agents.conversation_store import store
from app.agents.activity_logger import log_qualification, log_devis, log_error
import logging

logger = logging.getLogger("proprexis.qualification")

OLLAMA_URL = "http://localhost:11434/api/generate"
CRM_URL = "http://localhost:3000"

from app.utils.devis_engine import calculate as engine_calculate, get_questions_manquantes


def _call_ollama(prompt: str, max_tokens: int = 400) -> str:
    """Appelle Ollama phi3:mini et retourne le texte brut."""
    try:
        res = requests.post(
            OLLAMA_URL,
            json={
                "model": "phi3:mini",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": max_tokens}
            },
            timeout=120
        )
        return res.json()["response"].strip()
    except Exception as e:
        logger.error(f"Ollama erreur : {e}")
        return ""


def classify_message_ia(message: str, sujet: str = "", contexte: str = "", historique: list = None) -> str:
    """
    Utilise l'IA pour classifier l'intention d'un message.
    Retourne : accuse | interesse | devis | question | negociation | pas_interesse | signature | incertain
    """
    categories = ["accuse", "interesse", "devis", "question", "negociation", "pas_interesse", "signature", "incertain"]

    historique_str = ""
    if historique:
        historique_str = "\nHistorique des échanges :\n" + "\n".join(f"  - {h}" for h in historique[-10:])

    prompt = (
        "Tu analyses un email pour une entreprise de nettoyage professionnel.\n"
        f"Contexte : {contexte if contexte else 'Premier contact'}\n"
        f"{historique_str}\n"
        f"Sujet : {sujet if sujet else 'sans sujet'}\n"
        f"Corps : {message}\n\n"
        "RÈGLES IMPORTANTES :\n"
        "- accuse = message passif sans engagement : bien reçu, merci, je vais réfléchir, à bientôt, je l'étudie\n"
        "- signature = message actif avec engagement : on y va, je suis d'accord, c'est ok, on commence, je valide, je signe\n"
        "- Si l'historique montre qu'un devis vient d'être envoyé et que le message est court et positif = accuse\n\n"
        "Categories :\n"
        "- accuse : remerciement passif, confirmation réception sans engagement\n"
        "- interesse : intérêt général sans demande précise\n"
        "- devis : donne superficie/fréquence/type ou demande un devis\n"
        "- question : pose une question sur services, prix, zone\n"
        "- negociation : trop cher, demande remise ou réduction\n"
        "- pas_interesse : refus, stop, ne plus contacter\n"
        "- signature : accepte le devis, confirme vouloir commencer, donne son accord clair\n"
        "- incertain : vraiment impossible à classifier\n\n"
        'Réponds UNIQUEMENT avec ce JSON : {"categorie": "UNE_CATEGORIE"}'
    )

    raw = _call_ollama(prompt, max_tokens=30).strip()
    # Nettoyer les backticks markdown que phi3:mini ajoute parfois
    raw = re.sub(r"```json|```", "", raw).strip()
    try:
        data = json.loads(re.search(r"{.*}", raw, re.DOTALL).group())
        cat = data.get("categorie", "incertain").lower()
        if cat in categories:
            # Filet de sécurité signature
            if cat == "interesse":
                msg_lower = message.lower()
                signature_forts = [
                    "on y va", "je suis d'accord", "c'est ok pour moi",
                    "on commence", "je valide", "marché conclu", "deal",
                    "vous pouvez venir", "on peut démarrer", "c'est bon pour moi"
                ]
                if any(s in msg_lower for s in signature_forts):
                    return "signature"
            return cat
    except Exception:
        pass
    return "incertain"


def extract_infos_from_message(message: str, prospect_context: dict) -> dict:
    """Utilise l'IA pour extraire les infos de qualification depuis un message."""
    prompt = (
        "Tu es un assistant qui analyse des emails pour une entreprise de nettoyage professionnel.\n\n"
        f"Contexte du prospect :\n"
        f"- Entreprise : {prospect_context.get('company_name', 'inconnue')}\n"
        f"- Secteur : {prospect_context.get('industry', 'inconnu')}\n"
        f"- Ville : {prospect_context.get('city', 'inconnue')}\n\n"
        f"Message reçu :\n\"{message}\"\n\n"
        "Extrais les informations suivantes si présentes.\n"
        "Réponds UNIQUEMENT en JSON valide, sans markdown :\n"
        '{"type_prestation": "fin_chantier|bureaux|copropriete|null", '
        '"superficie_m2": nombre_ou_null, '
        '"frequence": "ponctuel|hebdo|mensuel|null", '
        '"ville": "ville_ou_null", '
        '"intention": "interesse|demande_devis|question|pas_interesse|incertain"}'
    )
    raw = _call_ollama(prompt, max_tokens=200)
    raw = re.sub(r"```json|```", "", raw).strip()
    try:
        match = re.search(r"{.*}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return {
        "type_prestation": None, "superficie_m2": None,
        "frequence": None, "ville": prospect_context.get("city"),
        "intention": "incertain"
    }


def generate_qualification_email(prospect_context: dict, infos_connues: dict, historique: list) -> str | None:
    """Génère un email de qualification qui pose uniquement les questions manquantes."""
    type_p = infos_connues.get("type_prestation") or "bureaux"
    questions_manquantes = get_questions_manquantes(type_p, infos_connues)

    if not questions_manquantes:
        return None

    historique_str = "\n".join([f"- {h}" for h in historique[-3:]]) if historique else "Premier échange"

    prompt = (
        f"Tu es Mohand Sari de Proprexis, entreprise de nettoyage professionnel en Île-de-France.\n"
        f"Prospect : {prospect_context.get('company_name')} à {prospect_context.get('city', 'Île-de-France')}\n"
        f"Secteur : {prospect_context.get('industry', 'non précisé')}\n\n"
        f"Informations déjà connues : {json.dumps({k: v for k, v in infos_connues.items() if v}, ensure_ascii=False)}\n\n"
        f"Questions à poser :\n" + "\n".join(f"- {q}" for q in questions_manquantes) + "\n\n"
        f"Historique récent :\n{historique_str}\n\n"
        "RÈGLES STRICTES :\n"
        "- UNIQUEMENT en français, aucun mot en anglais, aucune note, aucune traduction\n"
        "- Ne commence PAS par Bonjour\n"
        "- Pas de Note:, pas de tirets ---\n"
        "- Remercie en une phrase, pose les questions, termine par 'Nous vous enverrons un devis sous 24h.'\n"
        "- STOP après cette phrase\n\n"
        "Réponds UNIQUEMENT avec le corps de l'email, rien d'autre."
    )

    body = _call_ollama(prompt, max_tokens=300)

    if not body:
        body = "Merci de votre intérêt.\n\nPourriez-vous nous préciser :\n"
        for q in questions_manquantes:
            body += f"• {q.capitalize()}\n"
        body += "\nNous vous enverrons un devis sous 24h."

    # Nettoyer les artefacts
    body = re.sub(r"---.*", "", body, flags=re.DOTALL).strip()
    body = re.sub(r"Note[\s]*[\d]*[\s]*:.*", "", body, flags=re.DOTALL).strip()
    body = body.replace("Bonjour,", "").replace("Bonjour ,", "").strip()

    return f"Bonjour,\n\n{body}\n\nCordialement,\nMohand Sari — Proprexis\ncontact.proprexis@gmail.com | 06 XX XX XX XX"


def calculate_devis(infos: dict) -> dict:
    """Calcule le montant du devis via le moteur devis_rules.json."""
    type_p = infos.get("type_prestation") or "bureaux"
    superficie = infos.get("superficie_m2") or 100
    frequence = infos.get("frequence") or "ponctuel"
    return engine_calculate(type_p, superficie, frequence)


def needs_human_intervention(message: str, infos: dict, nb_echanges: int) -> tuple:
    """Détermine si un humain doit intervenir. Retourne (bool, raison)"""
    msg = message.lower()
    if any(x in msg for x in ["trop cher", "négoci", "negoci", "réduire", "moins cher", "remise"]):
        return True, "négociation prix"
    superficie = infos.get("superficie_m2")
    if superficie and superficie > 2000:
        return True, f"grand chantier ({superficie}m²) — visite recommandée"
    if nb_echanges >= 4:
        return True, "4 échanges sans devis finalisé"
    return False, None


def process_qualification(prospect: Prospect, message: str, service, sujet: str = "") -> str:
    """Point d'entrée principal — gère le dialogue de qualification complet."""
    from app.agents.telegram_notifier import send_message as tg
    from app.agents.gmail_agent import send_email, generate_auto_devis

    email = prospect.email

    # Charger ou créer la conversation depuis PostgreSQL
    conv = store.get_or_create(prospect)

    # Classifier l'intention avec l'IA
    devis_deja_envoye = store.is_devis_envoye(email)
    contexte = f"Devis déjà envoyé à {prospect.company_name}" if devis_deja_envoye else f"Prospect : {prospect.company_name}, {prospect.city}"
    historique_complet = conv.get("historique", [])
    intention_ia = classify_message_ia(message, sujet=sujet, contexte=contexte, historique=historique_complet)
    print(f"🧠 Intention IA : {intention_ia}")

    # Signature
    if intention_ia == "signature":
        tg(
            f"🎉 *Devis accepté !*\n\n"
            f"Client : *{prospect.company_name}* ({prospect.city})\n"
            f"Message : _{message[:200]}_\n\n"
            f"→ [Créer le chantier]({CRM_URL}/chantiers)"
        )
        store.mark_signe(email)
        log_qualification(prospect.id, prospect.company_name, "signed", ia_decision=f"IA: {intention_ia}")
        return "signed"

    # Accusé de réception
    if intention_ia == "accuse":
        print(f"📭 Accusé ignoré de {email}")
        return "acknowledgement_ignored"

    # Pas intéressé
    if intention_ia == "pas_interesse":
        db = SessionLocal()
        try:
            p = db.query(Prospect).filter(Prospect.email == email).first()
            if p:
                p.status = "lost"
                db.commit()
        finally:
            db.close()
        store.mark_perdu(email)
        log_qualification(prospect.id, prospect.company_name, "lost", ia_decision=f"IA: {intention_ia}")
        return "lost"

    # Négociation
    if intention_ia == "negociation":
        tg(
            f"💬 *Négociation en cours*\n\n"
            f"Client : *{prospect.company_name}* ({prospect.city})\n"
            f"_{message[:300]}_\n\n"
            f"Réponds depuis Gmail."
        )
        return "human_required"

    # Si devis déjà envoyé et nouvelle demande
    if devis_deja_envoye:
        if intention_ia in ("devis", "interesse", "question"):
            store.mark_perdu(email)  # reset
        else:
            return "acknowledgement_ignored"

    # Mettre à jour l'historique
    nb_echanges = conv["nb_echanges"] + 1
    historique = conv["historique"] + [f"Prospect [{sujet[:50] if sujet else 'sans sujet'}]: {message[:200]}"]
    store.update(email, nb_echanges=nb_echanges, historique=historique)
    conv["nb_echanges"] = nb_echanges
    conv["historique"] = historique

    # Extraire les infos
    prospect_context = {
        "company_name": prospect.company_name,
        "industry": prospect.industry,
        "city": prospect.city,
    }
    nouvelles_infos = extract_infos_from_message(message, prospect_context)
    print(f"📋 Infos extraites : {nouvelles_infos}")
    print(f"📋 Infos conversation : {conv['infos']}")

    infos = conv["infos"]
    updated = False
    for key in ["type_prestation", "superficie_m2", "frequence", "ville"]:
        if nouvelles_infos.get(key):
            infos[key] = nouvelles_infos[key]
            updated = True
    if updated:
        store.update(email, infos=infos)

    # Vérifier intervention humaine
    besoin_humain, raison = needs_human_intervention(message, infos, nb_echanges)
    if besoin_humain:
        tg(
            f"🙋 *Intervention requise*\n\n"
            f"Client : *{prospect.company_name}* ({prospect.city})\n"
            f"Raison : {raison}\n\n"
            f"_{message[:300]}_\n\n"
            f"→ [Voir le prospect]({CRM_URL}/prospects/{prospect.id})"
        )
        return "human_required"

    # Vérifier si on a toutes les infos
    infos_completes = all([infos.get("type_prestation"), infos.get("superficie_m2"), infos.get("frequence")])

    if infos_completes:
        calcul = calculate_devis(infos)
        db = SessionLocal()
        try:
            devis, pdf_path, client = generate_auto_devis(
                prospect, db,
                montant_ht_override=calcul["montant_ht"],
                description_override=f"{calcul['description']} — {infos.get('superficie_m2')}m²",
                service_type_override=calcul["type_prestation"],
            )

            email_body = (
                f"Bonjour,\n\n"
                f"Suite à notre échange, veuillez trouver ci-joint votre devis personnalisé.\n\n"
                f"Récapitulatif :\n"
                f"• Prestation : {calcul['description']}\n"
                f"• Superficie : {infos.get('superficie_m2')} m²\n"
                f"• Fréquence : {infos.get('frequence', 'ponctuel')}\n"
                f"• Montant HT : {calcul['montant_ht']:,.2f} €\n"
                f"• Montant TTC : {calcul['montant_ttc']:,.2f} €\n\n"
                f"Ce devis est valable 30 jours.\n\n"
                f"Cordialement,\nMohand Sari — Proprexis\n"
                f"contact.proprexis@gmail.com | 06 XX XX XX XX"
            )

            # Générer et joindre les CGV
            from app.utils.cgv_annexe import generate_cgv_pdf
            cgv_path = f"/tmp/cgv_proprexis.pdf"
            with open(cgv_path, 'wb') as f:
                f.write(generate_cgv_pdf())

            send_email(service, to=email, subject=f"Votre devis Proprexis — {devis.numero}",
                      body=email_body, pdf_path=pdf_path, cgv_path=cgv_path)

            historique_final = historique + [f"Proprexis [Votre devis {devis.numero}]: Devis envoyé — {calcul['montant_ttc']:.0f}€ TTC"]
            store.update(email, historique=historique_final)
            store.mark_devis_envoye(email)
            log_devis(prospect.id, prospect.company_name, devis.numero, calcul["montant_ttc"], calcul["type_prestation"])

            tg(
                f"🎯 *Devis envoyé !*\n\n"
                f"Client : *{prospect.company_name}*\n"
                f"Prestation : {calcul['description']}\n"
                f"Superficie : {infos.get('superficie_m2')}m²\n"
                f"Montant : *{calcul['montant_ttc']:,.0f} € TTC*\n\n"
                f"→ [Voir le devis]({CRM_URL}/devis)"
            )
            return "devis_sent"
        finally:
            db.close()
    else:
        email_body = generate_qualification_email(prospect_context, infos, historique)
        if email_body:
            send_email(service, to=email, subject="Re: Votre demande de nettoyage — Proprexis", body=email_body)
            hist = historique + [f"Proprexis [Re: qualification]: {email_body[:200]}"]
            store.update(email, historique=hist)
            log_qualification(prospect.id, prospect.company_name, "qualification_sent", infos=infos)
            return "qualification_sent"

    return "no_action"