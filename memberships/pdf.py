"""Membership ID card PDF generation (ReportLab, pure Python)."""
import io
import qrcode
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

NAVY = HexColor('#0B3D91')
RED = HexColor('#C8102E')
GOLD = HexColor('#C8B470')
INK = HexColor('#0f172a')
MUTED = HexColor('#64748b')
WHITE = HexColor('#FFFFFF')
CREAM = HexColor('#FFFDF7')


def _qr_png(data: str):
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#0B3D91', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def render_member_card_pdf(membership, request=None):
    """Generate an A4 PDF with a member ID card + details block."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    # Verification URL
    if request:
        verify_url = request.build_absolute_uri(
            f'/membership/verify/{membership.member_number}/')
    else:
        verify_url = f'https://kenyakorea.com/membership/verify/{membership.member_number}/'

    # ==== Header band ====
    c.setFillColor(NAVY)
    c.rect(0, H - 45*mm, W, 45*mm, fill=1, stroke=0)
    # Gold divider line
    c.setFillColor(GOLD)
    c.rect(0, H - 46*mm, W, 1*mm, fill=1, stroke=0)

    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 26)
    c.drawCentredString(W/2, H - 22*mm, 'KENYA COMMUNITY IN KOREA')
    c.setFont('Helvetica', 12)
    c.setFillColor(GOLD)
    c.drawCentredString(W/2, H - 32*mm, 'SOTE PAMOJA  ·  All Together')
    c.setFont('Helvetica-Bold', 10)
    c.setFillColor(WHITE)
    c.drawCentredString(W/2, H - 40*mm, 'OFFICIAL MEMBERSHIP CARD')

    # ==== Card (rounded rectangle, 150x90mm, centered) ====
    cw, ch = 150*mm, 90*mm
    cx = (W - cw) / 2
    cy = H - 160*mm
    # Card shadow
    c.setFillColor(HexColor('#e5e7eb'))
    c.roundRect(cx + 1.5*mm, cy - 1.5*mm, cw, ch, 6*mm, fill=1, stroke=0)
    # Card background
    c.setFillColor(CREAM)
    c.setStrokeColor(NAVY)
    c.setLineWidth(1.2)
    c.roundRect(cx, cy, cw, ch, 6*mm, fill=1, stroke=1)
    # Gold stripe top of card
    c.setFillColor(GOLD)
    c.rect(cx, cy + ch - 10*mm, cw, 4*mm, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.rect(cx, cy + ch - 10*mm, cw, 0.8*mm, fill=1, stroke=0)

    # Member number big
    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 22)
    c.drawString(cx + 8*mm, cy + ch - 25*mm, membership.member_number or '—')
    c.setFont('Helvetica', 7.5)
    c.setFillColor(MUTED)
    c.drawString(cx + 8*mm, cy + ch - 29*mm, 'MEMBER NUMBER')

    # Member name
    full_name = membership.user.get_full_name() or membership.user.username
    c.setFillColor(INK)
    c.setFont('Helvetica-Bold', 14)
    c.drawString(cx + 8*mm, cy + ch - 45*mm, full_name[:40])
    c.setFont('Helvetica', 7.5)
    c.setFillColor(MUTED)
    c.drawString(cx + 8*mm, cy + ch - 49*mm, 'MEMBER')

    # Tier
    c.setFillColor(INK)
    c.setFont('Helvetica-Bold', 10)
    c.drawString(cx + 8*mm, cy + ch - 60*mm, membership.tier.name)
    c.setFont('Helvetica', 7.5)
    c.setFillColor(MUTED)
    c.drawString(cx + 8*mm, cy + ch - 64*mm, 'TIER')

    # Validity
    valid_from = membership.period_start.strftime('%d %b %Y') if membership.period_start else '—'
    valid_to = membership.period_end.strftime('%d %b %Y') if membership.period_end else '—'
    c.setFillColor(INK)
    c.setFont('Helvetica-Bold', 10)
    c.drawString(cx + 8*mm, cy + ch - 75*mm, f'{valid_from}  →  {valid_to}')
    c.setFont('Helvetica', 7.5)
    c.setFillColor(MUTED)
    c.drawString(cx + 8*mm, cy + ch - 79*mm, 'VALIDITY')

    # QR code (bottom right of card)
    qr_img = ImageReader(_qr_png(verify_url))
    qr_size = 30*mm
    c.drawImage(qr_img, cx + cw - qr_size - 8*mm, cy + 8*mm, qr_size, qr_size, mask='auto')
    c.setFont('Helvetica', 6.5)
    c.setFillColor(MUTED)
    c.drawRightString(cx + cw - 8*mm, cy + 5*mm, 'Scan to verify')

    # ==== Details block below card ====
    y = cy - 18*mm
    c.setFillColor(INK)
    c.setFont('Helvetica-Bold', 11)
    c.drawString(30*mm, y, 'Verification')
    c.setFont('Helvetica', 9)
    c.setFillColor(MUTED)
    y -= 6*mm
    c.drawString(30*mm, y, f'This card is authentic and registered in the KCK membership registry.')
    y -= 5*mm
    c.drawString(30*mm, y, f'Verify at:  {verify_url}')
    y -= 5*mm
    c.drawString(30*mm, y, f'Reference:  {membership.reference_code}')

    # Footer
    c.setFillColor(NAVY)
    c.rect(0, 0, W, 18*mm, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(0, 18*mm, W, 0.8*mm, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 9)
    c.drawCentredString(W/2, 10*mm, 'Kenya Community in Korea  ·  kenyakorea.com')
    c.setFont('Helvetica', 7.5)
    c.setFillColor(GOLD)
    c.drawCentredString(W/2, 5*mm,
        'This card certifies the holder is a paid-up member of KCK for the validity period shown.')

    c.showPage()
    c.save()
    buf.seek(0)
    return buf
