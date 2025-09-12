from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from scripts.news_scraper import run_news_pipeline
from scripts.telegram_bot import send_weekly_digest
from app import create_app
from app.models import NewsItem, SocialMediaScript
from datetime import datetime, timedelta

def scheduled_job():
    print("Running weekly news aggregation...")
    app = create_app()
    with app.app_context():
        # Run the news pipeline
        news_items_with_scripts = run_news_pipeline()
        
        # Send via Telegram
        send_weekly_digest(news_items_with_scripts)
        
        print("Weekly news aggregation completed!")

def init_scheduler():
    scheduler = BackgroundScheduler()
    # Run every Thursday at 6 PM
    trigger = CronTrigger(day_of_week='thu', hour=18, minute=0)
    scheduler.add_job(scheduled_job, trigger)
    scheduler.start()
    print("Scheduler started. Will run every Thursday at 6 PM.")

if __name__ == "__main__":
    init_scheduler()
    # Keep the script running
    try:
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        pass