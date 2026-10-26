import os
from dotenv import load_dotenv  # Оставили строго нужный импорт

# Загружаем переменные из локального файла .env
load_dotenv()

# os.getenv читает переменные окружения из .env (или настройки Amvera на сервере)
TOKEN = os.getenv("TOKEN")
MY_TELEGRAM_ID = os.getenv("MY_TELEGRAM_ID")

# Безопасно переводим ID в число
if MY_TELEGRAM_ID:
    MY_TELEGRAM_ID = int(MY_TELEGRAM_ID)
else:
    MY_TELEGRAM_ID = 0

DATASET_DIR = "data"
DB_PATH = "data/valuation.db"
