import os
import logging
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            text TEXT NOT NULL,
            remind_at TIMESTAMP NOT NULL,
            notified_10 BOOLEAN DEFAULT FALSE,
            notified_5 BOOLEAN DEFAULT FALSE,
            notified_2 BOOLEAN DEFAULT FALSE,
            is_sent BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    conn.close()


def add_reminder(user_id: int, text: str, remind_at: datetime) -> int:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reminders (user_id, text, remind_at) VALUES (%s, %s, %s) RETURNING id",
        (user_id, text, remind_at)
    )
    reminder_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return reminder_id


def get_reminders(user_id: int) -> list:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, text, remind_at FROM reminders WHERE user_id = %s AND is_sent = FALSE ORDER BY remind_at ASC",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [(r[0], r[1], r[2].strftime("%Y-%m-%d %H:%M:%S")) for r in rows]


def delete_reminder(reminder_id: int, user_id: int) -> bool:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM reminders WHERE id = %s AND user_id = %s",
        (reminder_id, user_id)
    )
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_pending_reminders() -> list:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, user_id, text, remind_at, notified_10, notified_5, notified_2, is_sent
           FROM reminders WHERE is_sent = FALSE"""
    )
    rows = cursor.fetchall()
    conn.close()
    return [(r[0], r[1], r[2], r[3].strftime("%Y-%m-%d %H:%M:%S"), r[4], r[5], r[6], r[7]) for r in rows]


def mark_notified(reminder_id: int, level: str):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE reminders SET notified_{level} = TRUE WHERE id = %s",
        (reminder_id,)
    )
    conn.commit()
    conn.close()


def mark_sent(reminder_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE reminders SET is_sent = TRUE WHERE id = %s",
        (reminder_id,)
    )
    conn.commit()
    conn.close()


def snooze_reminder(reminder_id: int, new_time: datetime):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE reminders
           SET remind_at = %s, notified_10 = FALSE, notified_5 = FALSE, notified_2 = FALSE, is_sent = FALSE
           WHERE id = %s""",
        (new_time, reminder_id)
    )
    conn.commit()
    conn.close()
```

И обнови `requirements.txt`:
```
aiogram==3.7.0
aiohttp==3.9.5
psycopg2-binary
pytz
