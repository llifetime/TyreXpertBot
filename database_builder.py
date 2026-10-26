import json
import time
import requests

# Официальная конечная точка бесплатного API CarQuery
API_URL = "https://carqueryapi.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


def get_carquery_data(cmd_params):
    """Отправляет запрос к CarQuery API и возвращает чистый JSON"""
    try:
        response = requests.get(API_URL, params=cmd_params, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            # API CarQuery по умолчанию может возвращать данные с оборачиванием в JSONP,
            # очищаем строку до чистого JSON-формата, если это необходимо
            text_data = response.text
            if text_data.startswith("?("):
                text_data = text_data[2:-2]
            return json.loads(text_data)
    except Exception as e:
        print(f"❌ Ошибка запроса к API: {e}")
    return None


def build_global_car_database():
    print("🚀 Запуск глобального сборщика колесной базы через CarQuery API...")

    # 1. Запрашиваем список всех мировых производителей
    print("⏳ Получаем список автопроизводителей...")
    makes_res = get_carquery_data({"cmd": "getMakes", "sold_in_us": "0"})

    if not makes_res or 'Makes' not in makes_res:
        print("❌ Не удалось получить список марок. Проверьте интернет-соединение.")
        return

    makes_list = makes_res['Makes']
    print(f"✅ Успешно найдено марок авто: {len(makes_list)}")

    tire_to_car_map = {}
    count = 0

    # Перебираем каждого производителя (Toyota, Nissan, Chrysler, Pontiac и т.д.)
    for make_item in makes_list:
        count += 1
        make_id = make_item.get('make_id')
        make_display = make_item.get('make_display')

        print(f"📦 [{count}/{len(makes_list)}] Обрабатываем модели бренда: {make_display.upper()}...")

        # 2. Запрашиваем все модели и модификации этой марки с 1990 года
        models_data = get_carquery_data({
            "cmd": "getTrims",
            "make": make_id,
            "min_year": "1990",
            "max_year": "2026"
        })

        if not models_data or 'Trims' not in models_data:
            time.sleep(0.5)
            continue

        for trim in models_data['Trims']:
            # Собираем красивую строку машины (например, "Chrysler New Yorker (1994)")
            car_year = trim.get('model_year', '')
            car_model = trim.get('model_name', '')
            car_trim = trim.get('model_trim', '')

            car_full_name = f"{make_display} {car_model}"
            if car_trim:
                car_full_name += f" {car_trim}"
            if car_year:
                car_full_name += f" ({car_year})"

            # 3. Вытаскиваем параметры оригинального размера шин (OE)
            # В CarQuery колеса часто лежат в параметрах ширины, профиля и диаметра
            tire_w = trim.get('model_tire_w', '')  # Например, "215"
            tire_p = trim.get('model_tire_p', '')  # Например, "65"
            tire_r = trim.get('model_wheel_r', '')  # Например, "17"

            if tire_w and tire_p and tire_r:
                # Приводим к нашему стандарту бота: "215/65 R17"
                formatted_size = f"{tire_w}/{tire_p} R{tire_r}"

                if formatted_size not in tire_to_car_map:
                    tire_to_car_map[formatted_size] = []

                if car_full_name not in tire_to_car_map[formatted_size]:
                    tire_to_car_map[formatted_size].append(car_full_name)

        # Небольшая пауза, чтобы не наглеть
        time.sleep(0.5)

        # Сохраняем кэш базы на каждом шаге, чтобы видеть прогресс
        with open('car_base.json', 'w', encoding='utf-8') as f:
            json.dump(tire_to_car_map, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 ГЛОБАЛЬНЫЙ СПРАВОЧНИК УСПЕШНО СОБРАН в car_base.json!")
    print(f"Всего уникальных размеров в вашей новой базе: {len(tire_to_car_map)}")


if __name__ == "__main__":
    build_global_car_database()
