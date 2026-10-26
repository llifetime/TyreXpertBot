import os
from config import MY_TELEGRAM_ID
import database


def handle_stats_command(bot, message):
    if message.chat.id != MY_TELEGRAM_ID:
        bot.reply_to(message, "❌ Доступ ограничен.")
        return

    try:
        # Принимаем все 4 обновленных параметра из нашей новой функции
        total, avg_p, successful, total_volume = database.get_db_metrics()

        report = (
            f"📊 <b>=== ИТ-АНАЛИТИКА TYREXPERT v6.6 ===</b>\n\n"
            f"📈 Всего оценок в базе: <code>{total}</code>\n"
            f"✅ Прошли ИИ-фильтр (Approved): <code>{successful} шт.</code>\n"
            f"💰 Сумма потенциального выкупа: <b>{total_volume:,} ₽</b>\n"
            f"📏 Средний протектор лотов: <code>{avg_p:.2f} мм</code>\n\n"
            f"📂 Файлы зафиксированы в бессмертной папке <code>/data</code>"
        )
        bot.send_message(message.chat.id, report, parse_mode="HTML")
    except Exception as e:
        bot.send_message(message.chat.id, f"🚨 Ошибка аналитики: {e}")


def handle_excel_command(bot, message):
    if message.chat.id != MY_TELEGRAM_ID:
        bot.reply_to(message, "❌ Доступ ограничен.")
        return

    bot.send_message(message.chat.id, "⏳ Генерирую Excel-отчет для Poco Pad...")
    try:
        excel_filename = database.generate_excel_report()
        if excel_filename and os.path.exists(excel_filename):
            with open(excel_filename, "rb") as file:
                bot.send_document(
                    message.chat.id,
                    file,
                    caption="📈 <b>ИТ-выгрузка для Poco Pad готова.</b>\n<i>Все вилки цен и статусы износа внутри.</i>",
                    parse_mode="HTML"
                )
            os.remove(excel_filename)
        else:
            bot.send_message(message.chat.id, "🗄️ База данных еще пуста. Оценок не зафиксировано.")
    except Exception as e:
        bot.send_message(message.chat.id, f"🚨 Ошибка генерации Excel: {e}")
