from app import create_app, db
from app.models import User
from scheduler import init_scheduler
import os

app = create_app()

@app.cli.command("init-db")
def init_db():
    """Initialize the database."""
    db.create_all()
    
    # Create a default user if none exists
    if not User.query.filter_by(username='admin').first():
        user = User(username='admin', email='admin@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        print("Default user created: admin/password")

@app.cli.command("run-scheduler")
def run_scheduler():
    """Run the scheduler."""
    init_scheduler()

if __name__ == "__main__":
    app.run(debug=True)