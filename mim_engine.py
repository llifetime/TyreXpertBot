import json
import re

def parse_tire_size(text):
    # Ищем группы цифр в тексте пользователя
    matches = re.findall(r'\d+', text)
    if len(matches) >= 3:
        width = matches[0]
        profile = matches[1]
        radius = matches[2]
        return f"{width}/{profile} R{radius}", int(radius)
    # ИСПРАВЛЕНИЕ: Никакого хардкода! Возвращаем пустоту, если ввод неверный
    return None, None


def check_mim_has_multiwide(radius):
    try:
        with open("price_cache.json", "r", encoding="utf-8") as f:
            cache = json.load(f)
        for key in cache.keys():
            if f"R{radius}" in key and any(w in key.lower() for w in ["перед", "зад", "комплект"]):
                return True
    except Exception:
        pass
    return radius >= 18

def get_average_mim_price(radius):
    try:
        with open("price_cache.json", "r", encoding="utf-8") as f:
            cache = json.load(f)
        prices = []
        for key, price in cache.items():
            if f"R{radius}" in key:
                prices.append(price)
        if prices:
            return int(sum(prices) / len(prices))
    except Exception:
        pass
    return 3500 + (radius - 13) * 1500
