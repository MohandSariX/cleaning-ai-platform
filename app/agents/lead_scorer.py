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


# ============================================================
#  FONCTIONS DE SCORING
# ============================================================

def _score_joignabilite(prospect) -> tuple[int, list]:
    """
    Joignabilité — 40 pts max
    Email pro → 25 pts | Email perso → 10 pts
    Tél fixe  → 15 pts | Tél mobile  →  8 pts
    """
    score = 0
    details = []

    # ── Email ──────────────────────────────────────────────
    if prospect.email:
        local = prospect.email.lower().split("@")[0]
        domain = prospect.email.lower().split("@")[-1] if "@" in prospect.email else ""

        if any(local.startswith(p) for p in PRO_EMAIL_PREFIXES):
            score += 25
            details.append(f"✉ Email professionnel ({prospect.email}) +25")
        elif domain in PERSONAL_EMAIL_DOMAINS:
            score += 10
            details.append(f"✉ Email personnel ({prospect.email}) +10")
        else:
            # Email d'entreprise non générique (ex: nom@entreprise.fr)
            score += 20
            details.append(f"✉ Email entreprise ({prospect.email}) +20")
    else:
        details.append("✉ Pas d'email trouvé +0")

    # ── Téléphone ──────────────────────────────────────────
    if prospect.phone:
        digits = prospect.phone.replace(" ", "").replace(".", "").replace("-", "")
        if digits.startswith(("01", "02", "03", "04", "05", "09")):
            score += 15
            details.append(f"📞 Téléphone fixe ({prospect.phone}) +15")
        elif digits.startswith(("06", "07")):
            score += 8
            details.append(f"📱 Téléphone mobile ({prospect.phone}) +8")
        else:
            score += 5
            details.append(f"📞 Téléphone détecté +5")
    else:
        details.append("📞 Pas de téléphone +0")

    return score, details


def _score_presence_digitale(prospect) -> tuple[int, list]:
    """
    Présence digitale — 30 pts max
    Site web propre → 20 pts | Réseau social → 0 pts
    Email sur page contact → +10 pts bonus
    """
    score = 0
    details = []

    if prospect.website:
        website_lower = prospect.website.lower()

        if any(social in website_lower for social in SOCIAL_DOMAINS):
            score += 0
            details.append(f"🌐 Seul réseau social ({prospect.website}) +0")
        else:
            score += 20
            details.append(f"🌐 Site web présent ({prospect.website}) +20")

            # Bonus si email trouvé (= présence sur page contact)
            if prospect.email:
                score += 10
                details.append("📄 Email trouvé sur le site +10 bonus")
    else:
        details.append("🌐 Pas de site web +0")

    return score, details


def _score_potentiel_commercial(prospect) -> tuple[int, list]:
    """
    Potentiel commercial — 30 pts max
    Adresse complète → 10 pts
    Zone ciblée      → 15 pts
    Forme juridique  →  5 pts
    """
    score = 0
    details = []

    # ── Adresse complète ───────────────────────────────────
    if prospect.address:
        # Vérifier présence d'un code postal (5 chiffres)
        import re
        has_zip = bool(re.search(r'\b\d{5}\b', prospect.address))
        if has_zip and len(prospect.address) > 15:
            score += 10
            details.append(f"📍 Adresse complète +10")
        else:
            score += 5
            details.append(f"📍 Adresse partielle +5")
    else:
        details.append("📍 Pas d'adresse +0")

    # ── Zone géographique ciblée ───────────────────────────
    location_text = " ".join(filter(None, [
        prospect.city or "",
        prospect.address or ""
    ])).lower()

    if any(zone in location_text for zone in TARGET_ZONES):
        score += 15
        details.append(f"🎯 Dans ta zone de travail +15")
    else:
        details.append(f"🎯 Hors zone prioritaire +0")

    # ── Forme juridique professionnelle ───────────────────
    name_lower = (prospect.company_name or "").lower()
    if any(form in name_lower for form in LEGAL_FORMS):
        score += 5
        details.append(f"🏢 Forme juridique pro +5")
    else:
        details.append(f"🏢 Nom sans forme juridique +0")

    return score, details


def _get_label(score: int) -> str:
    """Retourne un label lisible selon le score."""
    if score >= 75:
        return "🔥 Priorité haute"
    elif score >= 50:
        return "⚡ Priorité moyenne"
    elif score >= 25:
        return "🌱 Priorité faible"
    else:
        return "❄️ Non prioritaire"


def calculate_score(prospect) -> tuple[int, str, str]:
    """
    Calcule le score complet d'un prospect.
    Retourne (score, label, explication détaillée)
    """
    score_j, details_j = _score_joignabilite(prospect)
    score_d, details_d = _score_presence_digitale(prospect)
    score_p, details_p = _score_potentiel_commercial(prospect)

    total = min(score_j + score_d + score_p, 100)  # plafonné à 100
    label = _get_label(total)

    # Explication lisible
    explanation = (
        f"Joignabilité {score_j}/40 | "
        f"Présence digitale {score_d}/30 | "
        f"Potentiel {score_p}/30\n"
        + "\n".join(details_j + details_d + details_p)
    )

    return total, label, explanation


# ============================================================
#  RUNNER
# ============================================================

def run_lead_scoring():

    db: Session = SessionLocal()

    prospects = db.query(Prospect).all()
    total = len(prospects)

    score_distribution = {"🔥 Priorité haute": 0, "⚡ Priorité moyenne": 0,
                          "🌱 Priorité faible": 0, "❄️ Non prioritaire": 0}

    for prospect in prospects:
        score, label, explanation = calculate_score(prospect)

        prospect.lead_score = score
        prospect.score_label = label
        prospect.score_explanation = explanation
        prospect.status = "scored"

        score_distribution[label] += 1

    db.commit()
    db.close()

    print(f"\n{'='*40}")
    print(f"📊 SCORING TERMINÉ — {total} prospects")
    print(f"{'='*40}")
    for label, count in score_distribution.items():
        pct = round(count / total * 100) if total > 0 else 0
        print(f"  {label} : {count} ({pct}%)")
    print(f"{'='*40}\n")