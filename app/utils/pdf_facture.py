from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (Paragraph, Spacer, Table, TableStyle,
                                 HRFlowable, BaseDocTemplate, Frame, PageTemplate)
from reportlab.lib.styles import ParagraphStyle
from io import BytesIO
from datetime import date, datetime

DARK         = colors.HexColor('#0f172a')
ACCENT       = colors.HexColor('#3b82f6')
ACCENT_LIGHT = colors.HexColor('#eff6ff')
GREEN        = colors.HexColor('#22c55e')
GREEN_LIGHT  = colors.HexColor('#f0fdf4')
MUTED        = colors.HexColor('#64748b')
LIGHT_GRAY   = colors.HexColor('#f1f5f9')
BORDER       = colors.HexColor('#e2e8f0')
WHITE        = colors.white

W, H = A4

# RIB entreprise — à personnaliser
RIB = {
    'banque':   'Crédit Mutuel',
    'titulaire': 'PROPREXIS',
    'iban':     'FR76 XXXX XXXX XXXX XXXX XXXX XXX',
    'bic':      'CMCIFRPP',
}


def _header_footer(canvas_obj, doc, facture_data):
    canvas_obj.saveState()

    # Bandeau header compact
    canvas_obj.setFillColor(DARK)
    canvas_obj.rect(0, H - 30*mm, W, 30*mm, fill=1, stroke=0)

    # Nom entreprise
    canvas_obj.setFillColor(WHITE)
    canvas_obj.setFont('Helvetica-Bold', 17)
    canvas_obj.drawString(20*mm, H - 14*mm, 'PROPREXIS')

    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.setFillColor(colors.HexColor('#94a3b8'))
    canvas_obj.drawString(20*mm, H - 21*mm, 'Nettoyage professionnel  |  contact@proprexis.fr  |  06 XX XX XX XX')

    # Badge FACTURE (coin droit)
    canvas_obj.setFillColor(ACCENT)
    canvas_obj.roundRect(W - 55*mm, H - 22*mm, 36*mm, 10*mm, 2*mm, fill=1, stroke=0)
    canvas_obj.setFillColor(WHITE)
    canvas_obj.setFont('Helvetica-Bold', 10)
    canvas_obj.drawCentredString(W - 37*mm, H - 18*mm, 'FACTURE')

    # Footer
    canvas_obj.setFillColor(MUTED)
    canvas_obj.setFont('Helvetica', 8)
    today_str = date.today().strftime('%d/%m/%Y')
    canvas_obj.drawString(20*mm, 12*mm, f"Facture {facture_data.get('numero', '')} - {today_str}")
    canvas_obj.drawRightString(W - 20*mm, 12*mm, f"Page {canvas_obj.getPageNumber()}")
    canvas_obj.setStrokeColor(BORDER)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(20*mm, 18*mm, W - 20*mm, 18*mm)

    canvas_obj.restoreState()


def generate_facture_pdf(facture_data: dict, client_data: dict) -> bytes:
    buffer = BytesIO()

    doc = BaseDocTemplate(
        buffer, pagesize=A4,
        topMargin=38*mm, bottomMargin=25*mm,
        leftMargin=20*mm, rightMargin=20*mm,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='main')
    template = PageTemplate(
        id='main', frames=[frame],
        onPage=lambda c, d: _header_footer(c, d, facture_data),
    )
    doc.addPageTemplates([template])

    # Styles
    s_title   = ParagraphStyle('title',   fontName='Helvetica-Bold', fontSize=20, textColor=DARK, spaceAfter=2*mm)
    s_numero  = ParagraphStyle('numero',  fontName='Helvetica',      fontSize=11, textColor=MUTED, spaceAfter=8*mm)
    s_section = ParagraphStyle('section', fontName='Helvetica-Bold', fontSize=9,  textColor=ACCENT, spaceBefore=6*mm, spaceAfter=3*mm)
    s_body    = ParagraphStyle('body',    fontName='Helvetica',      fontSize=10, textColor=DARK, leading=15)
    s_bold    = ParagraphStyle('bold',    fontName='Helvetica-Bold', fontSize=10, textColor=DARK)
    s_small   = ParagraphStyle('small',   fontName='Helvetica',      fontSize=8,  textColor=MUTED, leading=13)
    s_white_b = ParagraphStyle('white_b', fontName='Helvetica-Bold', fontSize=12, textColor=WHITE)
    s_white   = ParagraphStyle('white',   fontName='Helvetica',      fontSize=12, textColor=WHITE)
    s_green_b = ParagraphStyle('green_b', fontName='Helvetica-Bold', fontSize=11, textColor=GREEN)
    s_rib     = ParagraphStyle('rib',     fontName='Helvetica',      fontSize=9,  textColor=DARK, leading=14)

    story = []

    # Titre
    story.append(Paragraph('FACTURE', s_title))
    story.append(Paragraph(facture_data.get('numero', 'FAC-XXXX-XXX'), s_numero))

    # Dates
    def fmt_date(d):
        if not d: return '—'
        try: return datetime.strptime(str(d), '%Y-%m-%d').strftime('%d/%m/%Y')
        except: return str(d)

    emission  = fmt_date(facture_data.get('date_emission'))
    echeance  = fmt_date(facture_data.get('date_echeance'))
    paiement  = fmt_date(facture_data.get('date_paiement'))
    is_payee  = facture_data.get('status') == 'payee'

    # Bloc client / infos
    client_lines = [
        f"<b>{client_data.get('company_name', '')}</b>",
        client_data.get('contact_name') or '',
        client_data.get('address') or '',
        client_data.get('city') or '',
        client_data.get('email') or '',
        client_data.get('phone') or '',
    ]
    client_text = '<br/>'.join(l for l in client_lines if l)

    infos_text = (
        f"<b>Date d emission :</b> {emission}<br/>"
        f"<b>Date d echeance :</b> {echeance}<br/>"
        f"<b>Reference :</b> {facture_data.get('numero', '')}"
    )
    if is_payee and paiement != '—':
        infos_text += f"<br/><b>Paye le :</b> {paiement}"

    bloc = Table(
        [[Paragraph(f"<b>Facture adressee a :</b><br/>{client_text}", s_body),
          Paragraph(infos_text, s_body)]],
        colWidths=[doc.width * 0.55, doc.width * 0.45]
    )
    bloc.setStyle(TableStyle([
        ('VALIGN',     (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (0, 0), LIGHT_GRAY),
        ('BACKGROUND', (1, 0), (1, 0), ACCENT_LIGHT),
        ('BOX',        (0, 0), (0, 0), 0.5, BORDER),
        ('BOX',        (1, 0), (1, 0), 0.5, colors.HexColor('#bfdbfe')),
        ('PADDING',    (0, 0), (-1, -1), 10),
    ]))
    story.append(bloc)

    # Badge PAYEE si applicable
    if is_payee:
        story.append(Spacer(1, 4*mm))
        badge = Table(
            [[Paragraph('FACTURE ACQUITTEE', ParagraphStyle('paid', fontName='Helvetica-Bold', fontSize=11, textColor=GREEN))]],
            colWidths=[doc.width]
        )
        badge.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), GREEN_LIGHT),
            ('BOX',        (0, 0), (-1, -1), 1, GREEN),
            ('PADDING',    (0, 0), (-1, -1), 8),
            ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(badge)

    story.append(Spacer(1, 8*mm))

    # Prestation
    story.append(Paragraph('DETAIL DE LA PRESTATION', s_section))

    description = facture_data.get('description') or 'Prestation de nettoyage'
    montant_ht  = float(facture_data.get('montant_ht', 0) or 0)

    def fmt(n): return f"{n:,.2f} EUR".replace(',', ' ')

    presta = Table(
        [
            [Paragraph('<b>Designation</b>', s_bold),
             Paragraph('<b>Quantite</b>', s_bold),
             Paragraph('<b>Prix unitaire HT</b>', s_bold),
             Paragraph('<b>Total HT</b>', s_bold)],
            [Paragraph(description, s_body),
             Paragraph('1', s_body),
             Paragraph(fmt(montant_ht), s_body),
             Paragraph(fmt(montant_ht), s_body)],
        ],
        colWidths=[doc.width*0.45, doc.width*0.15, doc.width*0.2, doc.width*0.2]
    )
    presta.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), DARK),
        ('TEXTCOLOR',     (0, 0), (-1, 0), WHITE),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0), 9),
        ('BACKGROUND',    (0, 1), (-1, 1), WHITE),
        ('ALIGN',         (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN',         (3, 0), (-1, -1), 'RIGHT'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID',          (0, 0), (-1, -1), 0.3, BORDER),
        ('PADDING',       (0, 0), (-1, -1), 8),
        ('TOPPADDING',    (0, 1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 12),
    ]))
    story.append(presta)
    story.append(Spacer(1, 4*mm))

    # Totaux
    tva_pct = float(facture_data.get('tva_pct', 20) or 20)
    tva_amt = round(montant_ht * tva_pct / 100, 2)
    ttc     = round(montant_ht + tva_amt, 2)

    totaux = Table(
        [
            ['', Paragraph('Sous-total HT', s_body),    Paragraph(fmt(montant_ht), s_body)],
            ['', Paragraph(f'TVA {tva_pct:.0f}%', s_body), Paragraph(fmt(tva_amt), s_body)],
            ['', Paragraph('<b>NET A PAYER TTC</b>', s_white_b), Paragraph(f'<b>{fmt(ttc)}</b>', s_white)],
        ],
        colWidths=[doc.width*0.45, doc.width*0.3, doc.width*0.25]
    )
    totaux.setStyle(TableStyle([
        ('ALIGN',      (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING',    (1, 0), (-1, -1), 8),
        ('LINEABOVE',  (1, 0), (-1, 0), 0.5, BORDER),
        ('LINEBELOW',  (1, 1), (-1, 1), 0.5, BORDER),
        ('BACKGROUND', (1, 2), (-1, 2), ACCENT),
        ('PADDING',    (1, 2), (-1, 2), 10),
    ]))
    story.append(totaux)
    story.append(Spacer(1, 10*mm))

    # RIB / Coordonnees bancaires
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('COORDONNEES BANCAIRES', s_section))

    rib_text = (
        f"<b>Banque :</b> {RIB['banque']}<br/>"
        f"<b>Titulaire :</b> {RIB['titulaire']}<br/>"
        f"<b>IBAN :</b> {RIB['iban']}<br/>"
        f"<b>BIC :</b> {RIB['bic']}<br/>"
        f"<font size='8' color='#64748b'>Merci d indiquer la reference <b>{facture_data.get('numero', '')}</b> en objet du virement.</font>"
    )
    rib_bloc = Table(
        [[Paragraph(rib_text, s_rib)]],
        colWidths=[doc.width]
    )
    rib_bloc.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), ACCENT_LIGHT),
        ('BOX',        (0, 0), (-1, -1), 0.5, colors.HexColor('#bfdbfe')),
        ('PADDING',    (0, 0), (-1, -1), 12),
    ]))
    story.append(rib_bloc)
    story.append(Spacer(1, 6*mm))

    # Mentions legales
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph('MENTIONS LEGALES', s_section))
    for mention in [
        'Paiement a reception de facture. Tout retard de paiement entraine des penalites de 3 fois le taux legal.',
        'En cas de retard, une indemnite forfaitaire de 40 EUR pour frais de recouvrement sera appliquee.',
        'TVA non applicable, article 293 B du CGI. (A adapter selon votre situation fiscale)',
    ]:
        story.append(Paragraph(f'- {mention}', s_small))
        story.append(Spacer(1, 1*mm))

    doc.build(story)
    return buffer.getvalue()