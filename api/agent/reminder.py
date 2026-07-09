import os
import sqlite3
import uuid
import datetime

# Database path: api/db/reminders.db
DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "db"))
DB_PATH = os.path.join(DB_DIR, "reminders.db")

# Ensure the database directory exists
os.makedirs(DB_DIR, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id TEXT PRIMARY KEY,
            task TEXT NOT NULL,
            remind_at TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Initialize the database table
init_db()

def create_reminder(task: str, remind_at: str) -> str:
    """
    Creates a reminder and saves it to the SQLite database.
    """
    try:
        reminder_id = str(uuid.uuid4())
        created_at = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reminders (id, task, remind_at, created_at) VALUES (?, ?, ?, ?)",
            (reminder_id, task, remind_at, created_at)
        )
        conn.commit()
        conn.close()
        
        return f"Successfully created reminder: '{task}' at {remind_at}."
    except Exception as e:
        return f"Error creating reminder: {str(e)}"
