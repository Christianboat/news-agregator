# 📚 Education News Pipeline Web App

![Flask](https://img.shields.io/badge/Flask-2.0+-blue.svg?logo=flask)  
![Python](https://img.shields.io/badge/Python-3.9+-green.svg?logo=python)  
![SQLite](https://img.shields.io/badge/SQLite-Database-lightgrey.svg?logo=sqlite)  
![License](https://img.shields.io/badge/License-MIT-yellow.svg)  

A **Flask-based web application** that:  
- Fetches and filters the latest **Education News** from RSS feeds 🌍  
- Generates short **video scripts** using **Google Gemini AI** ✨  
- Stores news + scripts in a database 🗂️  
- Allows staff to **retrieve, manage, and view weekly scripts** 📖  
- Provides a simple **dashboard** for monitoring 📊
- Sends content to telegram

---

## ✨ Features

- ✅ User Authentication (Flask-Login)  
- ✅ Fetch news from multiple RSS feeds  
- ✅ Smart filtering for education-related content  
- ✅ Automatic image scraping + thumbnail generation  
- ✅ Gemini AI integration for short-form video scripts  
- ✅ Weekly **unified scripts** and per-news **social media scripts**  
- ✅ Dashboard to view and track progress
- ✅ Telegram Bot integrations  
- ✅ API endpoints (`/api/status`) for monitoring  

---


## 🛠️ Tech Stack

- **Backend:** Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login  
- **Database:** SQLite (default), easily switchable to PostgreSQL/MySQL  
- **Frontend:** HTML, Bootstrap, custom CSS, JS  
- **AI:** Google Gemini API (for script generation)  
- **Other:** APScheduler, Feedparser, BeautifulSoup4, Pillow  

---

## 🚀 Getting Started

### 1️⃣ Clone the repository
git clone https://github.com/yourusername/edu-news-pipeline.git
cd edu-news-pipeline

### 2️⃣ Set up a virtual environment
python3 -m venv venv
source venv/bin/activate

### 3️⃣ Install dependencies
pip install -r requirements.txt

### 4️⃣ Configure environment variables
update the config.py file in the project root:

SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///app.db

TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-chat-id
GEMINI_API_KEY=your-gemini-api-key

### 5️⃣ Initialize the database
flask db upgrade   # If using Flask-Migrate
# OR quick dev start:
python -c "from app import create_app, db; app=create_app(); 
with app.app_context(): db.create_all()"

### 6️⃣ Run the app

flask run



### 🔄 Workflow
User logs in ➝ clicks Retrieve News

Background thread runs the news pipeline:

Fetches latest RSS news

Filters education stories

Scrapes images & saves thumbnails

Generates AI video scripts

Saves unified + per-news scripts to DB

UI dashboard updates with weekly stats

Sends updates to th telegram chat

🧪 Development Notes
Uses background threads for the pipeline ➝ doesn’t block UI

Handles missing tables safely with db.create_all() (dev) or flask db migrate (prod)

Logging built in (logging module) for errors and pipeline events

API /api/status returns JSON for AJAX polling

🛡️ Security
Secrets & API keys are not hardcoded — configure them via .env

Passwords hashed with Werkzeug (generate_password_hash)

Session managed with Flask-Login


📜 License
This project is licensed under the MIT License.

--
<p align="center"> Made with ❤️ using Flask & Gemini AI </p>
