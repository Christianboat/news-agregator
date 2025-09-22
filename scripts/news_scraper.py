import feedparser
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse
import hashlib
from PIL import Image, UnidentifiedImageError
from io import BytesIO
from config import Config
from app import db
from app.models import NewsItem, SocialMediaScript, UnifiedScript
import time
import shutil
import logging

# Additional imports for robust download
import uuid
import mimetypes
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from werkzeug.utils import secure_filename

# Set up logging
logger = logging.getLogger(__name__)

# --- Helper: clear old DB rows and images ---
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError

def clear_old_data(auto_create_missing_tables=False):
    """
    Safely delete SocialMediaScript, NewsItem, UnifiedScript rows and clear images.
    - If a table doesn't exist, skip it.
    - If auto_create_missing_tables=True, call db.create_all() to create missing tables (dev only).
    """
    inspector = inspect(db.engine)
    # Map model classes to expected table names (adjust if your models set __tablename__)
    table_map = {
        'social_media_script': SocialMediaScript,
        'news_item': NewsItem,
        'unified_script': UnifiedScript,
    }

    try:
        # Optionally create missing tables (useful for dev; NOT recommended in production)
        if auto_create_missing_tables:
            missing = []
            for tbl in table_map.keys():
                if tbl not in inspector.get_table_names():
                    missing.append(tbl)
            if missing:
                logger.info("Missing tables detected: %s. Creating tables (db.create_all())", missing)
                db.create_all()
                # refresh inspector after create_all
                inspector = inspect(db.engine)

        # Delete rows from each table only if it exists
        for tablename, model in table_map.items():
            try:
                if tablename in inspector.get_table_names():
                    logger.info("Deleting rows from table: %s", tablename)
                    db.session.query(model).delete()
                    db.session.commit()
                else:
                    logger.info("Table %s does not exist. Skipping delete.", tablename)
            except OperationalError as oe:
                db.session.rollback()
                logger.error("OperationalError while clearing %s: %s", tablename, oe)
            except Exception as e:
                db.session.rollback()
                logger.exception("Unexpected error when clearing table %s: %s", tablename, e)

        # Clear image directory
        upload_folder = getattr(Config, "UPLOAD_FOLDER", None)
        if upload_folder and os.path.exists(upload_folder):
            for filename in os.listdir(upload_folder):
                file_path = os.path.join(upload_folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    logger.error("Failed to delete %s. Reason: %s", file_path, e)
            logger.info("Successfully cleared image directory")

        return True

    except Exception as e:
        # Last-resort rollback and log
        try:
            db.session.rollback()
        except Exception:
            pass
        logger.exception("Error clearing old data (final): %s", e)
        return False


def fetch_news():
    news_items = []
    for feed_url in Config.RSS_FEEDS:
        try:
            parsed_feed = feedparser.parse(feed_url)
            for entry in parsed_feed.entries:
                news_items.append({
                    'title': getattr(entry, 'title', '') or '',
                    'link': getattr(entry, 'link', '') or '',
                    'published': getattr(entry, 'published', '') or '',
                    'summary': getattr(entry, 'summary', '') or ''
                })
            time.sleep(1)  # be polite
        except Exception as e:
            logger.error(f"Error parsing feed {feed_url}: {e}")
    return news_items

def filter_education(news_items):
    filtered = []
    for item in news_items:
        text = (item['title'] + " " + item['summary']).lower()
        if any(keyword in text for keyword in Config.EDUCATION_KEYWORDS):
            filtered.append(item)
    return filtered

def filter_this_week(news_items):
    today = datetime.utcnow().date()
    start_of_week = today - timedelta(days=today.weekday())
    return [
        item for item in news_items
        if item.get('published') and is_this_week(item['published'], start_of_week)
    ]

def is_this_week(pub_str, start_of_week):
    try:
        pub_date = date_parser.parse(pub_str).date()
        return pub_date >= start_of_week
    except Exception:
        return False

def get_latest(news_items, limit=10):
    def parse_date_safe(item):
        try:
            return date_parser.parse(item['published'])
        except:
            return datetime.min
    sorted_news = sorted(news_items, key=parse_date_safe, reverse=True)
    return sorted_news[:limit]

# ---------------------------
# Robust download_image helper
# ---------------------------

# map common image content-types to extensions
_CONTENT_TYPE_EXT = {
    'image/jpeg': '.jpg',
    'image/pjpeg': '.jpg',
    'image/png': '.png',
    'image/webp': '.webp',
    'image/gif': '.gif',
    'image/svg+xml': '.svg',
    'image/bmp': '.bmp',
}

def _make_session_with_retries(total_retries=3, backoff_factor=0.8, status_forcelist=(429, 502, 503, 504)):
    session = requests.Session()
    retry = Retry(
        total=total_retries,
        read=total_retries,
        connect=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=frozenset(['GET', 'HEAD'])
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    # user-agent fallback to Config if present
    ua = getattr(Config, "REQUEST_USER_AGENT", None) or "NewsScraper/1.0 (+https://your.domain)"
    session.headers.update({'User-Agent': ua})
    return session

def _ext_from_url(url):
    path = urlparse(url).path
    ext = os.path.splitext(path)[1].lower()
    return ext if ext else None

def _ext_from_content_type(content_type):
    if not content_type:
        return None
    content_type = content_type.split(';', 1)[0].strip().lower()
    return _CONTENT_TYPE_EXT.get(content_type) or mimetypes.guess_extension(content_type) or None

def download_image(article_url, image_url=None, upload_folder=None, session=None, max_size=5 * 1024 * 1024, timeout=(5, 20)):
    """
    Robust image downloader.
    - article_url: URL of the article page (used to resolve relative image urls)
    - image_url: optional direct image URL; if None we'll extract from article page
    - returns: filename (string) saved inside Config.UPLOAD_FOLDER, or None on failure
    """
    try:
        if session is None:
            session = _make_session_with_retries()

        # Prefer explicit upload_folder, else config
        if upload_folder is None:
            upload_folder = getattr(Config, 'UPLOAD_FOLDER', None) or os.path.join(os.getcwd(), 'static', 'images')

        os.makedirs(upload_folder, exist_ok=True)

        if not article_url:
            logger.debug("No article_url provided to download_image()")
            return None

        article_url = article_url.strip()

        # If caller provided a direct image_url, resolve it; else scrape the article page for an image
        resolved_image_url = None
        if image_url:
            resolved_image_url = urljoin(article_url, image_url.strip())
        else:
            # Try to fetch the article HTML and scrape for og:image or first reasonable <img>
            try:
                resp = session.get(article_url, timeout=timeout)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.content, 'html.parser')
                og_image = soup.find('meta', property='og:image')
                if og_image and og_image.get('content'):
                    resolved_image_url = og_image['content'].strip()
                else:
                    # pick first non-logo/icon image
                    images = soup.find_all('img')
                    for img in images:
                        src = img.get('src') or img.get('data-src') or ''
                        if src:
                            if ('logo' in src.lower()) or ('icon' in src.lower()):
                                continue
                            resolved_image_url = src.strip()
                            break
                    # if still nothing, leave resolved_image_url None
            except Exception as e:
                logger.warning("Failed to fetch article page for image scraping: %s. Error: %s", article_url, e)
                resolved_image_url = None

        if not resolved_image_url:
            logger.info("No candidate image found for article: %s", article_url)
            return None

        resolved_image_url = urljoin(article_url, resolved_image_url)

        # Try HEAD to get content-type/length (some servers block HEAD; it's okay if it fails)
        content_type = None
        content_length = None
        try:
            head = session.head(resolved_image_url, allow_redirects=True, timeout=timeout)
            if head.ok:
                content_type = head.headers.get('content-type')
                content_length = head.headers.get('content-length')
        except Exception:
            # ignore HEAD errors; we'll proceed with GET
            content_type = None
            content_length = None

        # Reject non-image content-types (if known)
        if content_type and not content_type.lower().startswith('image/'):
            logger.warning("Head indicates non-image content-type=%s for %s", content_type, resolved_image_url)
            return None

        # Determine extension preference: URL ext -> content-type -> fallback .jpg
        ext = _ext_from_url(resolved_image_url) or _ext_from_content_type(content_type) or '.jpg'

        # Prepare filenames
        unique_name = uuid.uuid4().hex
        filename = secure_filename(unique_name + ext)
        tmp_filename = filename + '.part'
        filepath_tmp = os.path.join(upload_folder, tmp_filename)
        filepath_final = os.path.join(upload_folder, filename)

        # If content-length present, check size
        if content_length:
            try:
                if int(content_length) > max_size:
                    logger.warning("Image content-length %s exceeds max_size %s for %s", content_length, max_size, resolved_image_url)
                    return None
            except ValueError:
                pass

        # Stream GET and write to temp file with size guard
        with session.get(resolved_image_url, stream=True, timeout=timeout) as r:
            r.raise_for_status()

            r_ct = r.headers.get('content-type')
            if r_ct and not r_ct.lower().startswith('image/'):
                logger.warning("Downloaded resource content-type=%s is not image for %s", r_ct, resolved_image_url)
                return None

            total = 0
            chunk_size = 8192
            with open(filepath_tmp, 'wb') as fh:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > max_size:
                        fh.close()
                        try:
                            os.remove(filepath_tmp)
                        except OSError:
                            pass
                        logger.warning("Download exceeded max_size during streaming (%d > %d): %s", total, max_size, resolved_image_url)
                        return None
                    fh.write(chunk)

        # Verify file is an image using Pillow
        try:
            with Image.open(filepath_tmp) as img:
                img.verify()
        except (UnidentifiedImageError, OSError) as e:
            try:
                os.remove(filepath_tmp)
            except OSError:
                pass
            logger.warning("Downloaded file is not a valid image (%s): %s", resolved_image_url, e)
            return None

        # Move .part to final filename
        try:
            os.replace(filepath_tmp, filepath_final)
        except OSError:
            try:
                os.rename(filepath_tmp, filepath_final)
            except OSError as e:
                logger.exception("Failed to move downloaded image to final path: %s", e)
                try:
                    os.remove(filepath_tmp)
                except OSError:
                    pass
                return None

        # Create thumbnail (safe open)
        try:
            with Image.open(filepath_final) as img:
                img.thumbnail((300, 300))
                thumb_name = f"thumb_{filename}"
                thumb_path = os.path.join(upload_folder, thumb_name)
                img.save(thumb_path)
        except Exception as e:
            logger.warning("Failed to create thumbnail for %s: %s", filepath_final, e)
            # don't fail pipeline for thumbnail problems

        logger.info("Saved image %s from %s", filename, resolved_image_url)
        return filename

    except Exception as exc:
        logger.exception("Unexpected error in download_image for %s: %s", article_url or image_url, exc)
        return None

# ---------------------------
# End of download_image helper
# ---------------------------

def generate_video_script(latest_edu_news):
    prompt = f"""
You are a professional Ghanaian news presenter creating a short,
high-energy script
for TikTok, Instagram Reels, and Facebook Reels.

Here are the latest education news headlines and summaries:
{format_news(latest_edu_news)} 

Write an engaging, human-sounding short video script that hooks viewers in
the first 3 seconds.
Use a friendly but confident tone, keep sentences short and punchy. Keep
it under 60 seconds.
"""
    try:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error generating video script (Gemini): {e}")
        # fallback: simple assembled script
        fallback = " | ".join([f"{i+1}. {n['title']}" for i, n in enumerate(latest_edu_news[:5])])
        return f"Auto fallback: This week: {fallback}"

def generate_unified_script(news_items):
    prompt = f"""
YYou are a creative scriptwriter for TikTok news. 
Write a short, human-sounding script about this week’s top education news in Ghana. 


Goals:
- Hook viewers in the first 3 seconds with a bold statement, surprising fact, or sharp question.
- Use a friendly, confident, and conversational tone (like Dylan Page on TikTok).
- Keep sentences short and punchy so the delivery feels fast and engaging. 
- For each story, give enough detail so viewers understand WHY it matters (include key people, places, or impact).
- Add Ghanaian cultural flavor where natural (expressions, references, or relatable examples).
- Use smooth transitions like “Meanwhile…” or “Here’s the twist…” to connect stories.
- End with a memorable closing question or call-to-action for comments. 

Rules:
- Keep the script under 60–75 seconds when read aloud.
- Focus on clarity and human impact, not robotic headline summaries.
- Avoid long numbers or exact dates unless absolutely essential.
- Write it like a TikTok creator speaking directly to their followers, not like a news anchor.

Stories:
{format_news(news_items)}
"""
    try:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error generating unified script (Gemini): {e}")
        # fallback
        fallback = " | ".join([f"{i+1}. {n['title']}" for i, n in enumerate(news_items[:7])])
        return f"Auto fallback unified: {fallback}"

def format_news(news_list):
    return "\n".join(
        f"- {item['title']} ({item['link']}) \n {item['summary']}"
        for item in news_list
    )

def run_news_pipeline():
    """
    Main pipeline. Runs under an app context.
    Returns: list of plain dicts
    """
    # Clear old data first
    if not clear_old_data():
        logger.error("Failed to clear old data. Aborting pipeline.")
        return []

    # ensure upload folder exists
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    all_news = fetch_news()
    this_week_news = filter_this_week(all_news)
    edu_news = filter_education(this_week_news)
    latest_edu_news = get_latest(edu_news, limit=10)
    
    if not latest_edu_news:
        logger.info("No education news found for this week.")
        return []

    # Generate scripts
    unified_script_content = generate_unified_script(latest_edu_news)
    individual_script_content = generate_video_script(latest_edu_news)

    # Save unified script to DB
    today = datetime.utcnow().date()
    week_start = today - timedelta(days=today.weekday())
    unified = UnifiedScript(
        content=unified_script_content,
        week_start=datetime.combine(week_start, datetime.min.time())
    )
    db.session.add(unified)
    db.session.commit()  # Commit early to avoid locking

    results = []
    for news_item in latest_edu_news:
        # Avoid duplicates by link
        if NewsItem.query.filter_by(link=news_item['link']).first():
            logger.info(f"Skipping duplicate: {news_item['title']}")
            continue

        image_filename = None
        try:
            # call new download_image with just the article URL (the helper will scrape the page)
            image_filename = download_image(news_item['link'])
        except Exception as e:
            logger.error(f"Image download failed for {news_item['link']}: {e}")

        # parse published
        try:
            published_date = date_parser.parse(news_item['published'])
        except Exception:
            published_date = datetime.utcnow()

        # create DB record
        item = NewsItem(
            title=news_item['title'], 
            link=news_item['link'], 
            summary=news_item['summary'], 
            published=published_date, 
            category='education', 
            image_path=image_filename
        )
        db.session.add(item)
        db.session.flush()  # get id

        # Attach (same) weekly script reference
        script = SocialMediaScript(
            content=individual_script_content, 
            news_item_id=item.id
        )
        db.session.add(script)

        results.append({
            "title": news_item['title'], 
            "summary": news_item['summary'], 
            "link": news_item['link'], 
            "image_path": image_filename, 
            "created_at": datetime.utcnow().isoformat(), 
            "script": unified_script_content
        })

    db.session.commit()
    return results

if __name__ == "__main__":  
    # run with app context if executed directly  
    from app import create_app  
    app = create_app()  
    with app.app_context():  
        run_news_pipeline()
