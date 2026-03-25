import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot

from database import get_pending_reminders, mark_notified, mark_sent
from keyboards import done_keyboard, seen_keyboard

logger = logging.getLogger(__name__)


def format_remind_time(remind_at_str: str) -> str:
    """Красиво форматировать время напоминания"""
    dt = datetime.strptime(remind_at_str, "%Y-%m-%d %H:%M:%S")
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    if dt.date() == today:
        day_str = "Сегодня"
    elif dt.date() == tomorrow:
        day_str = "Завтра"
    else:
        day_str = dt.strftime("%d.%m.%Y")

    return f"{day_str} в {dt.strftime('%H:%M')}"


async def check_reminders(bot: Bot):
    """Главная функция планировщика — проверяет каждую минуту"""
    while True:
        try:
            now = datetime.now()
            reminders = get_pending_reminders()

            for row in reminders:
                reminder_id, user_id, text, remind_at_str, notified_10, notified_5, notified_2, is_sent = row
                remind_at = datetime.strptime(remind_at_str, "%Y-%m-%d %H:%M:%S")
                diff_minutes = (remind_at - now).total_seconds() / 60
                time_str = format_remind_time(remind_at_str)

                # За 10 минут
                if 9.5 <= diff_minutes <= 10.5 and not notified_10:
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"⏰ <b>Через 10 минут!</b>\n\n"
                             f"📌 {text}\n"
                             f"🕐 {time_str}\n\n"
                             f"Готовься! 💪",
                        parse_mode="HTML",
                        reply_markup=seen_keyboard(reminder_id)
                    )
                    mark_notified(reminder_id, "10")

                # За 5 минут
                elif 4.5 <= diff_minutes <= 5.5 and not notified_5:
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"🔔 <b>Через 5 минут!</b>\n\n"
                             f"📌 {text}\n"
                             f"🕐 {time_str}\n\n"
                             f"Уже скоро! ⚡",
                        parse_mode="HTML",
                        reply_markup=seen_keyboard(reminder_id)
                    )
                    mark_notified(reminder_id, "5")

                # За 2 минуты
                elif 1.5 <= diff_minutes <= 2.5 and not notified_2:
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"🚀 <b>Через 2 минуты!</b>\n\n"
                             f"📌 {text}\n"
                             f"🕐 {time_str}\n\n"
                             f"Почти время! 🎯",
                        parse_mode="HTML",
                        reply_markup=seen_keyboard(reminder_id)
                    )
                    mark_notified(reminder_id, "2")

                # Само напоминание (время пришло или прошло не более 2 мин назад)
                elif -2 <= diff_minutes <= 0.5 and not is_sent:
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"🚨 <b>ВРЕМЯ!</b>\n\n"
                             f"📌 {text}\n"
                             f"🕐 {time_str}\n\n"
                             f"Действуй! 🎯",
                        parse_mode="HTML",
                        reply_markup=done_keyboard(reminder_id)
                    )
                    mark_sent(reminder_id)

        except Exception as e:
            logger.error(f"Ошибка в планировщике: {e}")

        await asyncio.sleep(30)  # проверяем каждые 30 секунд
