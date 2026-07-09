import datetime
from db.reminder_db import SessionLocal, Base, engine
from db.models.reminder import Reminder

# Create tables if they do not exist
Base.metadata.create_all(bind=engine)

def create_reminder(task: str, remind_at: str) -> str:
    """
    Creates a reminder and saves it using SQLAlchemy.
    """
    db = SessionLocal()
    try:
        # Parse the remind_at ISO-8601 string to a datetime object
        remind_at_dt = datetime.datetime.fromisoformat(remind_at)
        
        db_reminder = Reminder(
            task=task,
            remind_at=remind_at_dt
        )
        db.add(db_reminder)
        db.commit()
        db.refresh(db_reminder)
        
        return f"Successfully created reminder: '{task}' at {remind_at}."
    except Exception as e:
        db.rollback()
        return f"Error creating reminder: {str(e)}"
    finally:
        db.close()
