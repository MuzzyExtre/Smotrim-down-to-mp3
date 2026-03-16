import requests
import json
import logging

logging.basicConfig(level=logging.INFO)

def test_api():
    """Тестируем различные варианты API запросов"""
    
    # Вариант 1: Прямой API запрос
    url1 = 'https://smotrim.ru/api/audios'
    params1 = {'page': 1, 'rubricId': '7741'}
    
    logging.info(f"Тест 1: {url1} с параметрами {params1}")
    try:
        resp1 = requests.get(url1, params=params1)
        logging.info(f"Статус: {resp1.status_code}")
        logging.info(f"Заголовки: {dict(resp1.headers)}")
        logging.info(f"Ответ: {resp1.text[:500]}...")
    except Exception as e:
        logging.error(f"Ошибка: {e}")
    
    # Вариант 2: С заголовками браузера
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
        'Referer': 'https://smotrim.ru/podcast/7741'
    }
    
    logging.info(f"\nТест 2: С заголовками браузера")
    try:
        resp2 = requests.get(url1, params=params1, headers=headers)
        logging.info(f"Статус: {resp2.status_code}")
        logging.info(f"Ответ: {resp2.text[:500]}...")
    except Exception as e:
        logging.error(f"Ошибка: {e}")
    
    # Вариант 3: Другой формат API
    url3 = 'https://smotrim.ru/api/audios?page=1&rubricId=7741'
    logging.info(f"\nТест 3: {url3}")
    try:
        resp3 = requests.get(url3, headers=headers)
        logging.info(f"Статус: {resp3.status_code}")
        logging.info(f"Ответ: {resp3.text[:500]}...")
    except Exception as e:
        logging.error(f"Ошибка: {e}")

if __name__ == '__main__':
    test_api() 