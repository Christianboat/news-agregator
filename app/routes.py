from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from app.models import User, NewsItem, SocialMediaScript
from datetime import datetime, timedelta
import os

# ✅ Define the blueprint here instead of importing it
bp = Blueprint('routes', __name__)

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    # Get this week's news
    week_start = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
    news_items = NewsItem.query.filter(
        NewsItem.created_at >= week_start
    ).order_by(NewsItem.created_at.desc()).all()

    return render_template('index.html', title='Home', news_items=news_items)

@bp.route('/dashboard')
@login_required
def dashboard():
    # Get news from the last 4 weeks
    four_weeks_ago = datetime.utcnow() - timedelta(weeks=4)
    news_items = NewsItem.query.filter(
        NewsItem.created_at >= four_weeks_ago
    ).order_by(NewsItem.created_at.desc()).all()
    
    # Group by week
    weekly_news = {}
    for item in news_items:
        week = item.created_at.isocalendar()[1]
        if week not in weekly_news:
            weekly_news[week] = []
        weekly_news[week].append(item)
    
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
    return redirect(url_for('routes.index'))
