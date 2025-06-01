from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    email = db.Column(db.String(128))
    skills = db.Column(db.Text)
    experience = db.Column(db.Text)
    # ...existing fields...

    # NEW fields for AI screening
    ai_screening_summary = db.Column(db.Text)
    ai_screening_questions = db.Column(db.JSON)