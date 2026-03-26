import logging
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from database import (
    add_reminder, get_reminders, delete_reminder,
    mark_sent, snooze_reminder
)
from keyboards import (
    main_menu_keyboard, date_keyboard, time_keyboard,
    list_keyboard, confirm_keyboard, delete_confirm_keyboard,
    warn_keyboard, done_keyboard, seen_keyboard
)

logger = logging.getLogger(__name__)
router = Router()


class AddReminder(StatesGroup):
    waiting_text = State()
    waiting_date = State()
    waiting_custom_date = State()
    waiting_time = State()
    waiting_custom_time = State()
    waiting_warn = State()
    waiting_custom_warn = State()


def format_remind_time(dt: datetime) -> str:
    from datetime import timedelta
    import pytz
    TIMEZONE = pytz.timezone("Asia/Oral")
    today = datetime.now(TIMEZONE).replace(tzinfo=None).date()
    tomorrow = today + timedelta(days=1)
    if dt.date() == today:
        return f"Сегодня в {dt.strftime('%H:%M')}"
    elif dt.date() == tomorrow:
        return f"Завтра в {dt.strftime('%H:%M')}"
    return dt.strftime("%d.%m.%Y в %H:%M")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        f"Я твой личный бот напоминаний 🔔\n"
        f"Помогу не забыть ничего важного.\n\n"
        f"Выбери действие 👇",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )


@router.callback_query(F.data == "menu")
async def show_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыбери действие 👇",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "add")
async def add_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddReminder.waiting_text)
    await callback.message.edit_text(
        "➕ <b>Новое напоминание</b>\n\n"
        "✏️ Введи текст напоминания:",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddReminder.waiting_text)
async def got_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await state.set_state(AddReminder.waiting_date)
    await message.answer(
        "📅 <b>Выбери день:</b>",
        parse_mode="HTML",
        reply_markup=date_keyboard()
    )


@router.callback_query(AddReminder.waiting_date, F.data.in_(["date_today", "date_tomorrow"]))
async def got_date_quick(callback: CallbackQuery, state: FSMContext):
    today = datetime.now().date()
    if callback.data == "date_today":
        chosen_date = today
        label = "Сегодня"
    else:
        chosen_date = today + timedelta(days=1)
        label = "Завтра"

    await state.update_data(date=chosen_date.strftime("%Y-%m-%d"), date_label=label)
    await state.set_state(AddReminder.waiting_time)
    await callback.message.edit_text(
        f"📅 {label}\n\n🕐 <b>Выбери время:</b>",
        parse_mode="HTML",
        reply_markup=time_keyboard()
    )
    await callback.answer()


@router.callback_query(AddReminder.waiting_date, F.data == "date_custom")
async def got_date_custom_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddReminder.waiting_custom_date)
    await callback.message.edit_text(
        "🗓 <b>Введи дату</b>\n\n"
        "Формат: <code>ДД.ММ.ГГГГ</code>\n"
        "Например: <code>01.04.2026</code>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddReminder.waiting_custom_date)
async def got_custom_date(message: Message, state: FSMContext):
    try:
        dt = datetime.strptime(message.text.strip(), "%d.%m.%Y")
        if dt.date() < datetime.now().date():
            await message.answer("❌ Эта дата уже прошла. Введи другую:")
            return
        label = dt.strftime("%d.%m.%Y")
        await state.update_data(date=dt.strftime("%Y-%m-%d"), date_label=label)
        await state.set_state(AddReminder.waiting_time)
        await message.answer(
            f"📅 {label}\n\n🕐 <b>Выбери время:</b>",
            parse_mode="HTML",
            reply_markup=time_keyboard()
        )
    except ValueError:
        await message.answer(
            "❌ Неверный формат. Попробуй ещё раз:\n"
            "Например: <code>01.04.2026</code>",
            parse_mode="HTML"
        )


@router.callback_query(AddReminder.waiting_time, F.data.startswith("time_") & ~F.data.in_(["time_custom"]))
async def got_time_quick(callback: CallbackQuery, state: FSMContext):
    time_str = callback.data.replace("time_", "")
    data = await state.get_data()
    remind_at = datetime.strptime(f"{data['date']} {time_str}", "%Y-%m-%d %H:%M")

    import pytz
    TIMEZONE = pytz.timezone("Asia/Oral")
    now = datetime.now(TIMEZONE).replace(tzinfo=None)

    if remind_at <= now:
        await callback.answer("❌ Это время уже прошло!", show_alert=True)
        return

    await state.update_data(remind_at=remind_at.strftime("%Y-%m-%d %H:%M"))
    await state.set_state(AddReminder.waiting_warn)
    await callback.message.edit_text(
        f"⏰ <b>За сколько минут предупредить?</b>",
        parse_mode="HTML",
        reply_markup=warn_keyboard()
    )
    await callback.answer()


@router.callback_query(AddReminder.waiting_time, F.data == "time_custom")
async def got_time_custom_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddReminder.waiting_custom_time)
    await callback.message.edit_text(
        "✏️ <b>Введи своё время</b>\n\n"
        "Формат: <code>ЧЧ:ММ</code>\n"
        "Например: <code>13:45</code>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddReminder.waiting_custom_time)
async def got_custom_time(message: Message, state: FSMContext):
    try:
        time_obj = datetime.strptime(message.text.strip(), "%H:%M")
        data = await state.get_data()
        remind_at = datetime.strptime(
            f"{data['date']} {time_obj.strftime('%H:%M')}", "%Y-%m-%d %H:%M"
        )

        import pytz
        TIMEZONE = pytz.timezone("Asia/Oral")
        now = datetime.now(TIMEZONE).replace(tzinfo=None)

        if remind_at <= now:
            await message.answer("❌ Это время уже прошло. Введи другое:")
            return

        await state.update_data(remind_at=remind_at.strftime("%Y-%m-%d %H:%M"))
        await state.set_state(AddReminder.waiting_warn)
        await message.answer(
            "⏰ <b>За сколько минут предупредить?</b>",
            parse_mode="HTML",
            reply_markup=warn_keyboard()
        )
    except ValueError:
        await message.answer(
            "❌ Неверный формат. Попробуй ещё раз:\n"
            "Например: <code>13:45</code>",
            parse_mode="HTML"
        )


@router.callback_query(AddReminder.waiting_warn, F.data.startswith("warn_"))
async def got_warn(callback: CallbackQuery, state: FSMContext):
    warn_val = callback.data.replace("warn_", "")

    if warn_val == "custom":
        await state.set_state(AddReminder.waiting_custom_warn)
        await callback.message.edit_text(
            "✏️ <b>Введи количество минут</b>\n\n"
            "Например: <code>20</code>",
            parse_mode="HTML"
        )
        await callback.answer()
        return

    warn_before = 0 if warn_val == "none" else int(warn_val)
    await save_reminder(callback.message, state, warn_before, edit=True, user_id=callback.from_user.id)
    await callback.answer()


@router.message(AddReminder.waiting_custom_warn)
async def got_custom_warn(message: Message, state: FSMContext):
    try:
        warn_before = int(message.text.strip())
        if warn_before <= 0:
            await message.answer("❌ Введи число больше нуля:")
            return
        await save_reminder(message, state, warn_before, edit=False, user_id=message.from_user.id)
    except ValueError:
        await message.answer("❌ Только цифры! Например: <code>20</code>", parse_mode="HTML")


async def save_reminder(message_or_callback, state: FSMContext, warn_before: int, edit: bool, user_id: int):
    data = await state.get_data()
    remind_at = datetime.strptime(data["remind_at"], "%Y-%m-%d %H:%M")
    reminder_id = add_reminder(user_id, data["text"], remind_at, warn_before)
    await state.clear()

    time_label = format_remind_time(remind_at)
    warn_text = f"⏰ Предупрежу за {warn_before} мин" if warn_before > 0 else "🔕 Без предупреждения"

    text = (
        f"✅ <b>Сохранено!</b>\n\n"
        f"📌 {data['text']}\n"
        f"📅 {time_label}\n"
        f"{warn_text}"
    )

    if edit:
        await message_or_callback.edit_text(text, parse_mode="HTML", reply_markup=confirm_keyboard(reminder_id))
    else:
        await message_or_callback.answer(text, parse_mode="HTML", reply_markup=confirm_keyboard(reminder_id))


@router.callback_query(F.data == "list")
async def show_list(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    reminders = get_reminders(callback.from_user.id)

    if not reminders:
        await callback.message.edit_text(
            "📋 <b>Твои напоминания</b>\n\n"
            "😴 Пока нет активных напоминаний.",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )
    else:
        lines = []
        for i, (rid, text, remind_at_str) in enumerate(reminders, 1):
            dt = datetime.strptime(remind_at_str, "%Y-%m-%d %H:%M:%S")
            time_label = format_remind_time(dt)
            lines.append(f"{i}. 📌 {text}\n    🕐 {time_label}")

        text_block = "\n\n".join(lines)
        await callback.message.edit_text(
            f"📋 <b>Твои напоминания ({len(reminders)}):</b>\n\n"
            f"{text_block}\n\n"
            f"👇 Нажми на напоминание чтобы удалить:",
            parse_mode="HTML",
            reply_markup=list_keyboard(reminders)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("delete_"))
async def delete_prompt(callback: CallbackQuery):
    reminder_id = int(callback.data.split("_")[1])
    await callback.message.edit_text(
        "🗑 <b>Удалить это напоминание?</b>",
        parse_mode="HTML",
        reply_markup=delete_confirm_keyboard(reminder_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete(callback: CallbackQuery):
    reminder_id = int(callback.data.split("_")[2])
    deleted = delete_reminder(reminder_id, callback.from_user.id)
    if deleted:
        await callback.message.edit_text(
            "✅ <b>Напоминание удалено!</b>",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )
    else:
        await callback.answer("❌ Не удалось удалить", show_alert=True)
    await callback.answer()


@router.callback_query(F.data.startswith("seen_"))
async def seen_handler(callback: CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("👍 Окей, жду тебя!", show_alert=False)


@router.callback_query(F.data.startswith("done_"))
async def done_handler(callback: CallbackQuery):
    reminder_id = int(callback.data.split("_")[1])
    mark_sent(reminder_id)
    await callback.message.edit_text(
        "🎉 <b>Молодец! Выполнено!</b>",
        parse_mode="HTML"
    )
    await callback.answer("🎉 Отлично!")


@router.callback_query(F.data.startswith("snooze_"))
async def snooze_handler(callback: CallbackQuery):
    reminder_id = int(callback.data.split("_")[1])
    import pytz
    TIMEZONE = pytz.timezone("Asia/Oral")
    new_time = datetime.now(TIMEZONE).replace(tzinfo=None) + timedelta(minutes=30)
    snooze_reminder(reminder_id, new_time)
    await callback.message.edit_text(
        f"⏰ <b>Напомню в {new_time.strftime('%H:%M')}!</b>",
        parse_mode="HTML"
    )
    await callback.answer()
