"""
Agent Gmail — Surveille la boîte contact.proprexis@gmail.com
- Lit les nouvelles réponses aux emails de prospection
- Détecte l'intention (intéressé, devis, question, pas intéressé)
- Génère et envoie le devis automatiquement
- Notifie sur Telegram
"""

import os
import base64
import json
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.prospect import Prospect
from app.models.client import Client
from app.models.devis import Devis
from app.agents.telegram_notifier import send_message
from app.agents.qualification_agent import process_qualification
import logging

logger = logging.getLogger("proprexis.gmail")

SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOKEN_PATH = os.path.join(BASE_DIR, 'token.json')
CREDS_PATH = os.path.join(BASE_DIR, 'credentials.json')
CRM_URL = "http://localhost:3000"


def get_gmail_service():
    """Retourne un service Gmail authentifié."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_PATH, 'w') as f:
                f.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)


def detect_intention(subject: str, body: str) -> dict:
    """
    Analyse le texte d'une réponse et détecte l'intention.
    Retourne {"intention": "...", "confidence": 0-1}
    """
    text = f"{subject} {body}".lower()

    # Mots-clés par intention
    interesse_mots = [
        "intéressé", "interesse", "interessé", "oui", "volontiers", "bien sûr", "pourquoi pas",
        "contactez", "rappeler", "rappel", "disponible", "rendez-vous", "rdv",
        "quand", "disponibilité", "venez", "passez"
    ]
    devis_mots = [
        "devis", "tarif", "prix", "combien", "coût", "cout", "estimation",
        "offre", "proposition", "budget"
    ]
    question_mots = [
        "?", "comment", "quoi", "quel", "quelle", "pourquoi", "zone",
        "secteur", "type", "prestation", "service", "intervention"
    ]
    pas_interesse_mots = [
        "non merci", "pas intéressé", "pas interesse", "ne pas recontacter",
        "désinscri", "desinscri", "stop", "unsubscribe", "retirer",
        "prestataire", "déjà", "deja", "contrat en cours", "satisfait"
    ]

    score_interesse = sum(1 for m in interesse_mots if m in text)
    score_devis = sum(1 for m in devis_mots if m in text)
    score_question = sum(1 for m in question_mots if m in text)
    score_pas = sum(1 for m in pas_interesse_mots if m in text)

    if score_pas >= 1:
        return {"intention": "pas_interesse", "confidence": 0.9}
    if score_devis >= 1:
        return {"intention": "demande_devis", "confidence": 0.85}
    if score_interesse >= 1:
        return {"intention": "interesse", "confidence": 0.8}
    if score_question >= 2:
        return {"intention": "question", "confidence": 0.7}

    return {"intention": "incertain", "confidence": 0.5}


def get_email_body(msg_payload) -> str:
    """Extrait le texte brut d'un message Gmail."""
    body = ""
    if msg_payload.get('body', {}).get('data'):
        body = base64.urlsafe_b64decode(msg_payload['body']['data']).decode('utf-8', errors='ignore')
    elif msg_payload.get('parts'):
        for part in msg_payload['parts']:
            if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                break
    return body[:2000]  # Limiter à 2000 chars


def send_email(service, to: str, subject: str, body: str, pdf_path: str = None):
    """Envoie un email avec pièce jointe optionnelle."""
    msg = MIMEMultipart()
    msg['to'] = to
    msg['subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(pdf_path)}"')
            msg.attach(part)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId='me', body={'raw': raw}).execute()


def generate_auto_devis(prospect: Prospect, db: Session,
                        montant_ht_override: float = None,
                        description_override: str = None,
                        service_type_override: str = None) -> tuple:
    """
    Génère automatiquement un devis pour un prospect intéressé.
    Retourne (devis_obj, pdf_path, client)
    """
    from app.utils.pdf_generator import generate_devis_pdf

    # Créer ou récupérer le client
    client = db.query(Client).filter(Client.company_name == prospect.company_name).first()
    if not client:
        client = Client(
            prospect_id=prospect.id,
            company_name=prospect.company_name,
            email=prospect.email,
            phone=prospect.phone,
            address=prospect.address,
            city=prospect.city,
            status="actif",
        )
        db.add(client)
        db.flush()

    # Numéro de devis auto
    year = datetime.now().year
    last = db.query(Devis).filter(Devis.numero.like(f"DEV-{year}-%")).count()
    numero = f"DEV-{year}-{str(last + 1).zfill(3)}"

    # Utiliser les overrides si fournis, sinon déduire du secteur
    if montant_ht_override and description_override and service_type_override:
        service_type = service_type_override
        description = description_override
        montant_ht = montant_ht_override
    else:
        industry = (prospect.industry or "").lower()
        if any(x in industry for x in ["construct", "promo", "rénov", "renov", "architect"]):
            service_type = "fin_chantier"
            description = "Nettoyage complet de fin de chantier — évacuation gravats, dégraissage sols, nettoyage vitrages, remise en état avant livraison"
            montant_ht = 850.0
        elif any(x in industry for x in ["immo", "syndic", "copro"]):
            service_type = "copropriete"
            description = "Entretien régulier des parties communes — hall, couloirs, escaliers, locaux poubelles (contrat mensuel)"
            montant_ht = 450.0
        else:
            service_type = "bureaux"
            description = "Nettoyage professionnel de locaux — bureaux, sanitaires, espaces communs (prestation hebdomadaire)"
            montant_ht = 320.0

    devis = Devis(
        client_id=client.id,
        numero=numero,
        service_type=service_type,
        description=description,
        montant_ht=montant_ht,
        tva_pct=20.0,
        status="envoye",
        sent_at=datetime.now(),
    )
    db.add(devis)
    db.commit()

    # Générer le PDF
    devis_data = {
        "numero": numero,
        "description": description,
        "service_type": service_type,
        "montant_ht": montant_ht,
        "tva_pct": 20.0,
        "status": "envoye",
        "created_at": datetime.now().strftime("%d/%m/%Y"),
    }
    client_data = {
        "company_name": client.company_name,
        "contact_name": client.contact_name or "",
        "address": client.address or "",
        "city": client.city or "",
        "email": client.email or "",
        "phone": client.phone or "",
    }

    pdf_bytes = generate_devis_pdf(devis_data, client_data)
    pdf_path = f"/tmp/devis_{numero}.pdf"
    with open(pdf_path, 'wb') as f:
        f.write(pdf_bytes)

    return devis, pdf_path, client


def handle_reply(service, msg_id: str, sender: str, subject: str, body: str):
    """Traite une réponse reçue."""
    print(f"📩 Traitement email de : {sender} | Sujet : {subject}")
    db = SessionLocal()
    try:
        # Trouver le prospect correspondant
        prospect = db.query(Prospect).filter(Prospect.email == sender).first()
        if not prospect:
            print(f"⚠️ Prospect inconnu pour {sender} — ignoré")
            return
        print(f"✅ Prospect trouvé : {prospect.company_name}")

        intention = detect_intention(subject, body)
        logger.info(f"Réponse de {prospect.company_name} — intention: {intention['intention']}")

        if intention["intention"] == "pas_interesse":
            prospect.status = "lost"
            db.commit()
            send_message(
                f"📭 *Pas intéressé*\n"
                f"{prospect.company_name} — {prospect.city}\n"
                f"Statut mis à jour → Perdu"
            )

        elif intention["intention"] in ("demande_devis", "interesse"):
            # Lancer la qualification IA — pose les questions manquantes avant de faire le devis
            prospect.status = "replied"
            db.commit()
            action = process_qualification(prospect, body, service, sujet=subject)
            print(f"✅ Qualification : {action}")

        elif intention["intention"] == "question":
            prospect.status = "replied"
            db.commit()
            # Notifier pour réponse manuelle
            send_message(
                f"❓ *Question reçue — intervention requise*\n\n"
                f"De : *{prospect.company_name}* ({prospect.city})\n"
                f"Email : {sender}\n\n"
                f"_{body[:300]}_\n\n"
                f"→ [Voir le prospect]({CRM_URL}/prospects/{prospect.id})\n"
                f"Réponds directement depuis Gmail."
            )

        else:  # incertain
            send_message(
                f"📬 *Réponse reçue — intention incertaine*\n\n"
                f"De : *{prospect.company_name}* ({prospect.city})\n\n"
                f"_{body[:300]}_\n\n"
                f"→ [Voir le prospect]({CRM_URL}/prospects/{prospect.id})"
            )

        # Marquer comme lu
        service.users().messages().modify(
            userId='me',
            id=msg_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()

    except Exception as e:
        logger.error(f"Erreur traitement réponse : {e}")
        import traceback; traceback.print_exc()
    finally:
        db.close()


def check_inbox():
    """
    Vérifie les nouveaux emails non lus et traite les réponses.
    Appelé toutes les 15 minutes par le scheduler.
    """
    try:
        print("📬 check_inbox démarré")
        service = get_gmail_service()
        print("✅ Service Gmail OK")
        results = service.users().messages().list(
            userId='me',
            labelIds=['INBOX', 'UNREAD'],
            maxResults=20
        ).execute()

        messages = results.get('messages', [])
        print(f"📨 {len(messages)} email(s) non lu(s) trouvé(s)")
        if not messages:
            print("📭 Boîte vide ou tous lus")
            return

        print(f"📬 {len(messages)} nouveau(x) email(s) non lu(s)")

        for msg_meta in messages:
            msg = service.users().messages().get(
                userId='me',
                id=msg_meta['id'],
                format='full'
            ).execute()

            headers = {h['name']: h['value'] for h in msg['payload'].get('headers', [])}
            sender_full = headers.get('From', '')
            subject = headers.get('Subject', '')

            # Extraire l'email du sender
            match = re.search(r'<(.+?)>', sender_full)
            sender_email = match.group(1) if match else sender_full

            # Ignorer nos propres emails
            if 'proprexis' in sender_email.lower():
                continue

            body = get_email_body(msg['payload'])
            handle_reply(service, msg_meta['id'], sender_email, subject, body)

    except Exception as e:
        logger.error(f"Erreur check_inbox : {e}")


def send_prospection_email(to: str, subject: str, body: str) -> bool:
    """Envoie un email de prospection depuis la boîte Gmail."""
    try:
        service = get_gmail_service()
        send_email(service, to=to, subject=subject, body=body)
        return True
    except Exception as e:
        logger.error(f"Erreur envoi prospection : {e}")
        return False