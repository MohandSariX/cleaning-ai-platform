from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, BaseDocTemplate,
                                 Frame, PageTemplate)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from io import BytesIO
from datetime import date, datetime

# ── Couleurs ────────────────────────────────────────────────
DARK         = colors.HexColor('#0f172a')
ACCENT       = colors.HexColor('#3b82f6')
ACCENT_LIGHT = colors.HexColor('#eff6ff')
MUTED        = colors.HexColor('#64748b')
LIGHT_GRAY   = colors.HexColor('#f1f5f9')
BORDER       = colors.HexColor('#e2e8f0')
WHITE        = colors.white

W, H = A4


def _header_footer(canvas_obj, doc, devis_data):
    canvas_obj.saveState()

    # Bandeau header
    canvas_obj.setFillColor(DARK)
    canvas_obj.rect(0, H - 55*mm, W, 55*mm, fill=1, stroke=0)

    # Nom entreprise
    canvas_obj.setFillColor(WHITE)
    canvas_obj.setFont('Helvetica-Bold', 22)
    canvas_obj.drawString(20*mm, H - 22*mm, 'PROPREXIS')

    # Tagline
    canvas_obj.setFont('Helvetica', 9)
    canvas_obj.setFillColor(colors.HexColor('#94a3b8'))
    canvas_obj.drawString(20*mm, H - 30*mm, 'Nettoyage professionnel')

    # Coordonnees entreprise (droite)
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.setFillColor(colors.HexColor('#cbd5e1'))
    for i, line in enumerate(['contact@proprexis.fr', '06 XX XX XX XX', 'Paris, Ile-de-France']):
        canvas_obj.drawRightString(W - 20*mm, H - (20 + i*5)*mm, line)

    # Footer
    canvas_obj.setFillColor(MUTED)
    canvas_obj.setFont('Helvetica', 8)
    today_str = date.today().strftime('%d/%m/%Y')
    canvas_obj.drawString(20*mm, 12*mm, f"Devis {devis_data.get('numero', '')} - genere le {today_str}")
    canvas_obj.drawRightString(W - 20*mm, 12*mm, f"Page {canvas_obj.getPageNumber()}")

    canvas_obj.setStrokeColor(BORDER)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(20*mm, 18*mm, W - 20*mm, 18*mm)

    canvas_obj.restoreState()


def generate_devis_pdf(devis_data: dict, client_data: dict) -> bytes:
    buffer = BytesIO()

    doc = BaseDocTemplate(
        buffer, pagesize=A4,
        topMargin=63*mm, bottomMargin=25*mm,
        leftMargin=20*mm, rightMargin=20*mm,
    )

    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='main')
    template = PageTemplate(
        id='main', frames=[frame],
        onPage=lambda c, d: _header_footer(c, d, devis_data),
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

    story = []

    # Titre
    story.append(Paragraph('DEVIS', s_title))
    story.append(Paragraph(devis_data.get('numero', 'DEV-XXXX-XXX'), s_numero))

    # Bloc client / infos
    emission = devis_data.get('date_emission') or date.today().strftime('%Y-%m-%d')
    try:
        emission_fmt = datetime.strptime(str(emission), '%Y-%m-%d').strftime('%d/%m/%Y')
    except Exception:
        emission_fmt = str(emission)

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
        f"<b>Date d emission :</b> {emission_fmt}<br/>"
        f"<b>Validite :</b> 30 jours<br/>"
        f"<b>Reference :</b> {devis_data.get('numero', '')}"
    )

    bloc = Table(
        [[Paragraph(f"<b>Adresse a :</b><br/>{client_text}", s_body),
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
    story.append(Spacer(1, 8*mm))

    # Prestation
    story.append(Paragraph('PRESTATION', s_section))

    service_map = {
        'bureaux': 'Nettoyage de bureaux',
        'fin_chantier': 'Nettoyage fin de chantier',
        'copropriete': 'Nettoyage copropriete',
        'autre': 'Prestation de nettoyage',
    }
    freq_map = {
        'unique': 'Prestation unique',
        'hebdo': 'Hebdomadaire',
        'bihebdo': 'Bi-hebdomadaire',
        'mensuel': 'Mensuel',
    }

    service_label = service_map.get(devis_data.get('service_type', ''), 'Nettoyage professionnel')
    freq_label    = freq_map.get(devis_data.get('frequence', 'unique'), 'Prestation unique')
    description   = devis_data.get('description') or service_label
    surface       = devis_data.get('surface_m2')
    montant_ht    = float(devis_data.get('montant_ht', 0) or 0)

    detail_text = f"{description}"
    if surface:
        detail_text += f" ({surface} m2)"
    detail_text += f"<br/><font size='8' color='#64748b'>{freq_label}</font>"

    def fmt(n): return f"{n:,.2f} EUR".replace(',', ' ')

    presta = Table(
        [
            [Paragraph('<b>Designation</b>', s_bold),
             Paragraph('<b>Detail</b>', s_bold),
             Paragraph('<b>Qte</b>', s_bold),
             Paragraph('<b>Prix HT</b>', s_bold)],
            [Paragraph(service_label, s_body),
             Paragraph(detail_text, s_body),
             Paragraph('1', s_body),
             Paragraph(fmt(montant_ht), s_body)],
        ],
        colWidths=[doc.width*0.22, doc.width*0.43, doc.width*0.1, doc.width*0.25]
    )
    presta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DARK),
        ('TEXTCOLOR',  (0, 0), (-1, 0), WHITE),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, 1), WHITE),
        ('ALIGN',      (2, 0), (-1, -1), 'CENTER'),
        ('ALIGN',      (3, 0), (-1, -1), 'RIGHT'),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID',       (0, 0), (-1, -1), 0.3, BORDER),
        ('PADDING',    (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
    ]))
    story.append(presta)
    story.append(Spacer(1, 4*mm))

    # Totaux
    tva_pct = float(devis_data.get('tva_pct', 20) or 20)
    tva_amt = round(montant_ht * tva_pct / 100, 2)
    ttc     = round(montant_ht + tva_amt, 2)

    totaux = Table(
        [
            ['', '', Paragraph('Sous-total HT', s_body), Paragraph(fmt(montant_ht), s_body)],
            ['', '', Paragraph(f'TVA {tva_pct:.0f}%', s_body), Paragraph(fmt(tva_amt), s_body)],
            ['', '', Paragraph('<b>TOTAL TTC</b>', s_white_b), Paragraph(f'<b>{fmt(ttc)}</b>', s_white)],
        ],
        colWidths=[doc.width*0.2, doc.width*0.35, doc.width*0.25, doc.width*0.2]
    )
    totaux.setStyle(TableStyle([
        ('ALIGN',      (2, 0), (-1, -1), 'RIGHT'),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING',    (2, 0), (-1, -1), 8),
        ('LINEABOVE',  (2, 0), (-1, 0), 0.5, BORDER),
        ('LINEBELOW',  (2, 1), (-1, 1), 0.5, BORDER),
        ('BACKGROUND', (2, 2), (-1, 2), ACCENT),
        ('PADDING',    (2, 2), (-1, 2), 10),
    ]))
    story.append(totaux)
    story.append(Spacer(1, 10*mm))

    # Conditions
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('CONDITIONS', s_section))

    for cond in [
        'Devis valable 30 jours a compter de la date d emission.',
        'Paiement a reception de facture par virement bancaire.',
        'En cas d acceptation, merci de retourner ce devis signe avec la mention "Bon pour accord".',
        'Toute prestation supplementaire fera l objet d un devis complementaire.',
    ]:
        story.append(Paragraph(f'- {cond}', s_small))
        story.append(Spacer(1, 1*mm))

    story.append(Spacer(1, 8*mm))

    # Zone signature
    sign = Table(
        [[Paragraph('<b>Cachet et signature client</b><br/><font size="8" color="#64748b">Bon pour accord - Date : ___________</font>', s_body),
          Paragraph('<b>Signature Proprexis</b><br/><font size="8" color="#64748b">Gerant</font>', s_body)]],
        colWidths=[doc.width * 0.5, doc.width * 0.5]
    )
    sign.setStyle(TableStyle([
        ('BOX',        (0, 0), (0, 0), 0.5, BORDER),
        ('BOX',        (1, 0), (1, 0), 0.5, BORDER),
        ('PADDING',    (0, 0), (-1, -1), 12),
        ('MINROWHEIGHT', (0, 0), (-1, -1), 35*mm),
        ('VALIGN',     (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (0, 0), LIGHT_GRAY),
        ('BACKGROUND', (1, 0), (1, 0), ACCENT_LIGHT),
    ]))
    story.append(sign)

    doc.build(story)
    return buffer.getvalue()