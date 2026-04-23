"""PDF generation for KCK endorsements / cover notes using ReportLab."""
import io
import os
import qrcode
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
)
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader


NAVY = HexColor('#0B3D91')
RED = HexColor('#C8102E')
GREEN = HexColor('#007A33')
DARK = HexColor('#1a1a1a')
GRAY = HexColor('#555555')
GOLD = HexColor('#C8B470')
BLACK = HexColor('#000000')


def _generate_qr(data: str):
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#003366', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def _make_letterhead_canvas(endorsement, verification_url):
    """Return a canvas-draw function for each page."""
    def _draw(canv, doc):
        canv.saveState()
        width, height = A4
        logo_path = str(settings.STATICFILES_DIRS[0] / 'images' / 'kck-logo.png')

        # Watermark
        if os.path.exists(logo_path):
            try:
                canv.setFillAlpha(0.04)
                canv.drawImage(logo_path, width/2 - 75*mm, height/2 - 75*mm,
                              width=150*mm, height=150*mm, mask='auto', preserveAspectRatio=True)
                canv.setFillAlpha(1.0)
            except Exception:
                pass

        # Letterhead (top)
        top_y = height - 15*mm
        if os.path.exists(logo_path):
            try:
                canv.drawImage(logo_path, 18*mm, top_y - 22*mm, width=22*mm, height=22*mm,
                              mask='auto', preserveAspectRatio=True)
            except Exception:
                pass

        canv.setFillColor(RED)
        canv.setFont('Helvetica-Bold', 16)
        canv.drawString(44*mm, top_y - 8*mm, 'KENYA COMMUNITY IN KOREA')
        canv.setFillColor(GRAY)
        canv.setFont('Helvetica-Oblique', 8)
        canv.drawString(44*mm, top_y - 12*mm, 'Community Organisation for Kenyans in the Republic of Korea')
        # Slogan: SOTE PAMOJA (prominent in gold)
        canv.setFillColor(HexColor('#9d7a00'))
        canv.setFont('Helvetica-Bold', 9)
        canv.drawString(44*mm, top_y - 16*mm, 'SOTE  PAMOJA  \u00b7  All Together')
        canv.setFillColor(GOLD)
        canv.setFont('Helvetica-Oblique', 7)
        canv.drawString(44*mm, top_y - 19*mm, 'A Community Liaison — Not a Government Body')

        # Right contact
        canv.setFillColor(DARK)
        canv.setFont('Helvetica', 8)
        canv.drawRightString(width - 18*mm, top_y - 5*mm, 'info@kenyakorea.com')
        canv.drawRightString(width - 18*mm, top_y - 9*mm, '+82-2-XXXX-XXXX')
        canv.drawRightString(width - 18*mm, top_y - 13*mm, 'kenyakorea.com')

        # Navy underline
        canv.setStrokeColor(NAVY)
        canv.setLineWidth(2)
        canv.line(18*mm, top_y - 24*mm, width - 18*mm, top_y - 24*mm)

        # Flag bar
        bar_y = top_y - 27*mm
        bar_h = 2*mm
        bar_w = width - 36*mm
        canv.setFillColor(BLACK); canv.rect(18*mm, bar_y, bar_w/3, bar_h, fill=1, stroke=0)
        canv.setFillColor(RED); canv.rect(18*mm + bar_w/3, bar_y, bar_w/3, bar_h, fill=1, stroke=0)
        canv.setFillColor(GREEN); canv.rect(18*mm + 2*bar_w/3, bar_y, bar_w/3, bar_h, fill=1, stroke=0)

        # Footer — QR + verification info
        footer_y = 20*mm
        canv.setStrokeColor(RED)
        canv.setLineWidth(1.2)
        canv.line(18*mm, footer_y + 10*mm, width - 18*mm, footer_y + 10*mm)

        # QR code
        try:
            qr_buf = _generate_qr(verification_url)
            qr_img = ImageReader(qr_buf)
            canv.drawImage(qr_img, 18*mm, footer_y - 2*mm, width=18*mm, height=18*mm, mask='auto')
        except Exception:
            pass

        # Verification text (center/right)
        canv.setFillColor(GRAY)
        canv.setFont('Helvetica-Bold', 8)
        canv.drawString(40*mm, footer_y + 6*mm, 'Verify the authenticity of this document online:')
        canv.setFont('Helvetica', 7)
        canv.drawString(40*mm, footer_y + 3*mm, verification_url)
        canv.setFont('Helvetica-Oblique', 7)
        canv.drawString(40*mm, footer_y, f'Reference: {endorsement.reference_number}')
        canv.drawString(40*mm, footer_y - 3*mm,
            'This is an official endorsement issued by the Kenya Community in Korea (KCK).')

        canv.restoreState()
    return _draw


def render_endorsement_pdf(endorsement, request=None):
    """Generate a formatted PDF for an endorsement/cover note."""
    if request:
        verification_url = request.build_absolute_uri(
            f'/endorsements/verify/{endorsement.verification_code}/'
        )
    else:
        verification_url = f'http://127.0.0.1:8000/endorsements/verify/{endorsement.verification_code}/'

    issuer = endorsement.issued_by
    issuer_name = endorsement.issued_by_name or (
        issuer.user.get_full_name() if issuer and issuer.user else 'KCK President'
    )
    issuer_role = endorsement.issued_by_role or (
        issuer.get_role_display() if issuer else 'President, KCK'
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=50*mm, bottomMargin=35*mm,
        leftMargin=22*mm, rightMargin=22*mm,
    )

    story = []
    styles = getSampleStyleSheet()

    # Reference + date row
    date_str = (endorsement.issued_at or endorsement.created_at or timezone.now()).strftime('%B %d, %Y')
    ref_date = [[
        Paragraph(
            f'<b>Our Ref:</b> {endorsement.reference_number}',
            ParagraphStyle('ref', parent=styles['Normal'], fontSize=10)
        ),
        Paragraph(
            f'<i>Date: {date_str}</i>',
            ParagraphStyle('date', parent=styles['Normal'], fontSize=10, alignment=TA_RIGHT)
        ),
    ]]
    tbl = Table(ref_date, colWidths=[80*mm, 80*mm])
    tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 6*mm))

    # Addressed to
    if endorsement.addressed_to:
        story.append(Paragraph(
            f'<b>{endorsement.addressed_to}</b>',
            ParagraphStyle('to', parent=styles['Normal'], fontSize=11, spaceAfter=2)
        ))
        if endorsement.addressed_to_address:
            for line in endorsement.addressed_to_address.splitlines():
                if line.strip():
                    story.append(Paragraph(
                        line.strip(),
                        ParagraphStyle('addr', parent=styles['Normal'], fontSize=10, spaceAfter=0)
                    ))
    else:
        story.append(Paragraph(
            '<b>TO WHOM IT MAY CONCERN</b>',
            ParagraphStyle('to', parent=styles['Normal'], fontSize=11, spaceAfter=2)
        ))
    story.append(Spacer(1, 6*mm))

    # Subject (centered, underlined, navy)
    story.append(Paragraph(
        f'<u>RE: {endorsement.subject.upper()}</u>',
        ParagraphStyle(
            'subject', parent=styles['Heading3'], alignment=TA_CENTER,
            fontSize=12, textColor=NAVY, fontName='Helvetica-Bold', spaceAfter=8,
        )
    ))
    story.append(Spacer(1, 4*mm))

    # Salutation
    if endorsement.addressed_to:
        salutation = 'Dear Sir/Madam,'
    else:
        salutation = 'Dear Sir/Madam,'
    story.append(Paragraph(
        f'<b>{salutation}</b>',
        ParagraphStyle('salut', parent=styles['Normal'], fontSize=11, spaceAfter=10)
    ))

    # Body
    body_style = ParagraphStyle(
        'body', parent=styles['Normal'], fontSize=11,
        alignment=TA_JUSTIFY, leading=16, spaceAfter=8,
    )

    # Intro paragraph referencing the member
    intro = (
        f'This is to confirm and endorse <b>{endorsement.member_full_name}</b>'
    )
    if endorsement.member_id_number:
        intro += f' (ID/Passport No: <b>{endorsement.member_id_number}</b>)'
    intro += ' who is known to the Kenya Community in Korea (KCK).'
    story.append(Paragraph(intro, body_style))

    # Member standing
    if endorsement.member_standing:
        for para in endorsement.member_standing.split('\n\n'):
            if para.strip():
                story.append(Paragraph(para.replace('\n', '<br/>'), body_style))

    # Purpose statement
    if endorsement.purpose:
        story.append(Paragraph(
            f'<b>Purpose of this letter:</b> {endorsement.purpose}',
            body_style
        ))

    # Main body
    for para in endorsement.body.split('\n\n'):
        if para.strip():
            story.append(Paragraph(para.replace('\n', '<br/>'), body_style))

    # Validity notice
    if endorsement.valid_until:
        story.append(Paragraph(
            f'<i>This endorsement is valid from {endorsement.valid_from.strftime("%B %d, %Y")} '
            f'to {endorsement.valid_until.strftime("%B %d, %Y")}.</i>',
            ParagraphStyle('valid', parent=styles['Normal'], fontSize=10, textColor=GRAY, spaceAfter=6)
        ))

    # Standard closing notice
    story.append(Paragraph(
        '<i>Any assistance extended to the above-named will be highly appreciated.</i>',
        ParagraphStyle('close_note', parent=styles['Normal'], fontSize=10, spaceAfter=10)
    ))

    story.append(Spacer(1, 8*mm))
    story.append(Paragraph(
        'Yours faithfully,',
        ParagraphStyle('closing', parent=styles['Normal'], fontSize=11, spaceAfter=4)
    ))

    # Signature
    if issuer and issuer.signature:
        try:
            sig_path = issuer.signature.path
            if os.path.exists(sig_path):
                story.append(RLImage(sig_path, width=40*mm, height=15*mm))
        except Exception:
            pass
    else:
        story.append(Spacer(1, 12*mm))  # space for wet signature

    story.append(Paragraph(
        f'<b><font color="#0B3D91">{issuer_name}</font></b>',
        ParagraphStyle('sname', parent=styles['Normal'], fontSize=11, spaceAfter=2)
    ))
    story.append(Paragraph(
        f'<i>{issuer_role}</i>',
        ParagraphStyle('srole', parent=styles['Normal'], fontSize=10, textColor=GRAY, spaceAfter=2)
    ))
    story.append(Paragraph(
        'Kenya Community in Korea (KCK)',
        ParagraphStyle('org', parent=styles['Normal'], fontSize=10, textColor=GRAY)
    ))

    on_page = _make_letterhead_canvas(endorsement, verification_url)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return buf.getvalue()


def issue_endorsement(endorsement, request=None):
    """Generate PDF and mark the endorsement as issued."""
    endorsement.status = 'generating'
    endorsement.save(update_fields=['status'])
    try:
        pdf_bytes = render_endorsement_pdf(endorsement, request=request)
        filename = f'{endorsement.reference_number.replace("/", "-")}.pdf'
        endorsement.pdf_file.save(filename, ContentFile(pdf_bytes), save=False)
        endorsement.status = 'issued'
        endorsement.issued_at = timezone.now()
        endorsement.save()
        return True
    except Exception:
        endorsement.status = 'draft'
        endorsement.save(update_fields=['status'])
        raise
