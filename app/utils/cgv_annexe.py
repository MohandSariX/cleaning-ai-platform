"""
Générateur CGV — annexe PDF aux devis.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (Paragraph, Spacer, Table, TableStyle,
                                 HRFlowable, BaseDocTemplate, Frame, PageTemplate)
from reportlab.lib.styles import ParagraphStyle
from io import BytesIO
from app.utils.devis_engine import load_rules

DARK   = colors.HexColor('#0f172a')
ACCENT = colors.HexColor('#3b82f6')
MUTED  = colors.HexColor('#64748b')
BORDER = colors.HexColor('#e2e8f0')
WHITE  = colors.white
W, H   = A4


def _cgv_header(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFillColor(DARK)
    canvas_obj.rect(0, H - 20*mm, W, 20*mm, fill=1, stroke=0)
    societe = load_rules().get("societe", {})
    canvas_obj.setFillColor(WHITE)
    canvas_obj.setFont('Helvetica-Bold', 12)
    canvas_obj.drawString(20*mm, H - 13*mm, f"CONDITIONS GÉNÉRALES DE VENTE — {societe.get('nom', 'PROPREXIS').upper()}")
    canvas_obj.setFillColor(MUTED)
    canvas_obj.setFont('Helvetica', 8)
    from datetime import date
    canvas_obj.drawRightString(W - 20*mm, 12*mm, f"Page {canvas_obj.getPageNumber()}")
    canvas_obj.setStrokeColor(BORDER)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(20*mm, 18*mm, W - 20*mm, 18*mm)
    canvas_obj.restoreState()


def generate_cgv_pdf() -> bytes:
    """Génère le PDF des CGV."""
    rules = load_rules()
    societe = rules.get("societe", {})
    validite = rules.get("validite_devis_jours", 30)

    buffer = BytesIO()
    doc = BaseDocTemplate(
        buffer, pagesize=A4,
        topMargin=28*mm, bottomMargin=25*mm,
        leftMargin=20*mm, rightMargin=20*mm,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='main')
    template = PageTemplate(id='main', frames=[frame], onPage=_cgv_header)
    doc.addPageTemplates([template])

    s_title   = ParagraphStyle('t', fontName='Helvetica-Bold', fontSize=10, textColor=ACCENT, spaceBefore=6*mm, spaceAfter=2*mm)
    s_body    = ParagraphStyle('b', fontName='Helvetica', fontSize=9, textColor=DARK, leading=14, spaceAfter=2*mm)
    s_bold    = ParagraphStyle('bo', fontName='Helvetica-Bold', fontSize=9, textColor=DARK)

    story = []

    articles = [
        ("Article 1 — Objet",
         f"{societe.get('nom', 'Proprexis')} ({societe.get('forme_juridique', 'Auto-entrepreneur')}, "
         f"SIRET {societe.get('siret', 'XXX')}) propose des prestations de nettoyage professionnel "
         f"de locaux, fins de chantier, parties communes et vitrerie en Île-de-France. "
         f"Les présentes CGV régissent l'ensemble des relations commerciales entre {societe.get('nom', 'Proprexis')} et ses clients."),

        ("Article 2 — Devis et commande",
         f"Tout devis est valable {validite} jours à compter de sa date d'émission. "
         f"La signature du devis avec la mention « Bon pour accord » vaut acceptation des présentes CGV. "
         f"Toute modification de la prestation devra faire l'objet d'un avenant signé."),

        ("Article 3 — Prix et TVA",
         f"Les prix sont indiqués en euros hors taxes (HT). La TVA applicable est celle en vigueur au jour de la facturation. "
         f"Pour les prestations de nettoyage de locaux d'habitation, la TVA réduite de 10% peut s'appliquer sous conditions. "
         f"Les tarifs sont révisables chaque année au 1er janvier."),

        ("Article 4 — Paiement",
         f"Le règlement s'effectue par virement bancaire à réception de facture. "
         f"IBAN : {societe.get('iban', 'FR76 XXXX')} — BIC : {societe.get('bic', 'XXXXXXXX')}. "
         f"En cas de retard de paiement, des pénalités de 3 fois le taux d'intérêt légal seront appliquées, "
         f"ainsi qu'une indemnité forfaitaire de recouvrement de 40€."),

        ("Article 5 — Exécution des prestations",
         f"Les prestations sont réalisées aux horaires convenus entre les parties. "
         f"Le client s'engage à assurer l'accès aux locaux et à fournir les accès nécessaires (codes, badges). "
         f"{societe.get('nom', 'Proprexis')} se réserve le droit de refuser une prestation si les conditions de sécurité ne sont pas réunies."),

        ("Article 6 — Responsabilité",
         f"{societe.get('nom', 'Proprexis')} est assuré en responsabilité civile professionnelle. "
         f"Toute réclamation doit être formulée par écrit dans les 48h suivant la prestation. "
         f"La responsabilité de {societe.get('nom', 'Proprexis')} est limitée au montant de la prestation concernée."),

        ("Article 7 — Annulation",
         f"Toute annulation doit être notifiée par email au moins 48h avant la prestation. "
         f"En cas d'annulation tardive (moins de 24h), une indemnité égale à 30% du montant HT sera facturée."),

        ("Article 8 — Confidentialité",
         f"Les informations collectées sont utilisées exclusivement pour la gestion commerciale. "
         f"Conformément au RGPD, vous disposez d'un droit d'accès, de rectification et de suppression "
         f"en contactant : {societe.get('email', 'contact@proprexis.fr')}."),

        ("Article 9 — Litiges",
         f"En cas de litige, les parties s'engagent à rechercher une solution amiable. "
         f"À défaut, le tribunal compétent sera celui du siège social de {societe.get('nom', 'Proprexis')}."),
    ]

    for titre, texte in articles:
        story.append(Paragraph(titre, s_title))
        story.append(Paragraph(texte, s_body))
        story.append(HRFlowable(width='100%', thickness=0.3, color=BORDER))

    story.append(Spacer(1, 8*mm))
    story.append(Paragraph(
        f"Document émis par {societe.get('nom', 'Proprexis')} — "
        f"SIRET {societe.get('siret', 'XXX')} — "
        f"{societe.get('adresse', 'Île-de-France')}",
        ParagraphStyle('footer', fontName='Helvetica', fontSize=8, textColor=MUTED)
    ))

    doc.build(story)
    return buffer.getvalue()