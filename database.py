import os
import logging
from datetime import datetime
import psycopg2

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
            warn_before INTEGER DEFAULT 10,
            notified_warn BOOLEAN DEFAULT FALSE,
            is_sent BOOLEAN DEFAULT FALSE,
            remind_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    # Миграция — добавляем/удаляем колонки если нужно
    migrations = [
        "ALTER TABLE reminders ADD COLUMN IF NOT EXISTS warn_before INTEGER DEFAULT 10",
        "ALTER TABLE reminders ADD COLUMN IF NOT EXISTS remind_count INTEGER DEFAULT 0",
        "ALTER TABLE reminders ADD COLUMN IF NOT EXISTS notified_warn BOOLEAN DEFAULT FALSE",
        "ALTER TABLE reminders DROP COLUMN IF EXISTS notified_10",
        "ALTER TABLE reminders DROP COLUMN IF EXISTS notified_5",
        "ALTER TABLE reminders DROP COLUMN IF EXISTS notified_2",
    ]
    for sql in migrations:
        cursor.execute(sql)
    conn.commit()
    conn.close()


def add_reminder(user_id: int, text: str, remind_at: datetime, warn_before: int = 10) -> int:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reminders (user_id, text, remind_at, warn_before) VALUES (%s, %s, %s, %s) RETURNING id",
        (user_id, text, remind_at, warn_before)
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
        "SELECT id, user_id, text, remind_at, warn_before, notified_warn, is_sent, remind_count FROM reminders WHERE is_sent = FALSE"
    )
    rows = cursor.fetchall()
    conn.close()
    return [(r[0], r[1], r[2], r[3].strftime("%Y-%m-%d %H:%M:%S"), r[4], r[5], r[6], r[7]) for r in rows]


def mark_notified_warn(reminder_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE reminders SET notified_warn = TRUE WHERE id = %s",
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


def increment_remind_count(reminder_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE reminders SET remind_count = remind_count + 1 WHERE id = %s",
        (reminder_id,)
    )
    conn.commit()
    conn.close()


def snooze_reminder(reminder_id: int, new_time: datetime):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE reminders SET remind_at = %s, notified_warn = FALSE, is_sent = FALSE, remind_count = 0 WHERE id = %s",
        (new_time, reminder_id)
    )
    conn.commit()
    conn.close()
