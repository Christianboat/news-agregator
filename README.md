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

---

## ✨ Features

- ✅ User Authentication (Flask-Login)  
- ✅ Fetch news from multiple RSS feeds  
- ✅ Smart filtering for education-related content  
- ✅ Automatic image scraping + thumbnail generation  
- ✅ Gemini AI integration for short-form video scripts  
- ✅ Weekly **unified scripts** and per-news **social media scripts**  
- ✅ Dashboard to view and track progress  
- ✅ API endpoints (`/api/status`) for monitoring  

---

## 🖼️ Screenshots

> _Add your own screenshots here (UI, dashboard, etc.)_

<p align="center">
  <img src="static/images/screenshot1.png" width="400" alt="Home Page"/>
  <img src="static/images/screenshot2.png" width="400" alt="Dashboard"/>
</p>

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
```bash
git clone https://github.com/yourusername/edu-news-pipeline.git
cd edu-news-pipeline
2️⃣ Set up a virtual environment
bash
Copy code
python3 -m venv venv
source venv/bin/activate
3️⃣ Install dependencies
bash
Copy code
pip install -r requirements.txt
4️⃣ Configure environment variables
Create a .env file in the project root:

ini
Copy code
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///app.db

TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-chat-id
GEMINI_API_KEY=your-gemini-api-key
5️⃣ Initialize the database
bash
Copy code
flask db upgrade   # If using Flask-Migrate
# OR quick dev start:
python -c "from app import create_app, db; app=create_app(); 
with app.app_context(): db.create_all()"
6️⃣ Run the app
bash
Copy code
flask run
Then visit 👉 http://127.0.0.1:5000/

📂 Project Structure
arduino
Copy code
.
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── templates/
│   ├── static/
│   │   └── images/
│   └── ...
├── scripts/
│   └── news_scraper.py
├── migrations/   # (if using Flask-Migrate)
├── config.py
├── run.py
├── requirements.txt
└── README.md
🔄 Workflow
User logs in ➝ clicks Retrieve News

Background thread runs the news pipeline:

Fetches latest RSS news

Filters education stories

Scrapes images & saves thumbnails

Generates AI video scripts

Saves unified + per-news scripts to DB

UI dashboard updates with weekly stats

🧪 Development Notes
Uses background threads for the pipeline ➝ doesn’t block UI

Handles missing tables safely with db.create_all() (dev) or flask db migrate (prod)

Logging built in (logging module) for errors and pipeline events

API /api/status returns JSON for AJAX polling

🛡️ Security
Secrets & API keys are not hardcoded — configure them via .env

Passwords hashed with Werkzeug (generate_password_hash)

Session managed with Flask-Login

📌 Roadmap
 Add pagination to dashboard

 Add support for more news sources

 Add user roles (admin, staff, viewer)

 Deploy to free hosting (Render, Railway, or other Heroku alternative)

🤝 Contributing
Pull requests welcome! Please fork the repo and submit a PR.
For major changes, open an issue first to discuss what you’d like to change.

📜 License
This project is licensed under the MIT License.

<p align="center"> Made with ❤️ using Flask & Gemini AI </p> ```
