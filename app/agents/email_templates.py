"""
Templates emails de prospection par secteur.
Personnalisés avec le nom de l'entreprise et la ville.
"""

TEMPLATES = {
    "btp": {
        "objet": "Nettoyage fin de chantier — Proprexis",
        "corps": """Bonjour,

Votre entreprise réalise des chantiers en Île-de-France — nous intervenons en fin de chantier pour la remise en état complète avant livraison.

Notre prestation comprend :
• Évacuation des gravats et déchets de chantier
• Dégraissage et nettoyage des sols
• Nettoyage des vitrages et surfaces
• Remise en état avant réception par le maître d'ouvrage

Nous intervenons sous 48h sur {ville} et ses alentours, avec une équipe dédiée et du matériel professionnel.

Souhaitez-vous recevoir un devis pour votre prochain chantier ?

Cordialement,
Mohand Sari — Proprexis
contact.proprexis@gmail.com | 06 XX XX XX XX""",
    },
    "immobilier": {
        "objet": "Entretien et nettoyage de vos biens — Proprexis",
        "corps": """Bonjour,

En tant qu'agence immobilière active sur {ville}, vous gérez régulièrement des remises en état entre deux locataires ou avant mise en vente.

Proprexis prend en charge :
• Nettoyage complet entre deux occupants
• Remise en état avant visite acquéreur
• Nettoyage de fin de bail
• Intervention express sous 24h si besoin

Nous travaillons déjà avec plusieurs agences du secteur et proposons des tarifs adaptés aux volumes.

Êtes-vous disponible pour qu'on échange sur vos besoins ?

Cordialement,
Mohand Sari — Proprexis
contact.proprexis@gmail.com | 06 XX XX XX XX""",
    },
    "syndic": {
        "objet": "Entretien parties communes — Proprexis",
        "corps": """Bonjour,

Nous proposons aux syndics de copropriété un service d'entretien régulier des parties communes : halls, escaliers, couloirs, locaux poubelles et parkings.

Ce que nous offrons :
• Contrats hebdomadaires, bi-hebdomadaires ou mensuels
• Équipe fixe dédiée à votre résidence
• Rapport d'intervention après chaque passage
• Tarifs dégressifs selon le nombre de lots

Nous intervenons sur {ville} et les communes voisines.

Souhaitez-vous un devis pour vos résidences ?

Cordialement,
Mohand Sari — Proprexis
contact.proprexis@gmail.com | 06 XX XX XX XX""",
    },
    "architecte": {
        "objet": "Nettoyage fin de chantier pour vos projets — Proprexis",
        "corps": """Bonjour,

En tant qu'architecte, vous savez combien la propreté du chantier lors de la livraison est déterminante pour la satisfaction du client final.

Proprexis intervient en coordination avec vos équipes pour :
• Nettoyage complet avant réception
• Remise en état des surfaces nobles
• Intervention dans les délais imposés par votre planning
• Devis express sous 4h

Nous intervenons sur {ville} et toute l'Île-de-France.

Pouvons-nous vous préparer une offre pour votre prochain projet ?

Cordialement,
Mohand Sari — Proprexis
contact.proprexis@gmail.com | 06 XX XX XX XX""",
    },
    "bureaux": {
        "objet": "Nettoyage de vos locaux professionnels — Proprexis",
        "corps": """Bonjour,

Proprexis assure l'entretien régulier de locaux professionnels à {ville} : bureaux, open spaces, salles de réunion, sanitaires et espaces communs.

Nos engagements :
• Intervention tôt le matin ou en soirée selon vos contraintes
• Équipe stable et formée
• Produits professionnels fournis
• Suivi qualité après chaque passage

Nous proposons des contrats hebdomadaires et mensuels avec tarifs adaptés à votre surface.

Souhaitez-vous un devis gratuit ?

Cordialement,
Mohand Sari — Proprexis
contact.proprexis@gmail.com | 06 XX XX XX XX""",
    },
    "default": {
        "objet": "Nettoyage professionnel pour votre entreprise — Proprexis",
        "corps": """Bonjour,

Proprexis est une entreprise de nettoyage professionnel basée en Île-de-France, spécialisée dans l'entretien de locaux d'entreprise et le nettoyage fin de chantier.

Nous intervenons sur {ville} et ses alentours pour :
• Nettoyage et entretien régulier de locaux
• Remise en état fin de chantier
• Nettoyage entre deux locataires
• Interventions ponctuelles

Souhaitez-vous recevoir un devis adapté à vos besoins ?

Cordialement,
Mohand Sari — Proprexis
contact.proprexis@gmail.com | 06 XX XX XX XX""",
    },
}

# Relances (angle différent)
RELANCES = {
    "btp": {
        "objet": "Re: Nettoyage fin de chantier — Proprexis",
        "corps": """Bonjour,

Je me permets de revenir vers vous suite à mon précédent message.

Nous venons de terminer une intervention fin de chantier à {ville} — 600m² remis en état en une journée.

Si vous avez un chantier en cours ou à venir, je peux vous établir un devis en moins d'une heure.

Cordialement,
Mohand Sari — Proprexis
contact.proprexis@gmail.com | 06 XX XX XX XX""",
    },
    "default": {
        "objet": "Relance — Proprexis nettoyage professionnel",
        "corps": """Bonjour,

Je reviens vers vous concernant nos services de nettoyage professionnel à {ville}.

Si le moment n'est pas opportun, pas de souci — je reste disponible dès que vous en aurez besoin.

N'hésitez pas à me contacter directement.

Cordialement,
Mohand Sari — Proprexis
contact.proprexis@gmail.com | 06 XX XX XX XX""",
    },
}


def get_template(industry: str, relance: bool = False) -> dict:
    """Retourne le template adapté au secteur."""
    industry_lower = (industry or "").lower()

    if relance:
        templates = RELANCES
    else:
        templates = TEMPLATES

    if any(x in industry_lower for x in ["construct", "btp", "bâtiment", "batiment", "rénov", "renov", "travaux"]):
        return templates.get("btp", templates["default"])
    elif any(x in industry_lower for x in ["immobil", "agence", "transaction"]):
        return templates.get("immobilier", templates["default"])
    elif any(x in industry_lower for x in ["syndic", "copro", "gestionnaire"]):
        return templates.get("syndic", templates["default"])
    elif any(x in industry_lower for x in ["architect"]):
        return templates.get("architecte", templates["default"])
    elif any(x in industry_lower for x in ["bureau", "office", "commerce", "retail"]):
        return templates.get("bureaux", templates["default"])
    else:
        return templates["default"]


def render_template(template: dict, prospect) -> tuple:
    """Remplace les variables dans le template. Retourne (objet, corps)."""
    ville = prospect.city or "Île-de-France"
    nom = prospect.company_name or "Madame, Monsieur"
    corps = template["corps"].replace("{ville}", ville).replace("{nom}", nom)
    return template["objet"], corps