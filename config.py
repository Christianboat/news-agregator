import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'c4a2f8b9e7d3f1a5c6e9b2a8d7f3c1e4a9f6b2d7e3c8a1f5d9b4e7c2f6a8d3c9'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Telegram configuration
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN') or '7919647588:AAE21PYxU4bC08PmvfC_IFRU1p_FgpOkwG'
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID') or '+233552767800'
    
    # Gemini API
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or 'AIzaSyDpGTJ9FsbKdogPsUAOHdkZxDDRbrXdxfk'
    
    # Image storage
    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/images')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # RSS feeds
    RSS_FEEDS = [
        "https://www.myjoyonline.com/feed",
        "https://www.pulse.com.gh/rss",
        "https://www.ghanaweb.com/feed/",
        "https://citinewsroom.com/feed",
        "https://www.modernghana.com/rssfeed/news.xml",
        "https://www.adomonline.com/feed",
        "https://www.ghanaiantimes.com.gh/feed",
        "https://www.peacefmonline.com/pages/rss/",
        "https://www.ghheadlines.com/rss",
        "https://allafrica.com/tools/headlines/rdf/ghana/headlines.rdf"
    ]
    
    EDUCATION_KEYWORDS = [
        "education", "school", "student", "teacher", "university", "college",
        "classroom", "curriculum", "learning", "training", "scholarship",
        "academic", "exam", "lecturer", "institution"
    ]