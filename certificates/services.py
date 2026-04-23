"""Certificate PDF generation using ReportLab (pure Python, no GTK needed)."""
import io
import os
import qrcode
from django.conf import settings
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader


# KCK brand colors
NAVY = HexColor('#0B3D91')
RED = HexColor('#C8102E')
GOLD = HexColor('#C8B470')
CREAM = HexColor('#FFFDF7')
DARK = HexColor('#1a1a1a')
GRAY = HexColor('#666666')
BLACK = HexColor('#000000')
GREEN = HexColor('#007A33')


_FONTS_REGISTERED = False

def _register_fonts():
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    try:
        font_path = str(settings.STATICFILES_DIRS[0] / 'fonts' / 'GreatVibes-Regular.ttf')
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('GreatVibes', font_path))
    except Exception:
        pass
    _FONTS_REGISTERED = True


def generate_qr_code(data: str):
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#003366', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def _draw_wrapped_text(canv, text, x, y, width, font='Helvetica', size=11, line_height=16):
    canv.setFont(font, size)
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = ' '.join(current + [word])
        if canv.stringWidth(test, font, size) <= width:
            current.append(word)
        else:
            if current:
                lines.append(' '.join(current))
            current = [word]
    if current:
        lines.append(' '.join(current))
    lines = lines[:6]
    for line in lines:
        canv.drawCentredString(x, y, line)
        y -= line_height
    return y


def render_certificate_pdf(certificate, request=None):
    """Generate a beautiful A4 landscape certificate PDF using ReportLab."""
    _register_fonts()

    if request:
        verification_url = request.build_absolute_uri(
            f'/certificates/verify/{certificate.verification_code}/'
        )
    else:
        verification_url = f'http://127.0.0.1:8000/certificates/verify/{certificate.verification_code}/'

    buf = io.BytesIO()
    page_size = landscape(A4)
    width, height = page_size
    c = canvas.Canvas(buf, pagesize=page_size)

    # Cream background
    c.setFillColor(CREAM)
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # Borders
    c.setStrokeColor(NAVY)
    c.setLineWidth(8)
    c.rect(12*mm, 12*mm, width - 24*mm, height - 24*mm, fill=0, stroke=1)
    c.setLineWidth(2)
    c.rect(16*mm, 16*mm, width - 32*mm, height - 32*mm, fill=0, stroke=1)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.rect(20*mm, 20*mm, width - 40*mm, height - 40*mm, fill=0, stroke=1)

    # Red corner ornaments
    c.setStrokeColor(RED)
    c.setLineWidth(3)
    cs = 25
    c.line(25*mm, height - 25*mm, 25*mm + cs, height - 25*mm)
    c.line(25*mm, height - 25*mm, 25*mm, height - 25*mm - cs)
    c.line(width - 25*mm, height - 25*mm, width - 25*mm - cs, height - 25*mm)
    c.line(width - 25*mm, height - 25*mm, width - 25*mm, height - 25*mm - cs)
    c.line(25*mm, 25*mm, 25*mm + cs, 25*mm)
    c.line(25*mm, 25*mm, 25*mm, 25*mm + cs)
    c.line(width - 25*mm, 25*mm, width - 25*mm - cs, 25*mm)
    c.line(width - 25*mm, 25*mm, width - 25*mm, 25*mm + cs)

    # Watermark logo
    logo_path = str(settings.STATICFILES_DIRS[0] / 'images' / 'kck-logo.png')
    if os.path.exists(logo_path):
        try:
            c.saveState()
            c.setFillAlpha(0.06)
            c.drawImage(logo_path, width/2 - 50*mm, height/2 - 50*mm,
                       width=100*mm, height=100*mm, mask='auto', preserveAspectRatio=True)
            c.restoreState()
        except Exception:
            pass

    center_x = width / 2
    y = height - 35*mm

    # Logo
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, center_x - 15*mm, y - 5*mm, width=30*mm, height=30*mm,
                       mask='auto', preserveAspectRatio=True)
        except Exception:
            pass
    y -= 32*mm

    # Org name
    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 18)
    c.drawCentredString(center_x, y, 'KENYA COMMUNITY IN KOREA')
    y -= 6*mm
    c.setFillColor(GRAY)
    c.setFont('Helvetica', 9)
    c.drawCentredString(center_x, y, 'C O N N E C T I N G   K E N Y A N S   I N   S O U T H   K O R E A')
    y -= 5*mm
    # Slogan: SOTE PAMOJA
    c.setFillColor(HexColor('#9d7a00'))  # deep gold
    c.setFont('Helvetica-BoldOblique', 11)
    c.drawCentredString(center_x, y, '\u2014  S O T E   P A M O J A  \u2014')
    y -= 4*mm

    # Kenyan flag bar
    bar_w = 60*mm; bar_h = 3*mm; bx = center_x - bar_w/2
    c.setFillColor(BLACK); c.rect(bx, y - bar_h, bar_w/3, bar_h, fill=1, stroke=0)
    c.setFillColor(RED); c.rect(bx + bar_w/3, y - bar_h, bar_w/3, bar_h, fill=1, stroke=0)
    c.setFillColor(GREEN); c.rect(bx + 2*bar_w/3, y - bar_h, bar_w/3, bar_h, fill=1, stroke=0)
    y -= 15*mm

    # Title
    c.setFillColor(RED)
    c.setFont('Helvetica-Bold', 34)
    c.drawCentredString(center_x, y, 'CERTIFICATE')
    y -= 10*mm
    c.setFillColor(NAVY)
    c.setFont('Helvetica-BoldOblique', 16)
    type_display = certificate.get_cert_type_display().replace('Certificate of ', '').replace('Certificate', '').strip() or 'Recognition'
    c.drawCentredString(center_x, y, f'of {type_display}')
    y -= 10*mm

    # Divider
    c.setStrokeColor(GOLD); c.setLineWidth(1)
    c.line(center_x - 50*mm, y, center_x - 8*mm, y)
    c.line(center_x + 8*mm, y, center_x + 50*mm, y)
    c.setFillColor(GOLD)
    c.saveState(); c.translate(center_x, y); c.rotate(45)
    c.rect(-2*mm, -2*mm, 4*mm, 4*mm, fill=1, stroke=0)
    c.restoreState()
    y -= 10*mm

    # "presented to"
    c.setFillColor(GRAY)
    c.setFont('Helvetica-Oblique', 12)
    c.drawCentredString(center_x, y, 'This certificate is proudly presented to')
    y -= 14*mm

    # Recipient name
    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 30)
    c.drawCentredString(center_x, y, certificate.recipient_name)
    name_w = c.stringWidth(certificate.recipient_name, 'Helvetica-Bold', 30)
    ul_w = max(name_w + 20*mm, 80*mm)
    c.setStrokeColor(GOLD); c.setLineWidth(1.5)
    c.line(center_x - ul_w/2, y - 3*mm, center_x + ul_w/2, y - 3*mm)
    y -= 14*mm

    # Body
    c.setFillColor(DARK)
    y = _draw_wrapped_text(c, certificate.body, center_x, y, width - 80*mm,
                          font='Helvetica', size=12, line_height=16)
    y -= 4*mm

    if certificate.event_title:
        c.setFillColor(GRAY)
        c.setFont('Helvetica-Oblique', 10)
        c.drawCentredString(center_x, y, f'- {certificate.event_title} -')

    # Footer
    footer_y = 35*mm
    issuer = certificate.issued_by
    issuer_name = certificate.issued_by_name or (
        issuer.user.get_full_name() if issuer and issuer.user else 'KCK Secretariat'
    )
    issuer_role = certificate.issued_by_role or (
        issuer.get_role_display() if issuer else 'Official'
    )

    # Signature (left)
    sig_x = width * 0.22
    try:
        c.setFont('GreatVibes', 26)
        c.setFillColor(NAVY)
        c.drawCentredString(sig_x, footer_y + 12*mm, issuer_name)
    except Exception:
        c.setFont('Helvetica-Oblique', 14)
        c.setFillColor(NAVY)
        c.drawCentredString(sig_x, footer_y + 12*mm, issuer_name)

    if issuer and issuer.signature:
        try:
            sig_path = issuer.signature.path
            if os.path.exists(sig_path):
                c.drawImage(sig_path, sig_x - 20*mm, footer_y + 8*mm, width=40*mm, height=15*mm,
                           mask='auto', preserveAspectRatio=True)
        except Exception:
            pass

    c.setStrokeColor(DARK); c.setLineWidth(1)
    c.line(sig_x - 30*mm, footer_y + 6*mm, sig_x + 30*mm, footer_y + 6*mm)
    c.setFillColor(NAVY); c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(sig_x, footer_y + 2*mm, issuer_name)
    c.setFillColor(GRAY); c.setFont('Helvetica-Oblique', 9)
    c.drawCentredString(sig_x, footer_y - 2*mm, issuer_role)

    # Cert info (center)
    info_x = width / 2
    c.setFillColor(NAVY); c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(info_x, footer_y + 12*mm, 'Date Issued')
    c.setFillColor(DARK); c.setFont('Helvetica', 10)
    date_str = certificate.issued_date.strftime('%B %d, %Y') if certificate.issued_date else ''
    c.drawCentredString(info_x, footer_y + 8*mm, date_str)
    c.setFillColor(NAVY); c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(info_x, footer_y + 2*mm, 'Certificate No.')
    c.setFont('Helvetica-Bold', 11); c.setFillColor(RED)
    c.drawCentredString(info_x, footer_y - 2*mm, certificate.cert_number)

    # QR (right)
    qr_x = width * 0.78
    qr_buf = generate_qr_code(verification_url)
    qr_img = ImageReader(qr_buf)
    qr_size = 22*mm
    c.drawImage(qr_img, qr_x - qr_size/2, footer_y, width=qr_size, height=qr_size, mask='auto')
    c.setFillColor(GRAY); c.setFont('Helvetica', 7)
    c.drawCentredString(qr_x, footer_y - 3*mm, 'Scan to verify')

    c.setFillColor(GRAY); c.setFont('Helvetica-Oblique', 8)
    c.drawCentredString(width/2, 24*mm, 'Verify at kenyakorea.com/certificates')

    c.showPage()
    c.save()
    return buf.getvalue()


def issue_certificate(certificate, request=None):
    certificate.status = 'generating'
    certificate.save(update_fields=['status'])
    try:
        pdf_bytes = render_certificate_pdf(certificate, request=request)
        filename = f'{certificate.cert_number}.pdf'
        certificate.pdf_file.save(filename, ContentFile(pdf_bytes), save=False)
        certificate.status = 'published'
        certificate.save()
        return True
    except Exception:
        certificate.status = 'failed'
        certificate.save(update_fields=['status'])
        raise
