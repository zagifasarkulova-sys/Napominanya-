from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить напоминание", callback_data="add")],
        [InlineKeyboardButton(text="📋 Мои напоминания", callback_data="list")],
    ])


def date_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Сегодня", callback_data="date_today"),
            InlineKeyboardButton(text="📅 Завтра", callback_data="date_tomorrow"),
        ],
        [InlineKeyboardButton(text="🗓 Другой день", callback_data="date_custom")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu")],
    ])


def time_keyboard() -> InlineKeyboardMarkup:
    times = ["07:00", "08:00", "09:00", "12:00", "15:00", "17:00", "18:00", "20:00", "22:00"]
    rows = []
    row = []
    for i, t in enumerate(times):
        row.append(InlineKeyboardButton(text=t, callback_data=f"time_{t}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="✏️ Своё время", callback_data="time_custom")])
    rows.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def warn_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="5 мин", callback_data="warn_5"),
            InlineKeyboardButton(text="10 мин", callback_data="warn_10"),
            InlineKeyboardButton(text="15 мин", callback_data="warn_15"),
            InlineKeyboardButton(text="30 мин", callback_data="warn_30"),
        ],
        [InlineKeyboardButton(text="✏️ Своё число", callback_data="warn_custom")],
        [InlineKeyboardButton(text="🔕 Не напоминать заранее", callback_data="warn_none")],
    ])


def confirm_keyboard(reminder_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu")],
        [InlineKeyboardButton(text="➕ Ещё одно", callback_data="add")],
    ])


def list_keyboard(reminders: list) -> InlineKeyboardMarkup:
    rows = []
    for r in reminders:
        rid, text, remind_at = r
        short = text[:20] + "..." if len(text) > 20 else text
        rows.append([
            InlineKeyboardButton(text=f"🗑 {short}", callback_data=f"delete_{rid}")
        ])
    rows.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def seen_keyboard(reminder_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Видел", callback_data=f"seen_{reminder_id}")]
    ])


def done_keyboard(reminder_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Выполнено", callback_data=f"done_{reminder_id}"),
            InlineKeyboardButton(text="⏰ +30 мин", callback_data=f"snooze_{reminder_id}"),
        ]
    ])


def delete_confirm_keyboard(reminder_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗑 Да, удалить", callback_data=f"confirm_delete_{reminder_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="list"),
        ]
    ])
