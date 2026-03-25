import sqlite3
from datetime import datetime

DB_PATH = "reminders.db"


def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            remind_at TEXT NOT NULL,
            notified_10 INTEGER DEFAULT 0,
            notified_5 INTEGER DEFAULT 0,
            notified_2 INTEGER DEFAULT 0,
            is_sent INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def add_reminder(user_id: int, text: str, remind_at: datetime) -> int:
    """Добавить напоминание, вернуть его ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reminders (user_id, text, remind_at) VALUES (?, ?, ?)",
        (user_id, text, remind_at.strftime("%Y-%m-%d %H:%M:%S"))
    )
    reminder_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return reminder_id


def get_reminders(user_id: int) -> list:
    """Получить все активные напоминания пользователя"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, text, remind_at FROM reminders WHERE user_id = ? AND is_sent = 0 ORDER BY remind_at ASC",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def delete_reminder(reminder_id: int, user_id: int) -> bool:
    """Удалить напоминание по ID (только своё)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM reminders WHERE id = ? AND user_id = ?",
        (reminder_id, user_id)
    )
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_pending_reminders() -> list:
    """Получить все несработавшие напоминания для планировщика"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, user_id, text, remind_at, notified_10, notified_5, notified_2, is_sent
           FROM reminders WHERE is_sent = 0"""
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def mark_notified(reminder_id: int, level: str):
    """Отметить что уведомление за N минут отправлено. level: '10', '5', '2'"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE reminders SET notified_{level} = 1 WHERE id = ?",
        (reminder_id,)
    )
    conn.commit()
    conn.close()


def mark_sent(reminder_id: int):
    """Отметить напоминание как отправленное (выполнено)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE reminders SET is_sent = 1 WHERE id = ?",
        (reminder_id,)
    )
    conn.commit()
    conn.close()


def snooze_reminder(reminder_id: int, new_time: datetime):
    """Отложить напоминание на новое время (кнопка +30 мин)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE reminders
           SET remind_at = ?, notified_10 = 0, notified_5 = 0, notified_2 = 0, is_sent = 0
           WHERE id = ?""",
        (new_time.strftime("%Y-%m-%d %H:%M:%S"), reminder_id)
    )
    conn.commit()
    conn.close()
