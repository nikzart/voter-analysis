#!/usr/bin/env python3
"""
Generate PDF document with all passwords for distribution
"""

import json
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime


def create_password_pdf():
    """Create PDF with all passwords"""
    base_dir = Path(__file__).parent
    plain_file = base_dir / 'passwords_distribution.json'

    # Load plain passwords
    with open(plain_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    master_password = data['master']
    ward_passwords = data['wards']

    # Create PDF
    pdf_file = base_dir / 'passwords_distribution.pdf'
    doc = SimpleDocTemplate(str(pdf_file), pagesize=A4,
                           rightMargin=0.75*inch, leftMargin=0.75*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)

    # Container for the 'Flowable' objects
    elements = []

    # Define styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.grey,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )

    warning_style = ParagraphStyle(
        'Warning',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.red,
        spaceAfter=20,
        fontName='Helvetica-Bold'
    )

    # Title
    title = Paragraph("Kerala Election Insights Dashboard", title_style)
    subtitle = Paragraph("Access Credentials - CONFIDENTIAL", subtitle_style)
    date = Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", subtitle_style)

    elements.append(title)
    elements.append(subtitle)
    elements.append(date)
    elements.append(Spacer(1, 0.3*inch))

    # Security warning
    warning = Paragraph(
        "⚠️ <b>SECURITY WARNING:</b> This document contains sensitive access credentials. "
        "Keep it secure and distribute only to authorized personnel.",
        warning_style
    )
    elements.append(warning)
    elements.append(Spacer(1, 0.2*inch))

    # Master Password Section
    master_heading = Paragraph("Master Password (Full Access)", heading_style)
    elements.append(master_heading)

    master_data = [
        ['Access Level', 'Password'],
        ['Full Access to All 56 Wards', master_password]
    ]

    master_table = Table(master_data, colWidths=[3*inch, 3.5*inch])
    master_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Courier-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))

    elements.append(master_table)
    elements.append(Spacer(1, 0.4*inch))

    # Ward Passwords Section
    ward_heading = Paragraph("Ward-Specific Passwords (Individual Access)", heading_style)
    elements.append(ward_heading)

    info = Paragraph(
        "Each ward password provides access only to that specific ward's data.",
        styles['Normal']
    )
    elements.append(info)
    elements.append(Spacer(1, 0.2*inch))

    # Create ward password table
    ward_data = [['Ward Name', 'Password']]

    for ward_name in sorted(ward_passwords.keys()):
        ward_data.append([ward_name, ward_passwords[ward_name]])

    ward_table = Table(ward_data, colWidths=[3.5*inch, 2.5*inch])
    ward_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica'),
        ('FONTNAME', (1, 1), (1, -1), 'Courier-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))

    elements.append(ward_table)

    # Build PDF
    doc.build(elements)

    print(f"✓ PDF generated: {pdf_file}")
    print(f"  Total passwords: 1 master + {len(ward_passwords)} wards")


if __name__ == "__main__":
    print("Generating password distribution PDF...")
    create_password_pdf()
    print("\nDone!")
