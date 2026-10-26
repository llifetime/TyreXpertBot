import sqlite3
import os
import pandas as pd
import datetime
from config import DB_PATH


def init_db():
    try:
        # Автоматически создаем папку для базы данных, если её нет
        db_dir = os.path.dirname(DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tire_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                brand TEXT,
                size_raw TEXT,
                age INTEGER,
                protector REAL,
                calculated_margin REAL,
                status TEXT,
                image_path TEXT
            )
        """)
        conn.commit()
        conn.close()
        print(f"⚙️ База данных SQLite успешно инициализирована по пути: {DB_PATH}")
    except Exception as e:
        print(f"🚨 Ошибка инициализации базы данных: {e}")


def log_tire_request(user_id, brand, size, age, protector, margin, img_path="Manual_Input"):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Автоматически определяем статус на основе жестких экспертных границ износа (Пункт 2 ТЗ)
        # Если протектор ниже 4 мм или возраст старше 5 лет — лот идет в Trash
        if protector < 4.0 or age > 5:
            final_status = "Trash"
            margin = 0.0  # За забаненный лот цену выкупа обнуляем
        else:
            final_status = "Approved"

        cursor.execute("""
            INSERT INTO tire_requests (user_id, brand, size_raw, age, protector, calculated_margin, status, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, brand, size, age, protector, margin, final_status, img_path))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"🚨 Ошибка записи статистики в БД: {e}")


def get_db_metrics():
    """
    Расширенная аналитика для admin_engine.py.
    Возвращает: (Всего_оценок, Ср_протектор, Успешных_сделок, Общий_объем_выкупа)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 1. Всего лотов в базе
        cursor.execute("SELECT COUNT(*) FROM tire_requests")
        total = cursor.fetchone()[0]

        # 2. Средний протектор
        cursor.execute("SELECT AVG(protector) FROM tire_requests WHERE protector IS NOT NULL")
        avg_p = cursor.fetchone()[0] or 0.0

        # 3. Количество успешно одобренных лотов (Approved)
        cursor.execute("SELECT COUNT(*) FROM tire_requests WHERE status = 'Approved'")
        successful = cursor.fetchone()[0]

        # 4. Общая сумма потенциального выкупа (сумма маржи/цен по одобренным сделкам)
        cursor.execute("SELECT SUM(calculated_margin) FROM tire_requests WHERE status = 'Approved'")
        total_volume = cursor.fetchone()[0] or 0.0

        conn.close()
        return total, avg_p, successful, int(total_volume)
    except Exception as e:
        print(f"🚨 Ошибка чтения метрик из БД: {e}")
        return 0, 0.0, 0, 0


def generate_excel_report():
    if not os.path.exists(DB_PATH):
        return None
    try:
        conn = sqlite3.connect(DB_PATH)
        # Выгружаем всю историю сделок, свежие — вверху
        df = pd.read_sql_query("SELECT * FROM tire_requests ORDER BY timestamp DESC", conn)
        conn.close()

        # Красиво переименуем колонки для Ивана, чтобы отчет в Excel на Poco Pad выглядел солидно
        df.columns = [
            "ID Сделки", "ID Пользователя", "Дата и Время", "Бренд",
            "Размер шины", "Возраст (лет)", "Протектор (мм)",
            "Цена выкупа (₽)", "Статус лота", "Источник (Фото/Ввод)"
        ]

        # Защита пути: проверяем существование папки /data (или той, что в config) перед записью excel
        excel_dir = os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else "data"
        os.makedirs(excel_dir, exist_ok=True)

        excel_filename = os.path.join(excel_dir, "Статистика_подбора_TyreXpert.xlsx")

        # Записываем честный красивый .xlsx файл через Pandas
        df.to_excel(excel_filename, index=False)
        return excel_filename
    except Exception as e:
        print(f"🚨 Ошибка генерации Excel-файла через Pandas: {e}")
        return None
