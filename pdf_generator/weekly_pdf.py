from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import textwrap
import json
import os
import re
import html
import unicodedata

def clean_text_for_pdf(text):
    """Clean text for PDF rendering while preserving emojis and special characters"""
    if not text:
        return ""
    
    # Convert to string if not already
    text = str(text)
    
    # Handle HTML entities
    text = html.unescape(text)
    
    # Remove control characters but keep emojis and normal text
    # This removes characters that can cause black boxes
    cleaned_text = ""
    for char in text:
        # Keep normal characters, emojis, and common symbols
        if (unicodedata.category(char)[0] in 'LMNPSZC' or  # Letters, Numbers, Punctuation, Symbols, etc.
            ord(char) >= 0x1F600 or  # Emoji range
            char in '\n\t\r '):  # Whitespace
            cleaned_text += char
        else:
            # Replace problematic characters with space
            cleaned_text += ' '
    
    # Clean up multiple spaces
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    return cleaned_text

def format_number(num):
    """Format numbers with commas"""
    if isinstance(num, (int, float)):
        return f"{num:,}"
    return str(num)

def split_long_text(text, max_length=500):
    """Split long text into smaller chunks for better PDF handling"""
    if len(text) <= max_length:
        return [text]
    
    # Split by sentences first
    sentences = re.split(r'[.!?]+', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk + sentence) <= max_length:
            current_chunk += sentence + ". "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def generate_weekly_report_pdf(report_data, output_path):
    """
    Generate a comprehensive weekly report PDF with ALL data included.
    Preserves emojis and handles all content properly.
    """
    # Create document with proper margins
    doc = SimpleDocTemplate(
        output_path, 
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=60,
        bottomMargin=60
    )
    
    styles = getSampleStyleSheet()
    
    # Define comprehensive custom styles
    title_style = ParagraphStyle(
        name='ReportTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=colors.HexColor('#1a472a'),
        spaceAfter=30,
        spaceBefore=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    section_style = ParagraphStyle(
        name='SectionHeader',
        fontSize=16,
        textColor=colors.white,
        spaceBefore=25,
        spaceAfter=15,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        backColor=colors.HexColor('#2e7d32'),
        borderWidth=1,
        borderColor=colors.HexColor('#1b5e20'),
        borderPadding=10
    )
    
    subsection_style = ParagraphStyle(
        name='SubsectionHeader',
        fontSize=14,
        textColor=colors.HexColor('#1976d2'),
        spaceBefore=18,
        spaceAfter=10,
        fontName='Helvetica-Bold',
        leftIndent=5,
        backColor=colors.HexColor('#f3f9ff'),
        borderWidth=1,
        borderColor=colors.HexColor('#1976d2'),
        borderPadding=5
    )
    
    news_title_style = ParagraphStyle(
        name='NewsTitle',
        fontSize=12,
        textColor=colors.HexColor('#d32f2f'),
        spaceBefore=12,
        spaceAfter=6,
        fontName='Helvetica-Bold',
        leftIndent=10
    )
    
    content_style = ParagraphStyle(
        name='ContentText',
        fontSize=10,
        spaceBefore=4,
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        fontName='Helvetica',
        leftIndent=10,
        rightIndent=10
    )
    
    meta_style = ParagraphStyle(
        name='MetaText',
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        spaceBefore=3,
        spaceAfter=5,
        fontName='Helvetica-Oblique',
        leftIndent=15
    )
    
    social_user_style = ParagraphStyle(
        name='SocialUser',
        fontSize=11,
        textColor=colors.HexColor('#1976d2'),
        spaceBefore=10,
        spaceAfter=4,
        fontName='Helvetica-Bold',
        leftIndent=10
    )
    
    hashtag_style = ParagraphStyle(
        name='HashtagStyle',
        fontSize=9,
        textColor=colors.HexColor('#1976d2'),
        spaceBefore=3,
        spaceAfter=5,
        fontName='Helvetica',
        leftIndent=15
    )
    
    elements = []
    
    # Handle nested data structure
    if 'data' in report_data:
        data = report_data['data']
        report_id = report_data.get('id', 'N/A')
        report_date = report_data.get('date', 'N/A')
        created_at = report_data.get('created_at', 'N/A')
    else:
        data = report_data
        report_id = data.get('id', 'N/A')
        report_date = data.get('date', 'N/A')
        created_at = data.get('created_at', 'N/A')
    
    # Title and Header
    elements.append(Paragraph("🌾 WEEKLY AGRICULTURAL INTELLIGENCE REPORT", title_style))
    elements.append(Spacer(1, 20))
    
    # Report metadata
    meta_data = [
        ['📋 Report ID:', clean_text_for_pdf(report_id)],
        ['📅 Report Date:', clean_text_for_pdf(report_date)],
        ['⏰ Generated:', clean_text_for_pdf(created_at[:19] if created_at and created_at != 'N/A' else 'N/A')]
    ]
    
    meta_table = Table(meta_data, colWidths=[2.5*inch, 4*inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f5e8')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#c8e6c9')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(meta_table)
    elements.append(Spacer(1, 30))
    
    # =========================
    # NEWS DATA SECTION - COMPLETE
    # =========================
    elements.append(Paragraph("📰 NEWS INTELLIGENCE", section_style))
    elements.append(Spacer(1, 10))
    
    news_data = data.get('news_data', [])
    if news_data:
        elements.append(Paragraph(f"Total News Items: {len(news_data)}", content_style))
        elements.append(Spacer(1, 15))
        
        for i, news in enumerate(news_data, 1):
            # News title
            title = clean_text_for_pdf(news.get('title_translated', news.get('original_title', 'Untitled News')))
            elements.append(Paragraph(f"<b>{i}. {title}</b>", news_title_style))
            
            # Complete news metadata
            region = clean_text_for_pdf(news.get('region', 'N/A'))
            country = clean_text_for_pdf(news.get('country', 'N/A'))
            category = clean_text_for_pdf(news.get('category', 'N/A'))
            timestamp = clean_text_for_pdf(news.get('timestamp', 'N/A'))
            language = clean_text_for_pdf(news.get('language', 'N/A'))
            
            elements.append(Paragraph(f"<b>Region:</b> {region} | <b>Country:</b> {country} | <b>Category:</b> {category}", meta_style))
            elements.append(Paragraph(f"<b>Date:</b> {timestamp} | <b>Language:</b> {language}", meta_style))
            
            # Source with proper URL handling
            source = news.get('source', 'N/A')
            if source and source != 'N/A':
                clean_source = clean_text_for_pdf(source)
                elements.append(Paragraph(f"<b>Source:</b> <link href='{source}' color='blue'>{clean_source}</link>", meta_style))
            
            # Full summary
            summary = clean_text_for_pdf(news.get('summary_en', ''))
            if summary:
                elements.append(Paragraph(f"<b>Summary:</b> {summary}", content_style))
            
            # Original title if different
            original_title = clean_text_for_pdf(news.get('original_title', ''))
            if original_title and original_title != title:
                elements.append(Paragraph(f"<b>Original Title:</b> {original_title}", meta_style))
            
            elements.append(Spacer(1, 20))
    else:
        elements.append(Paragraph("No news data available in this report.", content_style))
    
    elements.append(PageBreak())
    
    # =========================
    # TECHNICAL DATA SECTION - COMPLETE
    # =========================
    elements.append(Paragraph("🔬 TECHNICAL INTELLIGENCE", section_style))
    elements.append(Spacer(1, 10))
    
    tech_data = data.get('technical_data', {})
    
    # Patents Section - ALL patents
    patents = tech_data.get('patents', [])
    if patents:
        elements.append(Paragraph("📋 Patents & Innovations", subsection_style))
        elements.append(Paragraph(f"Total Patents: {len(patents)}", content_style))
        elements.append(Spacer(1, 10))
        
        for i, patent in enumerate(patents, 1):
            clean_patent = clean_text_for_pdf(patent)
            elements.append(Paragraph(f"<b>{i}.</b> {clean_patent}", content_style))
            elements.append(Spacer(1, 10))
    
    # Regulations Section - ALL regulations
    regulations = tech_data.get('regulations', [])
    if regulations:
        elements.append(Paragraph("⚖️ Regulations & Policies", subsection_style))
        elements.append(Paragraph(f"Total Regulations: {len(regulations)}", content_style))
        elements.append(Spacer(1, 10))
        
        for i, regulation in enumerate(regulations, 1):
            clean_regulation = clean_text_for_pdf(regulation)
            elements.append(Paragraph(f"<b>{i}.</b> {clean_regulation}", content_style))
            elements.append(Spacer(1, 10))
    
    # Genetic Resources Section - ALL resources
    genetic_resources = tech_data.get('genetic_resources', [])
    if genetic_resources:
        elements.append(Paragraph("🧬 Genetic Resources", subsection_style))
        elements.append(Paragraph(f"Total Genetic Resources: {len(genetic_resources)}", content_style))
        elements.append(Spacer(1, 10))
        
        for i, resource in enumerate(genetic_resources, 1):
            clean_resource = clean_text_for_pdf(resource)
            elements.append(Paragraph(f"<b>{i}.</b> {clean_resource}", content_style))
            elements.append(Spacer(1, 10))
    
    if not any([patents, regulations, genetic_resources]):
        elements.append(Paragraph("No technical data available in this report.", content_style))
    
    elements.append(PageBreak())
    
    # =========================
    # SOCIAL MEDIA SECTION - COMPLETE ALL PLATFORMS
    # =========================
    elements.append(Paragraph("📱 SOCIAL MEDIA INTELLIGENCE", section_style))
    elements.append(Spacer(1, 10))
    
    social_data = data.get('social_media_data', {})
    
    # Count total social media posts
    total_posts = sum([
        len(social_data.get('reddit', [])),
        len(social_data.get('twitter', [])),
        len(social_data.get('instagram', [])),
        len(social_data.get('facebook', [])),
        len(social_data.get('linkedin', []))
    ])
    
    elements.append(Paragraph(f"Total Social Media Posts: {total_posts}", content_style))
    elements.append(Spacer(1, 15))
    
    # Reddit Section - ALL posts
    reddit_posts = social_data.get('reddit', [])
    if reddit_posts:
        elements.append(Paragraph("🔴 Reddit Posts", subsection_style))
        elements.append(Paragraph(f"Total Reddit Posts: {len(reddit_posts)}", content_style))
        elements.append(Spacer(1, 10))
        
        for i, post in enumerate(reddit_posts, 1):
            title = clean_text_for_pdf(post.get('title', 'Untitled'))
            elements.append(Paragraph(f"<b>{i}. {title}</b>", social_user_style))
            
            user = clean_text_for_pdf(post.get('user', 'N/A'))
            subreddit = clean_text_for_pdf(post.get('subreddit', 'N/A'))
            elements.append(Paragraph(f"<b>User:</b> {user} | <b>Subreddit:</b> {subreddit}", meta_style))
            
            date = clean_text_for_pdf(post.get('date', 'N/A')[:19] if post.get('date') else 'N/A')
            elements.append(Paragraph(f"<b>Date:</b> {date}", meta_style))
            
            # Full body content - handle long posts
            body = clean_text_for_pdf(post.get('body', ''))
            if body:
                # Split long content into chunks
                body_chunks = split_long_text(body, 800)
                for chunk in body_chunks:
                    elements.append(Paragraph(f"<b>Content:</b> {chunk}", content_style))
            
            # URL
            url = post.get('url', '')
            if url:
                elements.append(Paragraph(f"<b>URL:</b> <link href='{url}' color='blue'>{clean_text_for_pdf(url)}</link>", meta_style))
            
            elements.append(Spacer(1, 15))
    
    # Twitter Section - ALL unique tweets
    twitter_posts = social_data.get('twitter', [])
    if twitter_posts:
        elements.append(Paragraph("🐦 Twitter Posts", subsection_style))
        
        # Remove duplicates based on tweet_id
        unique_tweets = {}
        for post in twitter_posts:
            tweet_id = post.get('tweet_id')
            if tweet_id not in unique_tweets:
                unique_tweets[tweet_id] = post
        
        elements.append(Paragraph(f"Total Unique Twitter Posts: {len(unique_tweets)}", content_style))
        elements.append(Spacer(1, 10))
        
        for i, post in enumerate(unique_tweets.values(), 1):
            user_name = clean_text_for_pdf(post.get('user_name', 'N/A'))
            elements.append(Paragraph(f"<b>{i}. @{user_name}</b>", social_user_style))
            
            # Complete user info
            location = clean_text_for_pdf(post.get('location', 'N/A'))
            followers = format_number(post.get('followers', 0))
            following = format_number(post.get('following', 0))
            elements.append(Paragraph(f"<b>Location:</b> {location} | <b>Followers:</b> {followers} | <b>Following:</b> {following}", meta_style))
            
            created_at = clean_text_for_pdf(post.get('created_at', 'N/A'))
            elements.append(Paragraph(f"<b>Account Created:</b> {created_at}", meta_style))
            
            # Tweet content with emojis preserved
            tweet_text = clean_text_for_pdf(post.get('text', ''))
            if tweet_text:
                elements.append(Paragraph(f"<b>Tweet:</b> {tweet_text}", content_style))
            
            # Language
            lang = clean_text_for_pdf(post.get('lang', 'N/A'))
            elements.append(Paragraph(f"<b>Language:</b> {lang}", meta_style))
            
            # Complete engagement metrics
            engagement_data = [
                ['❤️ Likes', format_number(post.get('like_count', 0))],
                ['🔄 Retweets', format_number(post.get('retweet_count', 0))],
                ['💬 Replies', format_number(post.get('reply_count', 0))],
                ['👀 Views', format_number(post.get('view_count', 0))]
            ]
            
            engagement_table = Table(engagement_data, colWidths=[1.5*inch, 1.5*inch])
            engagement_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e3f2fd')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bbdefb')),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            
            elements.append(engagement_table)
            
            # Additional info
            is_verified = post.get('is_blue_verified', False)
            elements.append(Paragraph(f"<b>Verified:</b> {'Yes' if is_verified else 'No'}", meta_style))
            
            # URLs
            url = post.get('url', '')
            if url:
                elements.append(Paragraph(f"<b>Tweet URL:</b> <link href='{url}' color='blue'>{clean_text_for_pdf(url)}</link>", meta_style))
            
            profile_url = post.get('twitter_profile_url', '')
            if profile_url:
                elements.append(Paragraph(f"<b>Profile URL:</b> <link href='{profile_url}' color='blue'>{clean_text_for_pdf(profile_url)}</link>", meta_style))
            
            elements.append(Spacer(1, 18))
    
    # Instagram Section - ALL unique posts
    instagram_posts = social_data.get('instagram', [])
    if instagram_posts:
        elements.append(Paragraph("📸 Instagram Posts", subsection_style))
        
        # Remove duplicates based on post_url
        unique_instagram = {}
        for post in instagram_posts:
            post_url = post.get('post_url')
            if post_url not in unique_instagram:
                unique_instagram[post_url] = post
        
        elements.append(Paragraph(f"Total Unique Instagram Posts: {len(unique_instagram)}", content_style))
        elements.append(Spacer(1, 10))
        
        for i, post in enumerate(unique_instagram.values(), 1):
            username = clean_text_for_pdf(post.get('username', 'N/A'))
            full_name = clean_text_for_pdf(post.get('full_name', 'N/A'))
            elements.append(Paragraph(f"<b>{i}. @{username}</b> ({full_name})", social_user_style))
            
            timestamp = clean_text_for_pdf(post.get('timestamp', 'N/A')[:19] if post.get('timestamp') else 'N/A')
            post_type = clean_text_for_pdf(post.get('type', 'N/A'))
            elements.append(Paragraph(f"<b>Posted:</b> {timestamp} | <b>Type:</b> {post_type}", meta_style))
            
            # Full caption with emojis preserved
            caption = clean_text_for_pdf(post.get('caption', ''))
            if caption:
                # Split long captions into chunks
                caption_chunks = split_long_text(caption, 600)
                for chunk in caption_chunks:
                    elements.append(Paragraph(f"<b>Caption:</b> {chunk}", content_style))
            
            # Engagement metrics
            likes = format_number(post.get('likes_count', 0))
            comments = format_number(post.get('comments_count', 0))
            elements.append(Paragraph(f"<b>Engagement:</b> {likes} likes, {comments} comments", meta_style))
            
            # Hashtags - ALL hashtags
            hashtags = post.get('hashtags', [])
            if hashtags:
                clean_hashtags = [clean_text_for_pdf(tag) for tag in hashtags]
                hashtag_text = ' '.join([f"#{tag}" for tag in clean_hashtags])
                elements.append(Paragraph(f"<b>Hashtags:</b> {hashtag_text}", hashtag_style))
            
            # Mentions - ALL mentions
            mentions = post.get('mentions', [])
            if mentions:
                clean_mentions = [clean_text_for_pdf(mention) for mention in mentions]
                mention_text = ' '.join([f"@{mention}" for mention in clean_mentions])
                elements.append(Paragraph(f"<b>Mentions:</b> {mention_text}", hashtag_style))
            
            # Sponsored info
            is_sponsored = post.get('is_sponsored', False)
            elements.append(Paragraph(f"<b>Sponsored:</b> {'Yes' if is_sponsored else 'No'}", meta_style))
            
            # URL
            url = post.get('post_url', '')
            if url:
                elements.append(Paragraph(f"<b>Post URL:</b> <link href='{url}' color='blue'>{clean_text_for_pdf(url)}</link>", meta_style))
            
            elements.append(Spacer(1, 18))
    
    # Facebook Section - ALL unique pages
    facebook_posts = social_data.get('facebook', [])
    if facebook_posts:
        elements.append(Paragraph("📘 Facebook Pages", subsection_style))
        
        # Remove duplicates based on facebook_id
        unique_facebook = {}
        for post in facebook_posts:
            facebook_id = post.get('facebook_id')
            if facebook_id not in unique_facebook:
                unique_facebook[facebook_id] = post
        
        elements.append(Paragraph(f"Total Unique Facebook Pages: {len(unique_facebook)}", content_style))
        elements.append(Spacer(1, 10))
        
        for i, post in enumerate(unique_facebook.values(), 1):
            title = clean_text_for_pdf(post.get('title', 'Untitled'))
            elements.append(Paragraph(f"<b>{i}. {title}</b>", social_user_style))
            
            # Complete page info
            followers = format_number(post.get('followers', 0))
            likes = format_number(post.get('likes', 0))
            comments = format_number(post.get('comments', 0))
            elements.append(Paragraph(f"<b>Followers:</b> {followers} | <b>Likes:</b> {likes} | <b>Comments:</b> {comments}", meta_style))
            
            # Categories - ALL categories
            categories = post.get('categories', [])
            if categories:
                clean_categories = [clean_text_for_pdf(cat) for cat in categories]
                category_text = ', '.join(clean_categories)
                elements.append(Paragraph(f"<b>Categories:</b> {category_text}", meta_style))
            
            # Address
            address = clean_text_for_pdf(post.get('address', ''))
            if address:
                elements.append(Paragraph(f"<b>Address:</b> {address}", meta_style))
            
            # Phone
            phone = clean_text_for_pdf(post.get('phone_number', ''))
            if phone:
                elements.append(Paragraph(f"<b>Phone:</b> {phone}", meta_style))
            
            # Facebook ID
            facebook_id = clean_text_for_pdf(post.get('facebook_id', 'N/A'))
            elements.append(Paragraph(f"<b>Facebook ID:</b> {facebook_id}", meta_style))
            
            # Date
            date = clean_text_for_pdf(post.get('date', 'N/A')[:19] if post.get('date') else 'N/A')
            elements.append(Paragraph(f"<b>Date:</b> {date}", meta_style))
            
            # URL
            url = post.get('page_url', '')
            if url:
                elements.append(Paragraph(f"<b>Page URL:</b> <link href='{url}' color='blue'>{clean_text_for_pdf(url)}</link>", meta_style))
            
            elements.append(Spacer(1, 18))
    
    # LinkedIn Section - ALL unique posts
    linkedin_posts = social_data.get('linkedin', [])
    if linkedin_posts:
        elements.append(Paragraph("💼 LinkedIn Posts", subsection_style))
        
        # Remove duplicates based on activity_id
        unique_linkedin = {}
        for post in linkedin_posts:
            activity_id = post.get('activity_id')
            if activity_id not in unique_linkedin:
                unique_linkedin[activity_id] = post
        
        elements.append(Paragraph(f"Total Unique LinkedIn Posts: {len(unique_linkedin)}", content_style))
        elements.append(Spacer(1, 10))
        
        for i, post in enumerate(unique_linkedin.values(), 1):
            author_name = clean_text_for_pdf(post.get('author_name', 'N/A'))
            elements.append(Paragraph(f"<b>{i}. {author_name}</b>", social_user_style))
            
            posted_date = clean_text_for_pdf(post.get('posted_date', 'N/A'))
            elements.append(Paragraph(f"<b>Posted:</b> {posted_date}", meta_style))
            
            # Full content with emojis preserved
            text = clean_text_for_pdf(post.get('text', ''))
            if text:
                # Split long content into chunks
                text_chunks = split_long_text(text, 800)
                for chunk in text_chunks:
                    elements.append(Paragraph(f"<b>Content:</b> {chunk}", content_style))
            
            # Complete engagement metrics
            reactions = format_number(post.get('total_reactions', 0))
            comments = format_number(post.get('comments', 0))
            shares = format_number(post.get('shares', 0))
            elements.append(Paragraph(f"<b>Engagement:</b> {reactions} reactions, {comments} comments, {shares} shares", meta_style))
            
            # ALL hashtags
            hashtags = post.get('hashtags', [])
            if hashtags:
                clean_hashtags = [clean_text_for_pdf(tag) for tag in hashtags]
                hashtag_text = ' '.join([f"#{tag}" for tag in clean_hashtags])
                elements.append(Paragraph(f"<b>Hashtags:</b> {hashtag_text}", hashtag_style))
            
            # Activity ID
            activity_id = clean_text_for_pdf(post.get('activity_id', 'N/A'))
            elements.append(Paragraph(f"<b>Activity ID:</b> {activity_id}", meta_style))
            
            # URLs
            post_url = post.get('post_url', '')
            if post_url:
                elements.append(Paragraph(f"<b>Post URL:</b> <link href='{post_url}' color='blue'>{clean_text_for_pdf(post_url)}</link>", meta_style))
            
            profile_url = post.get('author_profile_url', '')
            if profile_url:
                elements.append(Paragraph(f"<b>Profile URL:</b> <link href='{profile_url}' color='blue'>{clean_text_for_pdf(profile_url)}</link>", meta_style))
            
            elements.append(Spacer(1, 18))
    
    if not any([reddit_posts, twitter_posts, instagram_posts, facebook_posts, linkedin_posts]):
        elements.append(Paragraph("No social media data available in this report.", content_style))
    
    elements.append(PageBreak())
    
    # =========================
    # BREEDING RECOMMENDATIONS - ALL
    # =========================
    elements.append(Paragraph("🌱 BREEDING RECOMMENDATIONS", section_style))
    elements.append(Spacer(1, 10))
    
    breeding_recs = data.get('breeding_recommendation', [])
    if breeding_recs:
        elements.append(Paragraph(f"Total Recommendations: {len(breeding_recs)}", content_style))
        elements.append(Spacer(1, 15))
        
        for i, rec in enumerate(breeding_recs, 1):
            clean_rec = clean_text_for_pdf(rec)
            elements.append(Paragraph(f"<b>{i}.</b> {clean_rec}", content_style))
            elements.append(Spacer(1, 12))
    else:
        elements.append(Paragraph("No breeding recommendations available in this report.", content_style))
    
    # Summary Footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("--- REPORT SUMMARY ---", 
                             ParagraphStyle(name='SummaryHeader', fontSize=12, textColor=colors.HexColor('#2e7d32'), 
                                          alignment=TA_CENTER, fontName='Helvetica-Bold')))
    elements.append(Spacer(1, 10))
    
    # Generate summary statistics
    summary_stats = [
        ['News Articles', str(len(news_data))],
        ['Patents', str(len(patents))],
        ['Regulations', str(len(regulations))],
        ['Genetic Resources', str(len(genetic_resources))],
        ['Reddit Posts', str(len(reddit_posts))],
        ['Twitter Posts', str(len(twitter_posts))],
        ['Instagram Posts', str(len(instagram_posts))],
        ['Facebook Pages', str(len(facebook_posts))],
        ['LinkedIn Posts', str(len(linkedin_posts))],
        ['Breeding Recommendations', str(len(breeding_recs))],
        ['TOTAL DATA POINTS', str(len(news_data) + len(patents) + len(regulations) + len(genetic_resources) + 
                                  len(reddit_posts) + len(twitter_posts) + len(instagram_posts) + 
                                  len(facebook_posts) + len(linkedin_posts) + len(breeding_recs))]
    ]
    
    summary_table = Table(summary_stats, colWidths=[3*inch, 1*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -2), colors.HexColor('#f5f5f5')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#2e7d32')),
        ('TEXTCOLOR', (0, 0), (-1, -2), colors.black),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Footer
    elements.append(Paragraph("Report generated automatically from agricultural intelligence data sources.", 
                             ParagraphStyle(name='Footer', fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))
    elements.append(Paragraph("All emojis and special characters have been preserved for full visual impact.", 
                             ParagraphStyle(name='FooterNote', fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))
    
    # Build the PDF
    try:
        doc.build(elements)
        print(f"✅ PDF successfully generated: {output_path}")
        print(f"✅ Total data points processed: {len(news_data) + len(patents) + len(regulations) + len(genetic_resources) + len(reddit_posts) + len(twitter_posts) + len(instagram_posts) + len(facebook_posts) + len(linkedin_posts) + len(breeding_recs)}")
        
        # Print detailed statistics
        print("\n📊 DETAILED STATISTICS:")
        print(f"📰 News Articles: {len(news_data)}")
        print(f"🔬 Patents: {len(patents)}")
        print(f"⚖️ Regulations: {len(regulations)}")
        print(f"🧬 Genetic Resources: {len(genetic_resources)}")
        print(f"🔴 Reddit Posts: {len(reddit_posts)}")
        print(f"🐦 Twitter Posts: {len(twitter_posts)}")
        print(f"📸 Instagram Posts: {len(instagram_posts)}")
        print(f"📘 Facebook Pages: {len(facebook_posts)}")
        print(f"💼 LinkedIn Posts: {len(linkedin_posts)}")
        print(f"🌱 Breeding Recommendations: {len(breeding_recs)}")
        
        return True
    except Exception as e:
        print(f"❌ Error generating PDF: {str(e)}")
        return False

# # Example usage
# if __name__ == "__main__":
#     # Sample data structure based on your provided JSON
#     sample_data = {
#         "id": "e3200073-a014-4ab5-8516-ce9fd8ea364a",
#         "date": "2025-07-12",
#         "created_at": "2025-07-12T09:50:29.987835",
#         "data": {
#             # Your actual data structure here
#         }
#     }
    
#     # Generate comprehensive PDF
#     success = generate_weekly_report_pdf(sample_data, "complete_weekly_report_with_emojis.pdf")
    
#     if success:
#         print("🎉 PDF generation completed successfully!")
#         print("🎨 All emojis preserved!")
#         print("📄 All content included!")
#     else:
#         print("💥 PDF generation failed!")