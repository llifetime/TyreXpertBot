import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


# =====================================================================
# 1. АДАПТЕР СТРУКТУРЫ: Переворачиваем плоскую базу в древовидную для кнопок
# =====================================================================

def load_car_base():
    """Загружает плоский car_base.json и налету перестраивает в древовидную структуру"""
    try:
        with open("car_base.json", "r", encoding="utf-8") as f:
            flat_db = json.load(f)
    except Exception as e:
        print(f"🚨 Ошибка чтения файла car_base.json: {e}")
        return {}

    # Сюда соберем дерево: { brand_id: { "name": ..., "models": { model_id: [размеры] } } }
    tree_db = {}

    for tire_size, car_strings in flat_db.items():
        for car_str in car_strings:
            # Очищаем строку от мусора (например, "Chrysler 300, размер колёс...")
            clean_str = car_str.split(",")[0].strip()  # Получаем "Chrysler 300"
            words = clean_str.split(" ")

            if len(words) >= 1:
                brand_name = words[0].strip()  # "Chrysler"
                model_name = " ".join(words[1:]).strip() if len(words) > 1 else "General"  # "300"

                brand_id = brand_name.lower().replace(" ", "_")
                model_id = model_name.lower().replace(" ", "_")

                # Заполняем дерево брендов
                if brand_id not in tree_db:
                    tree_db[brand_id] = {"name": brand_name, "models": {}}

                # Заполняем модели и привязываем к ним размеры
                if model_id not in tree_db[brand_id]["models"]:
                    tree_db[brand_id]["models"][model_id] = []

                if tire_size not in tree_db[brand_id]["models"][model_id]:
                    tree_db[brand_id]["models"][model_id].append(tire_size)

    return tree_db


# =====================================================================
# 2. МОДЕРНИЗИРОВАННЫЙ БЛОК ТВОИХ КЛАВИАТУР ПОДБОРА ПО АВТО
# =====================================================================

def get_brands_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    car_db = load_car_base()

    for brand_id, brand_data in car_db.items():
        markup.add(InlineKeyboardButton(brand_data["name"], callback_data=f"carbrand_{brand_id}"))
    markup.add(InlineKeyboardButton("🔙 В главное меню", callback_data="error_retry_manual"))
    return markup


def get_models_keyboard(brand_id):
    markup = InlineKeyboardMarkup(row_width=2)
    car_db = load_car_base()

    if brand_id in car_db:
        for model_id in car_db[brand_id]["models"].keys():
            markup.add(InlineKeyboardButton(model_id.upper().replace("_", " "),
                                            callback_data=f"carmodel_{brand_id}_{model_id}"))
    markup.add(InlineKeyboardButton("🔙 К маркам машин", callback_data="car_model_flow"))
    return markup


def get_car_specs(brand_id, model_id):
    car_db = load_car_base()
    try:
        return car_db[brand_id]["models"][model_id]
    except Exception:
        return None


# =====================================================================
# 3. АНАЛИЗАТОР ЛИКВИДНОСТИ: Работает на основе реального car_base.json
# =====================================================================

def get_liquidity_data(tire_size):
    """Динамически вычисляет ликвидность на основе количества машин в car_base.json"""
    tire_size = tire_size.strip()

    try:
        with open("car_base.json", "r", encoding="utf-8") as f:
            flat_db = json.load(f)

        if tire_size in flat_db:
            applicable_cars = flat_db[tire_size]
            # Очищаем названия для красивого вывода в чат
            clean_car_names = [c.split(",")[0].strip() for c in applicable_cars]
            car_count = len(clean_car_names)

            # Если размер массовый и идет более чем на 3 модификации
            if car_count >= 3:
                return 1.2, clean_car_names, "ВЫСОКАЯ ЛИКВИДНОСТЬ (очень ходовой размер)"
            else:
                return 1.0, clean_car_names, "Средняя ликвидность (стандартный спрос)"
    except Exception:
        pass

    return 0.75, [], "Низкая ликвидность (экзотический или редкий размер)"


# =====================================================================
# 4. ЭКСПЕРТНЫЙ РАСЧЕТ: Математика, вилки, границы износа и дефекты
# =====================================================================

def calculate_tire_valuation(base_new_price, brand, protector, age, tire_size, defects=None):
    if defects is None:
        defects = []

    # --- ЖЕСТКИЕ ГРАНИЦЫ ИЗНОСА И ВОЗРАСТА ---
    if protector < 4.0:
        return {
            "success": False,
            "message": f"❌ **Скупка отклонена!**\n\nПротектор резины составляет **{protector} мм** (ниже лимита в 4 мм). Резина считается сильно изношенной и небезопасной."
        }

    if age > 5:
        return {
            "success": False,
            "message": f"❌ **Скупка отклонена!**\n\nДата изготовления критична: шине уже **{age} лет**. Срок безопасной эксплуатации (5 лет) превышен, резина имеет высокий риск расслоения."
        }

    # Понижающие коэффициенты износа протектора
    if 4.0 <= protector <= 5.9:
        prog_mult = 0.65
    elif 6.0 <= protector <= 6.9:
        prog_mult = 0.85
    else:
        prog_mult = 1.0

    age_mult = 0.8 if age >= 3 else 1.0

    # Получаем реальную ликвидность из car_base.json
    liq_mult, cars, liq_status = get_liquidity_data(tire_size)

    # Оценка дефектов шин по степеням изменения свойств резины
    defect_mult = 1.0
    for defect in defects:
        def_lower = defect.lower().strip()
        if def_lower in ['мелкие царапины', 'косметика', 'микротрещины']:
            defect_mult *= 0.90
        elif def_lower in ['один жгут', 'латка', 'грибок']:
            defect_mult *= 0.75
        elif def_lower in ['боковой порез', 'грыжа', 'шишка', 'вздутие']:
            return {
                "success": False,
                "message": f"❌ **Скупка отклонена!**\n\nОбнаружен критический дефект шины: **{defect}**. Изменение свойств резины критично для безопасности."
            }

    def run_calc(b_mult):
        market_used_price = base_new_price * 0.60 * b_mult
        final_sale = market_used_price * prog_mult * age_mult * liq_mult * defect_mult
        return int(final_sale * 0.7), int(final_sale * 0.9)

    # --- РАЗГРАНИЧЕНИЕ ПО БРЕНДАМ И ВИЛКА ЦЕН ---
    brand_classes = {
        'michelin': 1.3, 'continental': 1.3, 'bridgestone': 1.3, 'hankook': 1.3,
        'pirelli': 1.0, 'nokian': 1.0, 'ikon': 1.0, 'yokohama': 1.0,
        'cordiant': 0.6, 'viatti': 0.6, 'kama': 0.6, 'кама': 0.6
    }

    if isinstance(brand, list):
        brand_name = brand[0].lower().strip() if brand else "не указан"
    else:
        brand_name = str(brand).lower().strip()

    car_info = f"🚘 Подходит на авто: {', '.join(cars[:3])}" if cars else "🚘 Специфический/редкий размер для РФ."

    if brand_name in ["не указан", "", "unknown", "пропустить"]:
        min_buy, _ = run_calc(0.6)
        _, max_buy = run_calc(1.3)

        return {
            "success": True,
            "message": f"🔍 **Предварительный расчет (Бренд не указан)**\n"
                       f"Размер: <code>{tire_size}</code>\n"
                       f"Ликвидность: {liq_status}\n"
                       f"{car_info}\n\n"
                       f"💰 **Вилка цены скупки:** {min_buy} - {max_buy} руб.\n\n"
                       f"⚠️ *Точная цена зависит от бренда. Назовите бренд у капота для точной оценки.*"
        }

    brand_mult = brand_classes.get(brand_name, 1.0)
    buy_min, buy_max = run_calc(brand_mult)

    return {
        "success": True,
        "message": f"✅ **Оценка шин успешно произведена**\n"
                   f"Бренд: <b>{brand_name.capitalize()}</b>\n"
                   f"Размер: <code>{tire_size}</code> ({liq_status})\n"
                   f"{car_info}\n\n"
                   f"💰 **Вилка скупки за комплект:** {buy_min} - {buy_max} руб."
    }


def calculate_wheel_valuation(diameter, wheel_type, defects=None):
    if defects is None:
        defects = []

    type_base_rates = {
        'ковка': 2500, 'оригинал': 1800, 'реплика': 1000, 'китай': 700
    }

    w_type = wheel_type.lower().strip()
    base_rate = type_base_rates.get(w_type, 800)
    initial_price = base_rate * diameter

    defect_mult = 1.0
    for defect in defects:
        def_lower = defect.lower().strip()
        if def_lower in ['бордюрка', 'царапины', 'сколы']:
            defect_mult *= 0.85
        elif def_lower in ['требует прокатки', 'осевое биение', 'восьмерка']:
            defect_mult *= 0.60
        elif def_lower in ['трещина', 'сварка', 'аргон', 'яйцо', 'радиальное биение']:
            return {
                "success": False,
                "message": f"❌ **Скупка дисков отклонена!**\n\nОбнаружен критический дефект металла: **{defect}**. Выкуп невозможен."
            }

    final_wheel_price = initial_price * defect_mult
    return {
        "success": True,
        "message": f"⚙️ **Оценка дисков**\nТип: {wheel_type.capitalize()}\nДиаметр: R{diameter}\n\n💰 **Вилка скупки дисков:** {int(final_wheel_price * 0.7)} - {int(final_wheel_price * 0.9)} руб."
    }
