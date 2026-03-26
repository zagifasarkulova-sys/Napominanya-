import asyncio
import logging
import pytz
from datetime import datetime, timedelta
from aiogram import Bot
from database import get_pending_reminders, mark_notified_warn, mark_sent, increment_remind_count
from keyboards import done_keyboard, seen_keyboard

logger = logging.getLogger(__name__)

TIMEZONE = pytz.timezone("Asia/Oral")


def format_remind_time(remind_at_str: str) -> str:
    dt = datetime.strptime(remind_at_str, "%Y-%m-%d %H:%M:%S")
    today = datetime.now(TIMEZONE).replace(tzinfo=None).date()
    tomorrow = today + timedelta(days=1)
    if dt.date() == today:
        day_str = "Сегодня"
    elif dt.date() == tomorrow:
        day_str = "Завтра"
    else:
        day_str = dt.strftime("%d.%m.%Y")
    return f"{day_str} в {dt.strftime('%H:%M')}"


async def check_reminders(bot: Bot):
    while True:
        try:
            now = datetime.now(TIMEZONE).replace(tzinfo=None)
            reminders = get_pending_reminders()

            for row in reminders:
                reminder_id, user_id, text, remind_at_str, warn_before, notified_warn, is_sent, remind_count = row
                remind_at = datetime.strptime(remind_at_str, "%Y-%m-%d %H:%M:%S")
                diff_minutes = (remind_at - now).total_seconds() / 60
                time_str = format_remind_time(remind_at_str)

                # Предупреждение за N минут
                if warn_before and warn_before > 0:
                    warn_window_low = warn_before - 0.5
                    warn_window_high = warn_before + 0.5
                    if warn_window_low <= diff_minutes <= warn_window_high and not notified_warn:
                        await bot.send_message(
                            chat_id=user_id,
                            text=f"⏰ <b>Через {warn_before} минут!</b>\n\n"
                                 f"📌 {text}\n"
                                 f"🕐 {time_str}\n\n"
                                 f"Готовься! 💪",
                            parse_mode="HTML",
                            reply_markup=seen_keyboard(reminder_id)
                        )
                        mark_notified_warn(reminder_id)

                # Само напоминание — первый раз
                if -1 <= diff_minutes <= 0.5 and remind_count == 0:
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"🚨 <b>ВРЕМЯ!</b>\n\n"
                             f"📌 {text}\n"
                             f"🕐 {time_str}\n\n"
                             f"Действуй! 🎯",
                        parse_mode="HTML",
                        reply_markup=done_keyboard(reminder_id)
                    )
                    increment_remind_count(reminder_id)

                # Спам каждые 5 минут пока не нажмёт Выполнено
                elif remind_count > 0 and not is_sent:
                    minutes_since = (now - remind_at).total_seconds() / 60
                    expected_count = int(minutes_since / 5) + 1
                    if remind_count < expected_count:
                        await bot.send_message(
                            chat_id=user_id,
                            text=f"👋 <b>Эй, ты не забыл?</b>\n\n"
                                 f"📌 {text}\n\n"
                                 f"Нажми Выполнено когда сделаешь! ✅",
                            parse_mode="HTML",
                            reply_markup=done_keyboard(reminder_id)
                        )
                        increment_remind_count(reminder_id)

        except Exception as e:
            logger.error(f"Ошибка в планировщике: {e}")

        await asyncio.sleep(30)
