import datetime

import markup
import telebot
import re
import os
from config import TOKEN, DATASET_DIR
import database
import mim_engine
import keyboards
import car_engine
import admin_engine  # Подключили наш пульт админки

bot = telebot.TeleBot(TOKEN, threaded=False)
user_sessions = {}

# Инициализация бессмертных папок при старте сервера
database.init_db()
if not os.path.exists(DATASET_DIR):
    os.makedirs(DATASET_DIR)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_sessions[chat_id] = {"step": "waiting_menu_choice"}
    bot.send_message(
        chat_id,
        "📦 <b>=== ИИ-ЭКОСИСТЕМА VALUATION v6.6 ===</b>\n\nПривет, Иван! Софт работает в облаке 24/7.\nВыберите формат проценки лота у капота:",
        parse_mode="HTML",
        reply_markup=keyboards.get_start_keyboard()
    )


@bot.callback_query_handler(func=lambda call: call.data in ["manual_flow_start", "error_retry_manual"])
def manual_flow_start(call):
    chat_id = call.message.chat.id
    user_sessions[chat_id] = {"step": "waiting_full_text"}
    bot.delete_message(chat_id, call.message.message_id)
    bot.send_message(
        chat_id,
        "✏️ <b>Введи бренд и размер одной строкой:</b>\nПример: <code>Мишлен 235 60 18</code>\n\n<i>Напиши параметры прямо сюда в чат 👇</i>",
        parse_mode="HTML"
    )
    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda message: message.chat.id in user_sessions and user_sessions[message.chat.id].get(
    "step") == "waiting_full_text")
def handle_initial_text(message):
    chat_id = message.chat.id
    raw_text = message.text.strip()

    size_text, radius_int = mim_engine.parse_tire_size(raw_text)

    if size_text is None or radius_int is None:
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            telebot.types.InlineKeyboardButton("⌨️ Попробовать ввести заново", callback_data="error_retry_manual"),
            telebot.types.InlineKeyboardButton("📸 Перейти к оценке по ФОТО", callback_data="ai_photo_flow"),
            telebot.types.InlineKeyboardButton("🚘 Найти размер по МАРКЕ МАШИНЫ", callback_data="car_model_flow")
        )
        bot.send_message(
            chat_id,
            "❌ <b>Размер шины не распознан!</b>\n\nПожалуйста, введите параметры правильно (например: <code>235 60 18</code>).\nИли выберите альтернативный вариант подбора лота:",
            parse_mode="HTML",
            reply_markup=markup
        )
        return

    words = raw_text.split()
    brand_name = words if words else "Unknown"
    base_price = mim_engine.get_average_mim_price(radius_int)

    user_sessions[chat_id] = {
        "step": "waiting_options", "radius_val": radius_int, "size_display": size_text,
        "brand": brand_name, "price_new_one": base_price, "is_razno": False, "is_china": False
    }
    render_mim_menu(message, chat_id)


def render_mim_menu(message, chat_id):
    data = user_sessions[chat_id]
    markup = keyboards.get_mim_keyboard(data["radius_val"], data["is_razno"], data["is_china"])
    response = (
        f"📐 Размер <b>{data['size_display']}</b> успешно принят!\n\n"
        f"⚠️ <b>Сформируй опции комплекта:</b>\n"
        f"• Тип: <code>{'Разноширокие' if data['is_razno'] else 'Одноширокие'}</code>\n"
        f"• Класс: <code>{'Бюджетный Китай' if data['is_china'] else 'Премиум/Импорт'}</code>"
    )
    try:
        bot.edit_message_text(response, chat_id, message.message_id, parse_mode="HTML", reply_markup=markup)
    except Exception:
        bot.send_message(chat_id, response, parse_mode="HTML", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("opt_"))
def handle_options(call):
    chat_id = call.message.chat.id
    data = user_sessions.get(chat_id)
    if not data: return

    if call.data == "opt_mono_china":
        data["is_razno"] = False
    elif call.data == "opt_multi_china":
        data["is_razno"] = True
    elif call.data == "opt_only_china":
        data["is_china"] = True
    elif call.data == "opt_only_premium":
        data["is_china"] = False
    elif call.data == "opt_done":
        rad = data["radius_val"]
        base_p = data["price_new_one"]
        if data["is_china"]:
            base_p = 11000 if rad >= 21 else int(base_p * 0.6)
        data["price_new_one"] = base_p

        bot.delete_message(chat_id, call.message.message_id)
        bot.send_message(
            chat_id,
            f"✅ Параметры шин зафиксированы.\n💰 <b>Цена нового по МИМ: {base_p} ₽/колесо</b>\n\n❓ Лот идет в комплекте с дисками?",
            reply_markup=keyboards.get_disks_keyboard()
        )
        return
    render_mim_menu(call.message, chat_id)


@bot.callback_query_handler(
    func=lambda call: call.data in ["has_disks_flow", "no_disks_flow", "disk_original", "disk_replica"])
def handle_disks(call):
    chat_id = call.message.chat.id
    data = user_sessions.get(chat_id)
    if not data: return

    if call.data == "no_disks_flow":
        data["has_disks"], data["disks_bonus"], data["disks_status"] = False, 0, "None"
        ask_age_protector(chat_id, call.message.message_id)
    elif call.data == "has_disks_flow":
        bot.edit_message_text("🔮 <b>Оценка дисков:</b> Укажите класс установленных дисков:", chat_id,
                              call.message.message_id, parse_mode="HTML",
                              reply_markup=keyboards.get_disks_type_keyboard())
    elif call.data in ["disk_original", "disk_replica"]:
        data["has_disks"] = True
        data["disks_status"] = "Original" if call.data == "disk_original" else "Replica"
        data["disks_bonus"] = (20000 if data["radius_val"] >= 19 else 12000) if call.data == "disk_original" else 6000
        ask_age_protector(chat_id, call.message.message_id)
    bot.answer_callback_query(call.id)


def ask_age_protector(chat_id, msg_id):
    user_sessions[chat_id]["step"] = "waiting_age_prof"
    bot.delete_message(chat_id, msg_id)
    bot.send_message(chat_id,
                     "✏️ Введи через пробел <b>Возраст (лет)</b> и <b>Протектор (мм)</b>:\nПример: <code>3 6</code>",
                     parse_mode="HTML")


@bot.message_handler(func=lambda message: message.chat.id in user_sessions and user_sessions[message.chat.id].get(
    "step") == "waiting_age_prof")
def handle_age_prof(message):
    chat_id = message.chat.id
    text = message.text.strip()
    numbers = re.findall(r'\d+\.\d+|\d+', text)

    if len(numbers) >= 2:
        user_sessions[chat_id]["age"] = int(float(numbers[0]))
        user_sessions[chat_id]["protector"] = float(numbers[1])
        bot.send_message(chat_id, "⚙️ Данные износа приняты. Есть ли видимые дефекты шин?",
                         reply_markup=keyboards.get_defects_keyboard())
    else:
        bot.send_message(chat_id, "❌ Неверный формат! Введи два числа через пробел (например: 3 6)")


@bot.callback_query_handler(func=lambda call: call.data == "td_0")
def handle_final(call):
    chat_id = call.message.chat.id
    data = user_sessions.get(chat_id)
    if not data:
        return

    bot.delete_message(chat_id, call.message.message_id)

    # 1. ВЫЗЫВАЕМ ЭКСПЕРТНЫЙ КАЛЬКУЛЯТОР ШИН (Твой новый car_engine.py)
    tire_result = car_engine.calculate_tire_valuation(
        base_new_price=data["price_new_one"] * 4,
        brand=data["brand"],
        protector=data["protector"],
        age=data["age"],
        tire_size=data["size_display"],
        defects=[]  # На шаге td_0 дефектов шин нет
    )

    # Если шины не прошли жесткий фильтр (протектор < 4мм или возраст > 5 лет)
    if not tire_result["success"]:
        bot.send_message(chat_id, tire_result["message"], parse_mode="HTML")

        # ЗАПИСЫВАЕМ ОТКЛОНЕННЫЙ ЛОТ В БАЗУ (final_p = 0, лот уйдет в Trash автоматически)
        database.log_tire_request(
            user_id=chat_id,
            brand=str(data["brand"]),
            size=data["size_display"],
            age=data["age"],
            protector=data["protector"],
            margin=0,
            img_path="Manual_Input"
        )
        user_sessions.pop(chat_id, None)  # Очищаем сессию
        return

    # 2. СЧИТАЕМ ИТОГОВУЮ ЦЕНУ ДЛЯ ТВОЕЙ КОЛОНКИ calculated_margin
    # Вытаскиваем верхнюю границу цены регуляркой из сообщения движка
    prices = re.findall(r'\d+', tire_result['message'])
    final_p = int(prices[-1]) if prices else 0

    # 3. ЕСЛИ ЛОТ С ДИСКАМИ, СЧИТАЕМ ИХ СТОИМОСТЬ И ПРИБАВЛЯЕМ К ОБЩЕЙ СУММЕ
    wheel_report_text = ""
    if data.get("has_disks", False):
        w_type = 'оригинал' if data.get("disks_status") == "Original" else 'реплика'

        wheel_result = car_engine.calculate_wheel_valuation(
            diameter=data["radius_val"],
            wheel_type=w_type,
            defects=[]  # Дефектов дисков на этом шаге нет
        )

        if wheel_result["success"]:
            wheel_report_text = "\n\n" + wheel_result["message"]
            # Вытаскиваем верхнюю границу цены дисков и плюсуем к итоговой марже в БД
            wheel_prices = re.findall(r'\d+', wheel_result['message'])
            if wheel_prices:
                final_p += int(wheel_prices[-1])
        else:
            wheel_report_text = "\n\n⚠️ " + wheel_result["message"]

    # 4. ПИШЕМ СДЕЛКУ В ТВОЮ БАЗУ ДАННЫХ SQLITE С СОХРАНЕНИЕМ ВСЕХ КОЛОНОК
    database.log_tire_request(
        user_id=chat_id,
        brand=str(data["brand"]),
        size=data["size_display"],
        age=data["age"],
        protector=data["protector"],
        margin=final_p,  # Сумма выкупа лота пойдет в твою calculated_margin
        img_path="Manual_Input"
    )

    # 5. ВЫВОДИМ ОКОНЧАТЕЛЬНЫЙ ОТЧЕТ В ЧАТ
    final_report = (
        f"📦 <b>=== ИИ-ОТЧЕТ VALUATION v6.6 ===</b>\n\n"
        f"{tire_result['message']}"
        f"{wheel_report_text}"
    )

    # Эта закрывающая скобка инлайн-кнопки была оборвана в твоем сообщении, восстанавливаем её:
    markup.add(telebot.types.InlineKeyboardButton("🔄 Оценить еще один лот", callback_data="manual_flow_start"))
    bot.send_message(chat_id, final_report, parse_mode="HTML", reply_markup=markup)
    user_sessions.pop(chat_id, None)
    bot.answer_callback_query(call.id)


# =====================================================================
# 5. РЕГИСТРАЦИЯ КОМАНД АДМИН-ПУЛЬТА И ЗАПУСК СЕРВЕРА
# =====================================================================

@bot.message_handler(commands=['stats'])
def admin_stats(message):
    """Вызов ИТ-аналитики из пульта админки Ивана"""
    admin_engine.handle_stats_command(bot, message)


@bot.message_handler(commands=['excel'])
def admin_excel(message):
    """Выгрузка Pandas-отчета .xlsx для Poco Pad"""
    admin_engine.handle_excel_command(bot, message)


# Бессмертный цикл опроса Telegram-серверов 24/7
if __name__ == "__main__":
    print("🚀 [OK] ИИ-ЭКОСИСТЕМА VALUATION v6.6 успешно запущена в облаке!")
    print("📈 Пульт админки Ивана активен. Ожидание откликов...")
    bot.polling(none_stop=True)



