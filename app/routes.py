from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from app.models import User, NewsItem, SocialMediaScript, UnifiedScript
from datetime import datetime, timedelta
import threading
import logging

# Import your custom scripts
from scripts.news_scraper import run_news_pipeline
from scripts.telegram_bot import send_weekly_digest

# Define the blueprint
bp = Blueprint('routes', __name__)

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    # start of this week (UTC) as a datetime at 00:00
    today = datetime.utcnow().date()
    week_start_date = today - timedelta(days=today.weekday())
    week_start_dt = datetime.combine(week_start_date, datetime.min.time())

    news_items = NewsItem.query.filter(
        NewsItem.created_at >= week_start_dt
    ).order_by(NewsItem.created_at.desc()).all()

    unified_script = UnifiedScript.query.filter(
        UnifiedScript.week_start >= week_start_dt
    ).order_by(UnifiedScript.created_at.desc()).first()

    return render_template('index.html', title='Home',
                           news_items=news_items, unified_script=unified_script)

@bp.route('/dashboard')
@login_required
def dashboard():
    four_weeks_ago_dt = datetime.utcnow() - timedelta(weeks=4)
    news_items = NewsItem.query.filter(
        NewsItem.created_at >= four_weeks_ago_dt
    ).order_by(NewsItem.created_at.desc()).all()

    weekly_news = {}
    for item in news_items:
        week = item.created_at.isocalendar()[1]
        weekly_news.setdefault(week, []).append(item)

    return render_template('dashboard.html', title='Dashboard', weekly_news=weekly_news)
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('Invalid username or password')
            return redirect(url_for('routes.login'))
        
        login_user(user)
        return redirect(url_for('routes.index'))
    
    return render_template('login.html', title='Sign In')

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('routes.login'))

@bp.route('/trigger-news', methods=['POST'])
@login_required
def trigger_news():
    """Starts the news pipeline in a background daemon thread."""
    # Get the application instance
    app = current_app._get_current_object()
    
    def run_pipeline():
        # Create a new application context for the thread
        with app.app_context():
            try:
                current_app.logger.info("Starting news pipeline in background thread")
                news_dicts = run_news_pipeline()
                if news_dicts:
                    current_app.logger.info(f"Pipeline completed, found {len(news_dicts)} news items")
                    send_weekly_digest(news_dicts)
                else:
                    current_app.logger.info("Pipeline completed but no news items found")
            except Exception as e:
                current_app.logger.error(f"Error in news pipeline: {str(e)}")

    thread = threading.Thread(target=run_pipeline)
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'success', 'message': 'News retrieval started in the background. All old content has been cleared.'})
@bp.route('/api/status')
@login_required
def api_status():
    today = datetime.utcnow().date()
    week_start_date = today - timedelta(days=today.weekday())
    week_start_dt = datetime.combine(week_start_date, datetime.min.time())

    news_count = NewsItem.query.filter(
        NewsItem.created_at >= week_start_dt
    ).count()

    has_unified_script = UnifiedScript.query.filter(
        UnifiedScript.week_start >= week_start_dt
    ).first() is not None

    return jsonify({
        'news_count': news_count,
        'has_unified_script': has_unified_script
    })
