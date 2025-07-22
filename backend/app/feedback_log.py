# backend/app/feedback_log.py
from sqlalchemy.orm import Session
from app.db import get_db, FeedbackLog, SessionLocal

def log_feedback(question: str, answer: str, source: str | None):
    db: Session = SessionLocal()
    entry = FeedbackLog(question=question, answer=answer, source=source)
    db.add(entry)
    db.commit()
    db.close()
