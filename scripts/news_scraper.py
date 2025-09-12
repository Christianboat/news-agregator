import feedparser
from datetime import datetime
from dateutil import parser as date_parser
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse
import hashlib
from PIL import Image
from io import BytesIO
from config import Config
from app import create_app, db
from app.models import NewsItem, SocialMediaScript
import time

def fetch_news():
    news_items = []
    for feed_url in Config.RSS_FEEDS:
        try:
            parsed_feed = feedparser.parse(feed_url)
            for entry in parsed_feed.entries:
                news_items.append({
                    'title': entry.title,
                    'link': entry.link,
                    'published': entry.published if 'published' in entry else 'No date available',
                    'summary': entry.summary if 'summary' in entry else 'No summary available'
                })
            time.sleep(1)  # Be polite to servers
        except Exception as e:
            print(f"Error parsing feed {feed_url}: {e}")
    return news_items

def filter_education(news_items):
    filtered = []
    for item in news_items:
        text = (item['title'] + " " + item['summary']).lower()
        if any(keyword in text for keyword in Config.EDUCATION_KEYWORDS):
            filtered.append(item)
    return filtered

def filter_this_week(news_items):
    today = datetime.now().date()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    return [
        item for item in news_items
        if 'published' in item and is_this_week(item['published'], start_of_week)
    ]

def is_this_week(pub_str, start_of_week):
    try:
        pub_date = date_parser.parse(pub_str).date()
        return pub_date >= start_of_week
    except Exception:
        return False

def get_latest(news_items, limit=5):
    def parse_date_safe(item):
        try:
            return date_parser.parse(item['published'])
        except:
            return datetime.min
    sorted_news = sorted(news_items, key=parse_date_safe, reverse=True)
    return sorted_news[:limit]

def download_image(url, article_url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Parse the article page to find the main image
        response = requests.get(article_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for Open Graph image first
        image_url = None
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            image_url = og_image['content']
        else:
            # Look for the first large image in the content
            images = soup.find_all('img')
            for img in images:
                src = img.get('src')
                if src and ('logo' not in src.lower() and 'icon' not in src.lower()):
                    image_url = src
                    break
        
        if not image_url:
            return None
            
        # Make absolute URL
        image_url = urljoin(article_url, image_url)
        
        # Download the image
        img_response = requests.get(image_url, headers=headers, timeout=10)
        img_response.raise_for_status()
        
        # Generate a unique filename
        file_ext = os.path.splitext(urlparse(image_url).path)[1]
        if not file_ext:
            file_ext = '.jpg'
        
        filename = hashlib.md5(image_url.encode()).hexdigest() + file_ext
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        # Save the image
        with open(filepath, 'wb') as f:
            f.write(img_response.content)
        
        # Create thumbnail
        img = Image.open(BytesIO(img_response.content))
        img.thumbnail((300, 300))
        thumb_filename = f"thumb_{filename}"
        thumb_filepath = os.path.join(Config.UPLOAD_FOLDER, thumb_filename)
        img.save(thumb_filepath)
        
        return filename
        
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")
        return None

def generate_video_script(latest_edu_news):
    prompt = f"""
You are a professional Ghanaian news presenter creating a short, high-energy script 
for TikTok, Instagram Reels, and Facebook Reels.

Here are the latest education news headlines and summaries:
{format_news(latest_edu_news)}

Write an engaging, human-sounding short video script that hooks viewers in the first 3 seconds. 
Use a friendly but confident tone, like a social media news creator speaking directly to the audience. 
Keep sentences short and punchy for fast delivery. 

Structure:
1. **Attention-grabbing intro** – start with a shocking fact, a question, or a bold statement.
2. **Story delivery** – tell each news story with vivid language, a conversational flow, 
   and smooth transitions. Use emotion and curiosity to keep people watching.
3. **Quick transitions** – use phrases like “But that’s not all…” or “Meanwhile…” 
   to keep the energy high.
4. **Closing hook** – end with a short, memorable line or question to spark engagement in the comments.

Rules:
- Keep it under 60 seconds total.
- No robotic reading — make it feel like a real person talking to friends online.
- Avoid long numbers and dates unless they are critical to the story.
- Keep the focus on the human impact and why viewers should care.
"""

    genai.configure(api_key=Config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text

def format_news(news_list):
    return "\n".join(
        f"- {item['title']} ({item['link']})\n  {item['summary']}"
        for item in news_list
    )

def run_news_pipeline():
    app = create_app()
    with app.app_context():
        # Create upload directory if it doesn't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        # Fetch and process news
        all_news = fetch_news()
        this_week_news = filter_this_week(all_news)
        edu_news = filter_education(this_week_news)
        latest_edu_news = get_latest(edu_news, limit=10)
        
        scripts = []
        
        if latest_edu_news:
            # Generate script
            script_content = generate_video_script(latest_edu_news)
            
            # Save news items and scripts to database
            for news_item in latest_edu_news:
                # Download image
                image_path = download_image(news_item['link'], news_item['link'])
                
                # Parse publication date
                try:
                    published_date = date_parser.parse(news_item['published'])
                except:
                    published_date = datetime.utcnow()
                
                # Save to database
                item = NewsItem(
                    title=news_item['title'],
                    link=news_item['link'],
                    summary=news_item['summary'],
                    published=published_date,
                    category='education',
                    image_path=image_path
                )
                db.session.add(item)
                db.session.flush()  # To get the ID
                
                # Create script for this news item
                script = SocialMediaScript(
                    content=script_content,
                    news_item_id=item.id
                )
                db.session.add(script)
                scripts.append((item, script_content))
            
            db.session.commit()
            
            return scripts
        else:
            print("No education news found for this week.")
            return []

if __name__ == "__main__":
    run_news_pipeline()