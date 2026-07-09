from sqlalchemy import Column, String, Integer, Boolean, DateTime
from db.reminder_db import Base
from datetime import datetime

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    task = Column(String, index=True)
    remind_at = Column(DateTime, index=True)
    is_completed = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    