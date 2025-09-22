import os
from datetime import timedelta


basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Your_Secret_key_here'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
   
    # Telegram configuration
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN') or 'Your_telegram_bot_token_here'
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID') or 'Your_telegram_chat_id_here'
   
    # Gemini API
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or 'Your_gemini_api_key_here'
   
    # Image storage
    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/images')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
   
    # RSS feeds
    RSS_FEEDS = [
        #list all rss_feeds of site you want scrape here
    ]
   
    EDUCATION_KEYWORDS = [
        #you can chnage these key words to key words of the content type you want eg politices, health, etc
        "education", "school", "student", "teacher", "university", "college",
        "classroom", "curriculum", "learning", "training", "scholarship",
        "academic", "exam", "lecturer", "institution"
    ]
