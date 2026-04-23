"""Communication letter PDF generation using ReportLab."""
import io
import os
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


NAVY = HexColor('#0B3D91')
RED = HexColor('#C8102E')
GREEN = HexColor('#007A33')
DARK = HexColor('#1a1a1a')
GRAY = HexColor('#555555')
BLACK = HexColor('#000000')


def _make_page_decorator(communication):
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

        top_y = height - 15*mm
        if os.path.exists(logo_path):
            try:
                canv.drawImage(logo_path, 18*mm, top_y - 20*mm, width=20*mm, height=20*mm,
                              mask='auto', preserveAspectRatio=True)
            except Exception:
                pass

        # Org name
        canv.setFillColor(RED)
        canv.setFont('Helvetica-Bold', 16)
        canv.drawString(42*mm, top_y - 8*mm, 'KENYA COMMUNITY IN KOREA')
        canv.setFillColor(GRAY)
        canv.setFont('Helvetica-Oblique', 8)
        canv.drawString(42*mm, top_y - 12*mm, 'Serving Kenyans in South Korea')
        # Slogan: SOTE PAMOJA
        canv.setFillColor(HexColor('#9d7a00'))
        canv.setFont('Helvetica-Bold', 8)
        canv.drawString(42*mm, top_y - 16*mm, 'SOTE  PAMOJA  \u2014  All Together')

        # Contact right
        canv.setFillColor(DARK)
        canv.setFont('Helvetica', 8)
        canv.drawRightString(width - 18*mm, top_y - 5*mm, 'info@kenyakorea.com')
        canv.drawRightString(width - 18*mm, top_y - 9*mm, '+82-2-XXXX-XXXX')
        canv.drawRightString(width - 18*mm, top_y - 13*mm, 'kenyakorea.com')

        # Underline
        canv.setStrokeColor(NAVY); canv.setLineWidth(2)
        canv.line(18*mm, top_y - 22*mm, width - 18*mm, top_y - 22*mm)

        # Flag bar
        bar_y = top_y - 25*mm; bar_h = 2*mm; bar_w = width - 36*mm
        canv.setFillColor(BLACK); canv.rect(18*mm, bar_y, bar_w/3, bar_h, fill=1, stroke=0)
        canv.setFillColor(RED); canv.rect(18*mm + bar_w/3, bar_y, bar_w/3, bar_h, fill=1, stroke=0)
        canv.setFillColor(GREEN); canv.rect(18*mm + 2*bar_w/3, bar_y, bar_w/3, bar_h, fill=1, stroke=0)

        # Footer
        footer_y = 15*mm
        canv.setStrokeColor(RED); canv.setLineWidth(1.5)
        canv.line(18*mm, footer_y + 5*mm, width - 18*mm, footer_y + 5*mm)
        canv.setFillColor(GRAY); canv.setFont('Helvetica-Oblique', 7)
        canv.drawCentredString(width/2, footer_y + 2*mm,
            f'This is an official communication from the Kenya Community in Korea (KCK). Reference: {communication.reference_number}')
        canv.drawCentredString(width/2, footer_y - 1*mm, 'kenyakorea.com')

        canv.restoreState()
    return _draw


def render_letter_pdf(communication, request=None):
    sender = communication.sender
    sender_name = communication.sender_name_override or (
        sender.user.get_full_name() if sender and sender.user else 'KCK Secretariat'
    )
    sender_role = communication.sender_role_override or (
        sender.get_role_display() if sender else 'Official'
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=45*mm, bottomMargin=25*mm,
        leftMargin=22*mm, rightMargin=22*mm,
    )

    story = []
    styles = getSampleStyleSheet()

    date_str = (communication.published_at or communication.created_at or timezone.now()).strftime('%B %d, %Y')
    ref_date = [[
        Paragraph(f'<b>Ref:</b> {communication.reference_number}',
                  ParagraphStyle('ref', parent=styles['Normal'], fontSize=10)),
        Paragraph(f'<i>{date_str}</i>',
                  ParagraphStyle('date', parent=styles['Normal'], fontSize=10, alignment=TA_RIGHT)),
    ]]
    tbl = Table(ref_date, colWidths=[80*mm, 80*mm])
    tbl.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    story.append(tbl)
    story.append(Spacer(1, 6*mm))

    if communication.category and communication.category != 'general':
        story.append(Paragraph(
            f'<font color="#C8102E"><b>[{communication.get_category_display().upper()}]</b></font>',
            ParagraphStyle('cat', parent=styles['Normal'], alignment=TA_CENTER, fontSize=9)
        ))

    subject_style = ParagraphStyle(
        'subject', parent=styles['Heading3'], alignment=TA_CENTER, fontSize=13,
        textColor=NAVY, fontName='Helvetica-Bold', spaceAfter=8,
    )
    story.append(Paragraph(f'<u>{communication.subject.upper()}</u>', subject_style))
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph(
        '<b>Dear Fellow Kenyans in Korea (KCK Family),</b>',
        ParagraphStyle('salut', parent=styles['Normal'], fontSize=11, spaceAfter=10)
    ))

    body_style = ParagraphStyle(
        'body', parent=styles['Normal'],
        fontSize=11, alignment=TA_JUSTIFY, leading=16, spaceAfter=8,
    )
    for para in communication.body.split('\n\n'):
        if para.strip():
            html_para = para.replace('\n', '<br/>')
            story.append(Paragraph(html_para, body_style))

    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(
        'Kind Regards,',
        ParagraphStyle('closing', parent=styles['Normal'], fontSize=11, spaceAfter=4)
    ))

    if sender and sender.signature:
        try:
            sig_path = sender.signature.path
            if os.path.exists(sig_path):
                story.append(RLImage(sig_path, width=40*mm, height=15*mm))
        except Exception:
            pass

    story.append(Paragraph(
        f'<b><font color="#0B3D91">{sender_name}</font></b>',
        ParagraphStyle('sname', parent=styles['Normal'], fontSize=11, spaceAfter=2)
    ))
    story.append(Paragraph(
        f'<i>{sender_role}</i>',
        ParagraphStyle('srole', parent=styles['Normal'], fontSize=10, textColor=GRAY)
    ))

    on_page = _make_page_decorator(communication)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return buf.getvalue()


def publish_communication(communication, request=None):
    communication.status = 'processing'
    communication.save(update_fields=['status'])
    try:
        pdf_bytes = render_letter_pdf(communication, request=request)
        filename = f'{communication.reference_number.replace("/", "-")}.pdf'
        communication.pdf_file.save(filename, ContentFile(pdf_bytes), save=False)
        communication.status = 'published'
        communication.published_at = timezone.now()
        communication.save()
        return True
    except Exception:
        communication.status = 'draft'
        communication.save(update_fields=['status'])
        raise
