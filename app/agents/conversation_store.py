"""
ConversationStore — Interface de persistance des conversations.
Remplace le dict en mémoire par des opérations PostgreSQL.
"""
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.conversation import Conversation
from app.models.prospect import Prospect


class ConversationStore:
    """
    Gère la persistance des conversations de qualification.
    Thread-safe — chaque opération ouvre/ferme sa propre session.
    """

    def get(self, email: str) -> dict | None:
        """Récupère une conversation par email. Retourne None si inexistante."""
        db = SessionLocal()
        try:
            conv = db.query(Conversation).filter(Conversation.email == email).first()
            if not conv:
                return None
            return {
                "infos": json.loads(conv.infos_json or "{}"),
                "historique": json.loads(conv.historique_json or "[]"),
                "nb_echanges": conv.nb_echanges,
                "status": conv.status,
                "prospect_id": conv.prospect_id,
            }
        finally:
            db.close()

    def create(self, prospect: Prospect) -> dict:
        """Crée une nouvelle conversation pour un prospect."""
        db = SessionLocal()
        try:
            # Vérifier si elle existe déjà
            existing = db.query(Conversation).filter(
                Conversation.email == prospect.email
            ).first()
            if existing:
                return self.get(prospect.email)

            infos_initiales = {
                "ville": prospect.city,
                "type_prestation": None,
                "superficie_m2": None,
                "frequence": None,
            }
            conv = Conversation(
                prospect_id=prospect.id,
                email=prospect.email,
                status="en_cours",
                infos_json=json.dumps(infos_initiales),
                historique_json="[]",
                nb_echanges=0,
            )
            db.add(conv)
            db.commit()
            return {
                "infos": infos_initiales,
                "historique": [],
                "nb_echanges": 0,
                "status": "en_cours",
                "prospect_id": prospect.id,
            }
        finally:
            db.close()

    def update(self, email: str, infos: dict = None, historique: list = None,
               nb_echanges: int = None, status: str = None):
        """Met à jour une conversation existante."""
        db = SessionLocal()
        try:
            conv = db.query(Conversation).filter(Conversation.email == email).first()
            if not conv:
                return
            if infos is not None:
                conv.infos_json = json.dumps(infos)
            if historique is not None:
                conv.historique_json = json.dumps(historique[-20:])  # Garder 20 derniers
            if nb_echanges is not None:
                conv.nb_echanges = nb_echanges
            if status is not None:
                conv.status = status
                if status == "devis_envoye":
                    conv.devis_envoye_at = datetime.now()
            db.commit()
        finally:
            db.close()

    def mark_devis_envoye(self, email: str):
        """Marque la conversation comme devis envoyé."""
        self.update(email, status="devis_envoye")

    def mark_signe(self, email: str):
        """Marque la conversation comme signée."""
        self.update(email, status="signe")

    def mark_perdu(self, email: str):
        """Marque la conversation comme perdue."""
        self.update(email, status="perdu")

    def delete(self, email: str):
        """Supprime une conversation (utilisé après signature ou perte)."""
        db = SessionLocal()
        try:
            db.query(Conversation).filter(Conversation.email == email).delete()
            db.commit()
        finally:
            db.close()

    def is_devis_envoye(self, email: str) -> bool:
        """Vérifie si un devis a déjà été envoyé à cet email."""
        db = SessionLocal()
        try:
            conv = db.query(Conversation).filter(
                Conversation.email == email,
                Conversation.status == "devis_envoye"
            ).first()
            return conv is not None
        finally:
            db.close()

    def get_or_create(self, prospect: Prospect) -> dict:
        """Récupère ou crée une conversation pour un prospect."""
        existing = self.get(prospect.email)
        if existing:
            return existing
        return self.create(prospect)


# Instance globale — remplace le dict `conversations` et le set `devis_envoyes`
store = ConversationStore()