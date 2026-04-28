"""
Agent DVF — Scrape les transactions immobilières via data.gouv
Source : https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres
Mise à jour mensuelle par la DGFIP.

Stratégie :
- Télécharge les CSV.gz DVF par département depuis files.data.gouv.fr
- Décompresse et parse les CSVs (pattern identique à SITADEL permis_construire)
- Filtre sur les départements IDF cibles
- Filtre sur les types de bien pertinents (locaux, bureaux, commerces, appartements immeuble)
- Filtre sur les transactions récentes (< 12 mois)
- Crée des prospects avec score 55-70 selon le type et le montant
"""

import io
import csv
import gzip
import requests
import logging
from datetime import datetime, date, timedelta
from app.core.database import SessionLocal
from app.models.prospect import Prospect
from app.agents.activity_logger import log_system, log_error
from app.agents.telegram_notifier import send_message as tg

logger = logging.getLogger("proprexis.dvf")

# URL base des CSV DVF par département (data.gouv.fr / DGFIP)
# Essaie l'année courante, fallback à l'année précédente si nécessaire
def get_dvf_csv_base() -> str:
    """Retourne l'URL de base DVF avec l'année la plus récente disponible"""
    current_year = date.today().year
    # Les données DVF publiées en cours d'année sont souvent de l'année précédente
    # Essayer année précédente d'abord (plus probable d'avoir des données complètes)
    for year in [current_year - 1, current_year, current_year - 2]:
        url_test = f"https://files.data.gouv.fr/geo-dvf/latest/csv/{year}/departements/75.csv.gz"
        try:
            res = requests.head(url_test, timeout=5)
            if res.status_code == 200:
                return f"https://files.data.gouv.fr/geo-dvf/latest/csv/{year}/departements/{{dept}}.csv.gz"
        except Exception:
            pass
    # Fallback à l'année précédente si rien ne fonctionne
    return f"https://files.data.gouv.fr/geo-dvf/latest/csv/{current_year - 1}/departements/{{dept}}.csv.gz"

DVF_CSV_BASE = None  # Sera initialisé au premier appel

# Départements IDF cibles
DEPTS_CIBLES = {"75", "77", "78", "91", "92", "93", "94", "95"}

# Types de bien pertinents pour nettoyage
# DVF utilise des textes, pas des codes numériques
TYPES_BIEN_PERTINENTS = {
    "Appartement": "appartement",  # Appartements → copropriété
    "Local industriel. commercial ou assimilé": "commerce_bureau",  # Commerce/Bureaux
}

# Textes courts pour chaque type
TYPE_LABELS = {
    "Appartement": "Appartement/Immeuble (copropriété)",
    "Local industriel. commercial ou assimilé": "Commerce/Bureaux/Locaux d'activité",
}


def download_dvf_csv(dept: str) -> list[dict]:
    """Télécharge et parse le CSV DVF.gz pour un département"""
    try:
        global DVF_CSV_BASE
        if DVF_CSV_BASE is None:
            DVF_CSV_BASE = get_dvf_csv_base()
            logger.info(f"DVF CSV base URL: {DVF_CSV_BASE}")

        url = DVF_CSV_BASE.format(dept=dept)
        logger.info(f"Téléchargement DVF CSV.gz dept {dept} : {url}")
        res = requests.get(url, timeout=120, headers={"User-Agent": "Proprexis/1.0"})

        if res.status_code != 200:
            logger.error(f"Erreur HTTP {res.status_code} pour dept {dept}")
            return []

        # Décompresser le gzip
        try:
            decompressed = gzip.decompress(res.content)
        except Exception as e:
            logger.error(f"Erreur décompression gzip dept {dept} : {e}")
            return []

        # Parser le CSV
        try:
            text = decompressed.decode("utf-8")
        except Exception:
            text = decompressed.decode("latin-1")

        reader = csv.DictReader(io.StringIO(text), delimiter=",")
        rows = list(reader)

        if rows:
            logger.info(f"CSV DVF dept {dept} : {len(rows)} lignes chargées")
        return rows

    except Exception as e:
        logger.error(f"Erreur téléchargement DVF CSV dept {dept} : {e}")
        return []


def parse_dvf_transaction(row: dict) -> dict | None:
    """
    Parse une ligne du CSV DVF.
    Colonnes clés : code_departement, type_local, valeur_fonciere, date_mutation,
                    adresse_numero, adresse_suffixe, adresse_nom_voie,
                    nom_commune, nombre_pieces_principales, surface_reelle_bati
    """
    try:
        # Code département
        dept = str(row.get("code_departement", "") or "").strip().zfill(2)
        if dept not in DEPTS_CIBLES:
            return None

        # Type de bien — chercher d'abord code_type_local, puis type_local
        type_local = str(row.get("type_local", "") or row.get("code_type_local", "") or "").strip()
        if type_local not in TYPES_BIEN_PERTINENTS:
            return None

        # Valeur foncière (montant de la transaction)
        valeur_str = str(row.get("valeur_fonciere", "") or "").strip()
        if not valeur_str or valeur_str == "":
            return None
        try:
            valeur = float(valeur_str)
            if valeur < 10000:  # Transactions trop faibles
                return None
        except Exception:
            return None

        # Date de mutation (format YYYY-MM-DD dans le CSV)
        date_mut_str = str(row.get("date_mutation", "") or "").strip()
        if not date_mut_str:
            return None

        # Filtrer transactions > 12 mois — nouveau propriétaire = signal opportunité nettoyage
        try:
            if "-" in date_mut_str:
                year, month, day = date_mut_str.split("-")
            elif "/" in date_mut_str:
                year, month, day = date_mut_str.split("/")
            else:
                year = date_mut_str[:4]
                month = date_mut_str[4:6] if len(date_mut_str) >= 6 else "01"
                day = date_mut_str[6:8] if len(date_mut_str) >= 8 else "01"

            date_transaction = date(int(year), int(month), int(day))
            if (date.today() - date_transaction).days > 365:
                return None
        except Exception:
            return None

        # Commune — utiliser nom_commune (pas adresse_commune)
        commune = str(row.get("nom_commune", "") or "").strip().title()
        if not commune:
            return None

        # Adresse : numéro + suffixe + nom_voie
        num = str(row.get("adresse_numero", "") or "").strip()
        suffixe = str(row.get("adresse_suffixe", "") or "").strip()
        nom_voie = str(row.get("adresse_nom_voie", "") or "").strip()
        address_parts = [num, suffixe, nom_voie]
        address_parts = [p for p in address_parts if p]
        address = " ".join(address_parts) if address_parts else "Adresse partielle"

        # Surface
        surface_str = str(row.get("surface_reelle_bati", "") or "").strip()
        surface = 0
        if surface_str and surface_str != "0":
            try:
                surface = float(surface_str)
            except Exception:
                pass

        # Nombre de pièces
        nb_pieces_str = str(row.get("nombre_pieces_principales", "") or "").strip()
        nb_pieces = 0
        if nb_pieces_str and nb_pieces_str != "0":
            try:
                nb_pieces = int(float(nb_pieces_str))
            except Exception:
                pass

        return {
            "address": address,
            "commune": commune,
            "dept": dept,
            "type_local": type_local,
            "type_label": TYPE_LABELS.get(type_local, "Bien immobilier"),
            "valeur": valeur,
            "date_mutation": date_mut_str,
            "surface_m2": surface,
            "nb_pieces": nb_pieces,
            "source": "dvf",
        }

    except Exception as e:
        logger.debug(f"Erreur parse DVF : {e}")
        return None


def calculate_score(transaction: dict) -> int:
    """Score spécifique aux transactions DVF."""
    score = 55  # Base modérée — transaction récente c'est bon, mais pas de contact encore

    # Valeur de transaction
    valeur = transaction.get("valeur", 0)
    if valeur > 500000:
        score += 15
    elif valeur > 300000:
        score += 10
    elif valeur > 150000:
        score += 5

    # Type de bien
    type_local = transaction.get("type_local", "")
    if type_local == "4":  # Commerce/Bureaux → signal fort pour nettoyage
        score += 10
    elif type_local == "2":  # Appartement immeuble
        score += 5

    # Surface
    surface = transaction.get("surface_m2", 0)
    if surface > 500:
        score += 5
    elif surface > 200:
        score += 2

    # Département prioritaire
    if transaction.get("dept") in ("94", "93", "92"):
        score += 3

    return min(100, score)


def run_dvf_scraper() -> dict:
    """
    Lance le scraping des transactions DVF.
    Requête l'API par département, filtre IDF, crée les prospects.
    """
    db = SessionLocal()
    total_created = 0
    total_skipped = 0

    try:
        all_transactions = []

        # Télécharge chaque département IDF
        for dept in sorted(DEPTS_CIBLES):
            rows = download_dvf_csv(dept)
            if not rows:
                logger.warning(f"Aucun DVF pour dept {dept}")
                continue

            logger.info(f"Dept {dept} : {len(rows)} lignes retournées")

            # Parser les transactions
            for row in rows:
                parsed = parse_dvf_transaction(row)
                if parsed:
                    all_transactions.append(parsed)

        logger.info(f"Total transactions IDF pertinentes : {len(all_transactions)}")

        # Dédupliquer par adresse + commune
        seen = set()
        unique_transactions = []
        for t in all_transactions:
            key = f"{t['address'].lower()}_{t['commune'].lower()}"
            if key not in seen:
                seen.add(key)
                unique_transactions.append(t)

        logger.info(f"Après déduplication : {len(unique_transactions)} transactions")

        # Créer les prospects
        for transaction in unique_transactions:
            # Vérifier si déjà en base
            existing = db.query(Prospect).filter(
                Prospect.address == transaction["address"],
                Prospect.city == transaction["commune"],
            ).first()

            if existing:
                total_skipped += 1
                continue

            score = calculate_score(transaction)
            explanation = (
                f"Source : Transaction DVF (nouveau propriétaire)\n"
                f"Type : {transaction['type_label']}\n"
                f"Valeur : {transaction['valeur']:,.0f}€\n"
                f"Surface : {transaction['surface_m2']:.0f} m²\n"
                f"Pièces : {transaction['nb_pieces']}\n"
                f"Date : {transaction['date_mutation']}\n"
                f"Score {score}/100 — Signal : nouveau propriétaire = besoin nettoyage/remise en état"
            )

            prospect = Prospect(
                company_name=f"Propriétaire {transaction['commune']}",
                address=transaction["address"],
                city=transaction["commune"],
                industry="immobilier",
                lead_score=score,
                score_label="Priorité haute" if score >= 70 else "Priorité moyenne",
                score_explanation=explanation,
                status="scored",
            )
            db.add(prospect)
            total_created += 1

        db.commit()

        msg = f"🏠 DVF : {total_created} nouveaux prospects créés ({total_skipped} déjà en base)"
        logger.info(msg)
        log_system(msg, status="success", details={"created": total_created, "skipped": total_skipped})

        if total_created > 0:
            tg(
                f"🏠 *Transactions immobilières DVF*\n\n"
                f"{total_created} nouveaux propriétaires détectés en IDF\n"
                f"Potentiel nettoyage/remise en état\n\n"
                f"→ [Voir les prospects](http://localhost:3000/prospects)"
            )

        return {"status": "success", "created": total_created, "skipped": total_skipped}

    except Exception as e:
        logger.error(f"Erreur DVF scraper : {e}")
        log_error("dvf", str(e))
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
