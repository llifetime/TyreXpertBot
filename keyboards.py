from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from mim_engine import check_mim_has_multiwide


def get_start_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📸 Оценить комплект по ФОТО (ИИ)", callback_data="ai_photo_flow"),
        InlineKeyboardButton("⌨️ Ручной ввод параметров", callback_data="manual_flow_start")
    )
    return markup


def get_mim_keyboard(radius, is_razno, is_china):
    has_multi = check_mim_has_multiwide(radius)
    markup = InlineKeyboardMarkup(row_width=2)
    multi_btn = InlineKeyboardButton("🛞 Разноширокие",
                                     callback_data="opt_multi_china") if has_multi else InlineKeyboardButton(
        "🔒 Разношир недоступен в МИМ", callback_data="opt_locked")

    markup.add(InlineKeyboardButton("⚙️ Одноширокие", callback_data="opt_mono_china"), multi_btn)
    markup.add(InlineKeyboardButton("🇨🇳 Бюджетный Китай", callback_data="opt_only_china"),
               InlineKeyboardButton("👑 Premium (Импорт)", callback_data="opt_only_premium"))
    markup.add(InlineKeyboardButton("⏩ Всё настроил, к оценке дисков", callback_data="opt_done"))
    return markup


def get_disks_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("💿 Да, комплект на ДИСКАХ", callback_data="has_disks_flow"),
        InlineKeyboardButton("⭕ Нет, только ГОЛАЯ резина", callback_data="no_disks_flow")
    )
    return markup


def get_disks_type_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("👑 Оригинал (Завод)", callback_data="disk_original"),
        InlineKeyboardButton("🇨🇳 Реплика / Литьё", callback_data="disk_replica")
    )
    return markup


def get_defects_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("⚠️ Указать дефекты шин", callback_data="def_tires_menu"),
        InlineKeyboardButton("⏩ Пропустить (Без дефектов)", callback_data="td_0")
    )
    return markup
