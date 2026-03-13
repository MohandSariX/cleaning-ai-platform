"""
Agent de qualification IA — Dialogue avec les prospects par email
Utilise Ollama/Mistral en local pour comprendre et qualifier les besoins
"""

import requests
import json
import re
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.prospect import Prospect
import logging

logger = logging.getLogger("proprexis.qualification")

OLLAMA_URL = "http://localhost:11434/api/generate"

# Grille tarifaire Proprexis
TARIFS = {
    "fin_chantier": {
        "base": 8.0,       # €/m²
        "min": 400,        # € minimum
        "description": "Nettoyage fin de chantier",
    },
    "bureaux_ponctuel": {
        "base": 4.5,       # €/m²
        "min": 150,
        "description": "Nettoyage bureaux ponctuel",
    },
    "bureaux_hebdo": {
        "base": 3.5,       # €/m²/semaine
        "min": 120,
        "description": "Nettoyage bureaux hebdomadaire",
    },
    "bureaux_mensuel": {
        "base": 2.5,       # €/m²/mois
        "min": 80,
        "description": "Nettoyage bureaux mensuel",
    },
    "copropriete": {
        "base": 2.0,       # €/m²/mois
        "min": 200,
        "description": "Entretien parties communes",
    },
}


def _call_ollama(prompt: str, max_tokens: int = 400) -> str:
    """Appelle Ollama Mistral et retourne le texte brut."""
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
        "IMPORTANT : Si l'historique montre qu'un devis vient d'être envoyé et que le message est court et positif, c'est un accuse.\n\n"
        "Categories :\n"
        "- accuse : bien reçu, merci, ok, je regarde, je réfléchis, à bientôt\n"
        "- interesse : intérêt général\n"
        "- devis : donne superficie/fréquence/type ou demande devis\n"
        "- question : pose une question\n"
        "- negociation : trop cher, remise\n"
        "- pas_interesse : refus\n"
        "- signature : accepte, on y va, je signe\n"
        "- incertain : impossible à classifier\n\n"
        'Réponds UNIQUEMENT avec ce JSON : {"categorie": "UNE_CATEGORIE"}'
    )
    raw = _call_ollama(prompt, max_tokens=30).strip()
    try:
        data = json.loads(re.search(r"{.*}", raw, re.DOTALL).group())
        cat = data.get("categorie", "incertain").lower()
        if cat in categories:
            return cat
    except Exception:
        pass
    return "incertain"


def extract_infos_from_message(message: str, prospect_context: dict) -> dict:
    """
    Utilise l'IA pour extraire les infos de qualification depuis un message.
    Retourne les infos trouvées et ce qui manque encore.
    """
    prompt = f"""Tu es un assistant qui analyse des emails de prospects pour une entreprise de nettoyage professionnel.

Contexte du prospect :
- Entreprise : {prospect_context.get('company_name', 'inconnue')}
- Secteur : {prospect_context.get('industry', 'inconnu')}
- Ville : {prospect_context.get('city', 'inconnue')}

Message reçu :
"{message}"

Extrais les informations suivantes si présentes dans le message.
Réponds UNIQUEMENT en JSON valide, sans markdown :
{{
  "type_prestation": "fin_chantier|bureaux|copropriete|null",
  "superficie_m2": nombre ou null,
  "frequence": "ponctuel|hebdo|mensuel|null",
  "ville": "ville mentionnée ou null",
  "disponibilite": "disponibilité mentionnée ou null",
  "infos_supplementaires": "autres infos utiles ou null",
  "intention": "interesse|demande_devis|question|pas_interesse|incertain"
}}"""

    raw = _call_ollama(prompt, max_tokens=300)

    try:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except:
        pass

    return {
        "type_prestation": None,
        "superficie_m2": None,
        "frequence": None,
        "ville": prospect_context.get('city'),
        "disponibilite": None,
        "infos_supplementaires": None,
        "intention": "incertain"
    }


def generate_qualification_email(prospect_context: dict, infos_connues: dict, historique: list) -> str:
    """
    Génère un email de qualification qui pose uniquement les questions manquantes.
    """
    questions_manquantes = []
    if not infos_connues.get("type_prestation"):
        questions_manquantes.append("type de prestation (fin de chantier, bureaux, parties communes...)")
    if not infos_connues.get("superficie_m2"):
        questions_manquantes.append("superficie approximative en m²")
    if not infos_connues.get("frequence"):
        questions_manquantes.append("fréquence souhaitée (intervention unique, hebdomadaire, mensuelle...)")

    if not questions_manquantes:
        return None  # Toutes les infos sont là, on peut faire le devis

    historique_str = "\n".join([f"- {h}" for h in historique[-3:]]) if historique else "Premier échange"

    prompt = f"""Tu es Mohand Sari de Proprexis, entreprise de nettoyage professionnel en Île-de-France.
Tu dois répondre à un prospect intéressé par tes services pour lui demander des informations manquantes.

Prospect : {prospect_context.get('company_name')} à {prospect_context.get('city', 'Île-de-France')}
Secteur : {prospect_context.get('industry', 'non précisé')}

Informations déjà connues :
{json.dumps({k: v for k, v in infos_connues.items() if v}, ensure_ascii=False)}

Questions à poser (seulement celles-ci, pas d'autres) :
{chr(10).join(f"- {q}" for q in questions_manquantes)}

Historique récent :
{historique_str}

Rédige un email court et professionnel en français (max 80 mots hors signature).

RÈGLES STRICTES :
- UNIQUEMENT en français, aucun mot en anglais, aucune traduction, aucune note
- Ne commence PAS par "Bonjour" (il sera ajouté automatiquement)
- Pas de "Note:", pas de "Translation:", pas de tirets "---"
- Remercie pour l'intérêt en une phrase
- Pose UNIQUEMENT les questions manquantes listées ci-dessus
- Termine par "Nous vous enverrons un devis sous 24h."
- STOP après cette phrase, rien d'autre

Réponds UNIQUEMENT avec le corps de l'email, rien d'autre."""

    body = _call_ollama(prompt, max_tokens=300)

    if not body:
        # Fallback sans IA
        body = f"Suite à votre intérêt pour nos services, afin de vous établir un devis précis, pourriez-vous nous préciser :\n\n"
        for q in questions_manquantes:
            body += f"• {q.capitalize()}\n"
        body += "\nNous vous adresserons votre devis sous 24h."

    # Nettoyer les artefacts Mistral
    import re as _re
    body = _re.sub(r'---.*', '', body, flags=_re.DOTALL).strip()
    body = _re.sub(r'Note[\s]*[\d]*[\s]*:.*', '', body, flags=_re.DOTALL).strip()
    body = body.replace("Bonjour,", "").replace("Bonjour ,", "").strip()

    email = f"""Bonjour,

{body}

Cordialement,
Mohand Sari — Proprexis
contact.proprexis@gmail.com | 06 XX XX XX XX"""

    return email


def calculate_devis(infos: dict) -> dict:
    """Calcule le montant du devis selon les infos collectées."""
    type_p = infos.get("type_prestation", "bureaux")
    superficie = infos.get("superficie_m2") or 100
    frequence = infos.get("frequence", "ponctuel")

    # Déterminer la clé tarifaire
    if type_p == "fin_chantier":
        cle = "fin_chantier"
    elif type_p == "copropriete":
        cle = "copropriete"
    elif frequence == "hebdo":
        cle = "bureaux_hebdo"
    elif frequence == "mensuel":
        cle = "bureaux_mensuel"
    else:
        cle = "bureaux_ponctuel"

    tarif = TARIFS.get(cle, TARIFS["bureaux_ponctuel"])
    montant_ht = max(tarif["min"], superficie * tarif["base"])
    montant_ht = round(montant_ht, 2)

    return {
        "type_prestation": type_p,
        "description": tarif["description"],
        "superficie_m2": superficie,
        "frequence": frequence,
        "montant_ht": montant_ht,
        "tva_pct": 20.0,
        "montant_ttc": round(montant_ht * 1.2, 2),
        "cle_tarif": cle,
    }


def needs_human_intervention(message: str, infos: dict, nb_echanges: int) -> tuple:
    """
    Détermine si un humain doit intervenir.
    Retourne (bool, raison)
    """
    message_lower = message.lower()

    # Négociation de prix
    if any(x in message_lower for x in ["trop cher", "négoci", "negoci", "réduire", "moins cher", "remise", "discount"]):
        return True, "négociation prix"

    # Gros chantier
    superficie = infos.get("superficie_m2")
    if superficie and superficie > 2000:
        return True, f"grand chantier ({superficie}m²) — visite recommandée"

    # Trop d'échanges sans aboutir
    if nb_echanges >= 4:
        return True, "4 échanges sans devis finalisé"

    return False, None


# ── Stockage des conversations en cours ──────────────────────────────────────
# { email: { "infos": {}, "historique": [], "nb_echanges": 0 } }
conversations = {}

# Emails ayant déjà reçu un devis — on ignore leurs messages tant qu'ils n'ont pas signé
devis_envoyes = set()


def process_qualification(prospect: Prospect, message: str, service, sujet: str = "") -> str:
    """
    Point d'entrée principal — gère le dialogue de qualification complet.
    Retourne l'action effectuée.
    """
    from app.agents.telegram_notifier import send_message as tg
    from app.agents.gmail_agent import send_email, generate_auto_devis

    email = prospect.email
    CRM_URL = "http://localhost:3000"

    # Initialiser la conversation si nouvelle (avant classification)
    if email not in conversations:
        conversations[email] = {
            "infos": {
                "ville": prospect.city,
                "type_prestation": None,
                "superficie_m2": None,
                "frequence": None,
            },
            "historique": [],
            "nb_echanges": 0,
        }

    conv = conversations[email]

    # Classifier l'intention avec l'IA
    contexte = f"Devis déjà envoyé à {prospect.company_name}" if email in devis_envoyes else f"Prospect : {prospect.company_name}, {prospect.city}"
    historique_complet = conv.get("historique", [])
    intention_ia = classify_message_ia(message, sujet=sujet, contexte=contexte, historique=historique_complet)
    print(f"🧠 Intention IA : {intention_ia}")

    # Signature → notifier Telegram et clore
    if intention_ia == "signature":
        from app.agents.telegram_notifier import send_message as tg
        tg(
            f"🎉 *Devis accepté !*\n\n"
            f"Client : *{prospect.company_name}* ({prospect.city})\n"
            f"Message : _{message[:200]}_\n\n"
            f"→ [Créer le chantier]({CRM_URL}/chantiers)"
        )
        devis_envoyes.discard(email)
        return "signed"

    # Accusé de réception → ignorer
    if intention_ia == "accuse":
        print(f"📭 Accusé ignoré de {email}")
        return "acknowledgement_ignored"

    # Pas intéressé → mettre statut lost
    if intention_ia == "pas_interesse":
        db2 = SessionLocal()
        try:
            p2 = db2.query(Prospect).filter(Prospect.email == email).first()
            if p2:
                p2.status = "lost"
                db2.commit()
        finally:
            db2.close()
        devis_envoyes.discard(email)
        return "lost"

    # Négociation → intervention humaine
    if intention_ia == "negociation":
        from app.agents.telegram_notifier import send_message as tg
        tg(
            f"💬 *Négociation en cours*\n\n"
            f"Client : *{prospect.company_name}* ({prospect.city})\n"
            f"_{message[:300]}_\n\n"
            f"Réponds depuis Gmail."
        )
        return "human_required"

    # Si devis déjà envoyé et nouvelle demande → recommencer qualification
    if email in devis_envoyes:
        if intention_ia in ("devis", "interesse", "question"):
            devis_envoyes.discard(email)
        else:
            return "acknowledgement_ignored"

    # Initialiser la conversation si nouvelle
    if email not in conversations:
        conversations[email] = {
            "infos": {
                "ville": prospect.city,
                "type_prestation": None,
                "superficie_m2": None,
                "frequence": None,
            },
            "historique": [],
            "nb_echanges": 0,
        }

    conv = conversations[email]

    # (classification déjà effectuée ci-dessus)

    conv["nb_echanges"] += 1
    conv["historique"].append(f"Prospect [{sujet[:50] if sujet else 'sans sujet'}]: {message[:200]}")

    # Extraire les infos du message avec l'IA
    prospect_context = {
        "company_name": prospect.company_name,
        "industry": prospect.industry,
        "city": prospect.city,
    }
    nouvelles_infos = extract_infos_from_message(message, prospect_context)

    # Fusionner avec les infos déjà connues
    for key in ["type_prestation", "superficie_m2", "frequence", "ville"]:
        if nouvelles_infos.get(key):
            conv["infos"][key] = nouvelles_infos[key]

    infos = conv["infos"]

    # Vérifier si intervention humaine nécessaire
    besoin_humain, raison = needs_human_intervention(message, infos, conv["nb_echanges"])
    if besoin_humain:
        tg(
            f"🙋 *Intervention requise*\n\n"
            f"Client : *{prospect.company_name}* ({prospect.city})\n"
            f"Raison : {raison}\n"
            f"Échanges : {conv['nb_echanges']}\n\n"
            f"_{message[:300]}_\n\n"
            f"→ [Voir le prospect]({CRM_URL}/prospects/{prospect.id})\n"
            f"Réponds depuis Gmail directement."
        )
        return "human_required"

    # Vérifier si on a toutes les infos pour faire le devis
    infos_completes = all([
        infos.get("type_prestation"),
        infos.get("superficie_m2"),
        infos.get("frequence"),
    ])

    if infos_completes:
        # Générer le devis avec les vrais chiffres
        calcul = calculate_devis(infos)
        db = SessionLocal()
        try:
            devis, pdf_path, client = generate_auto_devis(
                prospect, db,
                montant_ht_override=calcul["montant_ht"],
                description_override=f"{calcul['description']} — {infos.get('superficie_m2')}m²",
                service_type_override=calcul["type_prestation"],
            )

            email_body = f"""Bonjour,

Suite à notre échange, veuillez trouver ci-joint votre devis personnalisé.

Récapitulatif :
• Prestation : {calcul['description']}
• Superficie : {infos.get('superficie_m2')} m²
• Fréquence : {infos.get('frequence', 'ponctuel')}
• Montant HT : {calcul['montant_ht']:,.2f} €
• Montant TTC : {calcul['montant_ttc']:,.2f} €

Ce devis est valable 30 jours. N'hésitez pas à nous contacter pour toute question.

Cordialement,
Mohand Sari — Proprexis
contact.proprexis@gmail.com | 06 XX XX XX XX"""

            send_email(service, to=email, subject=f"Votre devis Proprexis — {devis.numero}", body=email_body, pdf_path=pdf_path)

            # Marquer le devis comme envoyé et nettoyer la conversation
            devis_envoyes.add(email)
            del conversations[email]

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
        # Poser les questions manquantes
        email_body = generate_qualification_email(prospect_context, infos, conv["historique"])
        if email_body:
            send_email(service, to=email, subject="Re: Votre demande de nettoyage — Proprexis", body=email_body)
            conv["historique"].append(f"Proprexis [Re: qualification]: {email_body[:200]}")
            return "qualification_sent"

    return "no_action"