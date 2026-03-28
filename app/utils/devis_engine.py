"""
Moteur de devis intelligent — lit devis_rules.json et calcule les montants.
Remplace les tarifs codés en dur dans qualification_agent.py
"""
import json
import os
from datetime import datetime, date, timedelta

RULES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "devis_rules.json"
)

def load_rules() -> dict:
    """Charge les règles tarifaires depuis devis_rules.json."""
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_tarif_key(type_prestation: str, frequence: str) -> str:
    """Détermine la clé tarifaire selon le type et la fréquence."""
    if type_prestation == "fin_chantier":
        return "fin_chantier"
    elif type_prestation == "vitrerie":
        return "vitrerie"
    elif type_prestation == "remise_en_etat":
        return "remise_en_etat"
    elif type_prestation == "copropriete":
        if frequence == "hebdo":
            return "copropriete_hebdo"
        return "copropriete_mensuel"
    else:  # bureaux (default)
        mapping = {
            "hebdo":       "bureaux_hebdo",
            "mensuel":     "bureaux_mensuel",
            "trimestriel": "bureaux_trimestriel",
            "annuel":      "bureaux_annuel",
            "ponctuel":    "bureaux_ponctuel",
        }
        return mapping.get(frequence, "bureaux_ponctuel")


def calculate(type_prestation: str, superficie_m2: float, frequence: str,
              nb_heures: float = None) -> dict:
    """
    Calcule le montant HT d'un devis.
    Retourne un dict complet avec tous les détails.
    """
    rules = load_rules()
    tarifs = rules["tarifs"]
    tva = rules["tva"]["taux_standard"]

    cle = get_tarif_key(type_prestation, frequence)
    tarif = tarifs.get(cle, tarifs["bureaux_ponctuel"])

    # Calcul montant HT
    if tarif["tarif_m2"] and superficie_m2:
        montant_ht = max(tarif["minimum_ht"], superficie_m2 * tarif["tarif_m2"])
    elif tarif["tarif_horaire"] and nb_heures:
        montant_ht = max(tarif["minimum_ht"], nb_heures * tarif["tarif_horaire"])
    else:
        montant_ht = tarif["minimum_ht"]

    montant_ht = round(montant_ht, 2)
    montant_ttc = round(montant_ht * (1 + tva / 100), 2)

    # Durée estimée
    duree_h = None
    if tarif.get("duree_estimee_h_par_100m2") and superficie_m2:
        duree_h = round((superficie_m2 / 100) * tarif["duree_estimee_h_par_100m2"], 1)

    # Date d'échéance devis
    validite = rules.get("validite_devis_jours", 30)
    date_echeance = (datetime.now() + timedelta(days=validite)).strftime("%d/%m/%Y")

    return {
        "cle_tarif": cle,
        "label": tarif["label"],
        "description": tarif["description"],
        "type_prestation": type_prestation,
        "superficie_m2": superficie_m2,
        "frequence": frequence,
        "tarif_m2": tarif.get("tarif_m2"),
        "tarif_horaire": tarif.get("tarif_horaire"),
        "montant_ht": montant_ht,
        "tva_pct": tva,
        "montant_ttc": montant_ttc,
        "duree_estimee_heures": duree_h,
        "validite_jours": validite,
        "date_echeance_devis": date_echeance,
        "societe": rules.get("societe", {}),
    }


def get_questions_manquantes(type_prestation: str, infos_connues: dict) -> list:
    """
    Retourne les questions à poser selon le type de prestation
    et les infos déjà collectées.
    """
    rules = load_rules()
    questions_config = rules.get("questions_qualification", {})

    cle = type_prestation or "bureaux"
    questions_requises = questions_config.get(cle, ["superficie_m2", "frequence"])

    labels = {
        "superficie_m2":   "superficie approximative en m²",
        "frequence":       "fréquence souhaitée (unique, hebdomadaire, mensuelle, trimestrielle, annuelle)",
        "type_batiment":   "type de bâtiment (maison, appartement, bureaux, entrepôt...)",
        "nb_personnes":    "nombre de personnes travaillant dans les locaux",
        "nb_lots":         "nombre de lots dans la copropriété",
        "nb_faces":        "nombre de faces de vitres (simple, double...)",
        "hauteur":         "hauteur des vitrages (accessible sans échafaudage ?)",
        "date_souhaitee":  "date souhaitée pour l'intervention",
        "type_sinistre":   "type de sinistre (dégât des eaux, incendie, travaux...)",
    }

    manquantes = []
    for q in questions_requises:
        if not infos_connues.get(q):
            manquantes.append(labels.get(q, q))

    return manquantes


def get_all_tarifs() -> list:
    """Retourne tous les tarifs pour l'affichage dans le dashboard."""
    rules = load_rules()
    result = []
    for cle, tarif in rules["tarifs"].items():
        result.append({
            "cle": cle,
            "label": tarif["label"],
            "description": tarif["description"],
            "tarif_m2": tarif.get("tarif_m2"),
            "tarif_horaire": tarif.get("tarif_horaire"),
            "minimum_ht": tarif["minimum_ht"],
        })
    return result