import re
from sqlalchemy.orm import Session
from app.models.prospect import Prospect
from app.core.database import SessionLocal


# ============================================================
#  CONFIGURATION — adapte à ta zone de travail
# ============================================================

# Villes que tu cibles en priorité (zone de travail)
TARGET_ZONES = [
    "saint-maur", "joinville", "champigny", "chennevières",
    "créteil", "vincennes", "nogent", "maisons-alfort",
    "fontenay", "boissy", "sucy", "bonneuil", "villiers",
    "paris", "ivry", "charenton", "alfortville", "vitry",
]

# Formes juridiques professionnelles
LEGAL_FORMS = [
    "sarl", "sas", "sasu", "eurl", "sa ", "sci ",
    "ets ", "cie ", "sté ", "société", "groupe", "entreprise"
]

# Préfixes d'emails considérés comme professionnels
PRO_EMAIL_PREFIXES = [
    "contact", "info", "accueil", "bonjour", "hello",
    "devis", "commercial", "direction", "admin", "secretariat"
]

# Domaines d'emails personnels
PERSONAL_EMAIL_DOMAINS = [
    "gmail.com", "hotmail.com", "hotmail.fr", "yahoo.com",
    "yahoo.fr", "orange.fr", "free.fr", "laposte.net",
    "outlook.com", "outlook.fr", "live.fr", "sfr.fr",
    "wanadoo.fr", "bbox.fr"
]

# Domaines réseaux sociaux (présence digitale nulle)
SOCIAL_DOMAINS = [
    "facebook.com", "instagram.com", "twitter.com", "linkedin.com",
    "youtube.com", "tiktok.com"
]

# Industries cibles pour scoring signaux
TARGET_INDUSTRIES = {
    "high": ["btp", "construction", "immo", "immobilier", "promoteur", "promotion"],
    "medium": ["syndic", "hotel", "restaurant", "restauration", "hôtel"],
    "low": ["bureau", "commerce", "architecte", "cabinet"],
}


# ============================================================
#  EXTRACTEURS DE DONNÉES — Parse score_explanation
# ============================================================

def _extract_pappers_data(explanation: str) -> dict:
    """
    Extrait les données Pappers du champ score_explanation.
    Retourne un dict avec : ca, dirigeant, siret, effectifs, actif
    """
    if not explanation:
        return {}

    data = {}

    # CA : regex "CA : XXX €" ou "CA: XXX €"
    ca_match = re.search(r'CA\s*:\s*([\d\s\.]+)\s*€', explanation, re.IGNORECASE)
    if ca_match:
        ca_str = ca_match.group(1).replace(" ", "").replace(".", "")
        try:
            data["ca"] = int(ca_str)
        except:
            data["ca"] = None

    # Dirigeant : "Dirigeant : Nom Prénom"
    dirigeant_match = re.search(r'Dirigeant\s*:\s*([^\n]+)', explanation, re.IGNORECASE)
    if dirigeant_match:
        data["dirigeant"] = dirigeant_match.group(1).strip()

    # SIRET : 14 chiffres
    siret_match = re.search(r'SIRET\s*:\s*(\d{14})', explanation)
    if siret_match:
        data["siret"] = siret_match.group(1)

    # Effectifs : "Effectifs : N"
    effectifs_match = re.search(r'Effectifs\s*:\s*(\d+)', explanation)
    if effectifs_match:
        try:
            data["effectifs"] = int(effectifs_match.group(1))
        except:
            data["effectifs"] = None

    # Statut actif : cherche "actif" (cas-insensible)
    data["is_active"] = bool(re.search(r'\bactif\b', explanation, re.IGNORECASE))

    # Source Pappers : bloc "Pappers" anywhere
    data["has_pappers"] = "Pappers" in explanation

    return data


def _extract_permis_data(explanation: str) -> bool:
    """
    Détecte si "Source : Permis de construire accordé" est présent.
    Retourne True si présent.
    """
    if not explanation:
        return False
    return "Source : Permis de construire" in explanation or "Permis de construire accordé" in explanation


def _extract_dvf_data(explanation: str) -> bool:
    """
    Détecte si source DVF est mentionnée.
    Retourne True si présent.
    """
    if not explanation:
        return False
    return "Source : DVF" in explanation or "source_dvf" in explanation.lower()


# ============================================================
#  FONCTIONS DE SCORING — 300 PTS TOTAL
# ============================================================

def _score_joignabilite(prospect) -> tuple[int, list]:
    """
    Joignabilité — 80 pts max
    Email professionnel : +40
    Email entreprise    : +30
    Email personnel     : +15
    Téléphone fixe      : +25
    Téléphone mobile    : +15
    """
    score = 0
    details = []

    # ── Email ──────────────────────────────────────────────
    if prospect.email:
        local = prospect.email.lower().split("@")[0]
        domain = prospect.email.lower().split("@")[-1] if "@" in prospect.email else ""

        if any(local.startswith(p) for p in PRO_EMAIL_PREFIXES):
            score += 40
            details.append(f"✉ Email professionnel (contact@...) +40")
        elif domain in PERSONAL_EMAIL_DOMAINS:
            score += 15
            details.append(f"✉ Email personnel (gmail, etc.) +15")
        else:
            # Email d'entreprise non générique
            score += 30
            details.append(f"✉ Email entreprise (nom@domaine.com) +30")
    else:
        details.append("✉ Pas d'email trouvé +0")

    # ── Téléphone ──────────────────────────────────────────
    if prospect.phone:
        digits = prospect.phone.replace(" ", "").replace(".", "").replace("-", "")
        if digits.startswith(("01", "02", "03", "04", "05", "09")):
            score += 25
            details.append(f"📞 Téléphone fixe +25")
        elif digits.startswith(("06", "07")):
            score += 15
            details.append(f"📱 Téléphone mobile +15")
        else:
            score += 10
            details.append(f"📞 Téléphone détecté +10")
    else:
        details.append("📞 Pas de téléphone +0")

    return score, details


def _score_identite(prospect) -> tuple[int, list]:
    """
    Présence & Identité — 60 pts max
    Site web présent    : +20
    Email sur site      : +10
    Bloc Pappers        : +10
    Dirigeant identifié : +10
    SIRET connu         : +5
    Forme juridique     : +5
    """
    score = 0
    details = []

    pappers_data = _extract_pappers_data(prospect.score_explanation or "")

    # ── Site web ────────────────────────────────────────────
    if prospect.website:
        website_lower = prospect.website.lower()
        if any(social in website_lower for social in SOCIAL_DOMAINS):
            details.append("🌐 Seul réseau social +0")
        else:
            score += 20
            details.append("🌐 Site web présent +20")

            if prospect.email:
                score += 10
                details.append("📄 Email trouvé sur le site +10")
    else:
        details.append("🌐 Pas de site web +0")

    # ── Pappers : bloc présent ───────────────────────────────
    if pappers_data.get("has_pappers"):
        score += 10
        details.append("🔹 Données Pappers trouvées +10")

    # ── Dirigeant identifié ──────────────────────────────────
    if pappers_data.get("dirigeant"):
        score += 10
        details.append(f"👤 Dirigeant : {pappers_data['dirigeant'][:30]} +10")

    # ── SIRET connu ──────────────────────────────────────────
    if pappers_data.get("siret"):
        score += 5
        details.append("🔢 SIRET connu +5")

    # ── Forme juridique professionnelle ──────────────────────
    name_lower = (prospect.company_name or "").lower()
    if any(form in name_lower for form in LEGAL_FORMS):
        score += 5
        details.append("🏢 Forme juridique pro +5")
    else:
        details.append("🏢 Pas de forme juridique +0")

    return score, details


def _score_potentiel(prospect) -> tuple[int, list]:
    """
    Potentiel commercial — 80 pts max
    Zone prioritaire    : +20
    Adresse complète    : +15
    CA > 1M€            : +30
    CA > 500k€          : +20
    CA > 100k€          : +10
    Effectifs ≥ 10      : +15
    Effectifs 5-9       : +8
    Entreprise active   : +5
    """
    score = 0
    details = []

    pappers_data = _extract_pappers_data(prospect.score_explanation or "")

    # ── Zone prioritaire ─────────────────────────────────────
    location_text = " ".join(filter(None, [
        prospect.city or "",
        prospect.address or ""
    ])).lower()

    if any(zone in location_text for zone in TARGET_ZONES):
        score += 20
        details.append("🎯 Zone prioritaire (IDF) +20")
    else:
        details.append("🎯 Hors zone prioritaire +0")

    # ── Adresse complète ────────────────────────────────────
    if prospect.address:
        has_zip = bool(re.search(r'\b\d{5}\b', prospect.address))
        if has_zip and len(prospect.address) > 15:
            score += 15
            details.append("📍 Adresse complète (code postal) +15")
        else:
            score += 7
            details.append("📍 Adresse partielle +7")
    else:
        details.append("📍 Pas d'adresse +0")

    # ── Chiffre d'affaires ──────────────────────────────────
    ca = pappers_data.get("ca")
    if ca:
        if ca > 1_000_000:
            score += 30
            details.append(f"💰 CA > 1M€ ({ca:,}€) +30")
        elif ca > 500_000:
            score += 20
            details.append(f"💰 CA > 500k€ ({ca:,}€) +20")
        elif ca > 100_000:
            score += 10
            details.append(f"💰 CA > 100k€ ({ca:,}€) +10")
    else:
        details.append("💰 Pas de CA trouvé +0")

    # ── Effectifs ───────────────────────────────────────────
    effectifs = pappers_data.get("effectifs")
    if effectifs:
        if effectifs >= 10:
            score += 15
            details.append(f"👥 Effectifs ≥ 10 ({effectifs} salariés) +15")
        elif effectifs >= 5:
            score += 8
            details.append(f"👥 Effectifs 5-9 ({effectifs} salariés) +8")
    else:
        details.append("👥 Pas d'effectifs trouvés +0")

    # ── Entreprise active ───────────────────────────────────
    if pappers_data.get("is_active"):
        score += 5
        details.append("✅ Entreprise active +5")

    return score, details


def _score_signaux(prospect) -> tuple[int, list]:
    """
    Signaux d'opportunité — 80 pts max
    Permis de construire : +40
    Industrie BTP        : +20
    Industrie syndic/hôtel : +15
    Industrie bureau/commerce : +10
    Email répondu (status) : +30
    Source DVF           : +20
    """
    score = 0
    details = []

    # ── Permis de construire ─────────────────────────────────
    if _extract_permis_data(prospect.score_explanation or ""):
        score += 40
        details.append("🏗️ Permis de construire accordé +40")
    else:
        details.append("🏗️ Pas de permis de construire +0")

    # ── Industries cibles ────────────────────────────────────
    industry_lower = (prospect.industry or "").lower()

    if any(ind in industry_lower for ind in TARGET_INDUSTRIES["high"]):
        score += 20
        details.append("🎯 Industrie BTP/Construction/Immo +20")
    elif any(ind in industry_lower for ind in TARGET_INDUSTRIES["medium"]):
        score += 15
        details.append("🎯 Industrie Syndic/Hôtel/Restaurant +15")
    elif any(ind in industry_lower for ind in TARGET_INDUSTRIES["low"]):
        score += 10
        details.append("🎯 Industrie Bureau/Commerce/Architecte +10")
    else:
        details.append("🎯 Industrie non ciblée +0")

    # ── Email répondu ───────────────────────────────────────
    if prospect.status == "replied":
        score += 30
        details.append("📧 Email répondu +30")

    # ── Source DVF ───────────────────────────────────────────
    if _extract_dvf_data(prospect.score_explanation or ""):
        score += 20
        details.append("🏠 Source DVF (transaction récente) +20")

    return score, details


def _get_label(score: int) -> str:
    """
    Retourne un label lisible selon le score /100.
    Seuils :
    - ≥ 80 : Priorité haute
    - ≥ 60 : Priorité moyenne
    - ≥ 40 : Priorité faible
    - < 40 : Non prioritaire
    """
    if score >= 80:
        return "🔥 Priorité haute"
    elif score >= 60:
        return "⚡ Priorité moyenne"
    elif score >= 40:
        return "🌱 Priorité faible"
    else:
        return "❄️ Non prioritaire"


def calculate_score(prospect) -> tuple[int, str, str]:
    """
    Calcule le score complet sur 300 pts, puis normalise à /100.
    Retourne (score_normalized, label, explication détaillée)
    """
    score_j, details_j = _score_joignabilite(prospect)      # 80 max
    score_i, details_i = _score_identite(prospect)           # 60 max
    score_p, details_p = _score_potentiel(prospect)          # 80 max
    score_s, details_s = _score_signaux(prospect)            # 80 max

    total_brut = score_j + score_i + score_p + score_s       # 300 max
    score_normalized = round(total_brut / 300 * 100)         # Normaliser à /100
    label = _get_label(score_normalized)

    # Explication lisible avec catégories
    explanation = (
        f"[300pts] Joignabilité {score_j}/80 | "
        f"Identité {score_i}/60 | "
        f"Potentiel {score_p}/80 | "
        f"Signaux {score_s}/80\n"
        f"Score brut: {total_brut}/300 → {score_normalized}/100\n\n"
        + "JOIGNABILITÉ:\n" + "\n".join(details_j) + "\n\n"
        + "IDENTITÉ:\n" + "\n".join(details_i) + "\n\n"
        + "POTENTIEL:\n" + "\n".join(details_p) + "\n\n"
        + "SIGNAUX:\n" + "\n".join(details_s)
    )

    return score_normalized, label, explanation


# ============================================================
#  RUNNER
# ============================================================

def run_lead_scoring():
    """
    Parcourt TOUS les prospects et calcule le score enrichi.
    Met à jour lead_score (normalisé /100), score_label, score_explanation.
    """
    db: Session = SessionLocal()

    prospects = db.query(Prospect).all()
    total = len(prospects)

    score_distribution = {
        "🔥 Priorité haute": 0,
        "⚡ Priorité moyenne": 0,
        "🌱 Priorité faible": 0,
        "❄️ Non prioritaire": 0
    }

    for prospect in prospects:
        score, label, explanation = calculate_score(prospect)

        prospect.lead_score = score
        prospect.score_label = label
        prospect.score_explanation = explanation
        prospect.status = "scored"

        score_distribution[label] += 1

    db.commit()
    db.close()

    print(f"\n{'='*50}")
    print(f"📊 SCORING ENRICHI 300pts → /100 — {total} prospects")
    print(f"{'='*50}")
    for label, count in score_distribution.items():
        pct = round(count / total * 100) if total > 0 else 0
        print(f"  {label} : {count} ({pct}%)")
    print(f"{'='*50}\n")