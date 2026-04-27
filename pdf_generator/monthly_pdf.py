from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
import os


def generate_monthly_report_pdf(report_data, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph(f"Monthly Report ID: {report_data.get('id', '')}", styles['Title']))
    elements.append(Paragraph(f"Date: {report_data.get('date', '')}", styles['Normal']))
    elements.append(Paragraph(f"Created At: {report_data.get('created_at', '')}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # News Data
    elements.append(Paragraph("<b>News Data</b>", styles['Heading2']))
    news_data = report_data.get('news_data', [])
    for i, news in enumerate(news_data, 1):
        elements.append(Paragraph(f"<b>{i}. {news.get('title_translated', news.get('original_title', ''))}</b>", styles['Heading4']))
        for key, value in news.items():
            if key not in ['title_translated', 'original_title']:
                elements.append(Paragraph(f"<b>{key.replace('_', ' ').capitalize()}:</b> {value}", styles['Normal']))
        elements.append(Spacer(1, 6))
    elements.append(Spacer(1, 12))

    # Technical Data
    elements.append(Paragraph("<b>Technical Data</b>", styles['Heading2']))
    tech = report_data.get('technical_data', {})
    for section in ['patents', 'regulations', 'genetic_resources']:
        items = tech.get(section, [])
        if items:
            elements.append(Paragraph(f"<b>{section.replace('_', ' ').capitalize()}:</b>", styles['Heading4']))
            for i, item in enumerate(items, 1):
                elements.append(Paragraph(f"{i}. {item}", styles['Normal']))
            elements.append(Spacer(1, 6))
    elements.append(Spacer(1, 12))

    # Social Media Data
    elements.append(Paragraph("<b>Social Media Data</b>", styles['Heading2']))
    sm = report_data.get('social_media_data', {})
    for platform, posts in sm.items():
        if posts:
            elements.append(Paragraph(f"<b>{platform.capitalize()}:</b>", styles['Heading4']))
            for i, post in enumerate(posts, 1):
                if isinstance(post, dict):
                    elements.append(Paragraph(f"{i}. {post.get('title', post.get('text', post.get('caption', '')))}", styles['Normal']))
                else:
                    elements.append(Paragraph(f"{i}. {post}", styles['Normal']))
            elements.append(Spacer(1, 6))
    elements.append(Spacer(1, 12))

    # Breeding Recommendations
    elements.append(Paragraph("<b>Breeding Recommendations</b>", styles['Heading2']))
    recs = report_data.get('breeding_recommendation', [])
    for i, rec in enumerate(recs, 1):
        elements.append(Paragraph(f"{i}. {rec}", styles['Normal']))
    elements.append(Spacer(1, 12))

    doc.build(elements) 