import requests
from bs4 import BeautifulSoup
import logging
import json

logging.basicConfig(level=logging.INFO)

def debug_site_structure():
    """Изучаем реальную структуру сайта smotrim.ru"""
    url = 'https://smotrim.ru/podcast/7741'
    logging.info(f"Загружаем страницу: {url}")
    
    resp = requests.get(url)
    if resp.status_code != 200:
        logging.error(f"Ошибка загрузки: {resp.status_code}")
        return
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Ищем кнопку "Показать еще"
    logging.info("=== Анализ кнопки 'Показать еще' ===")
    more_btn = soup.select_one('.section__link--more')
    if more_btn:
        logging.info(f"Найдена кнопка 'Показать еще': {more_btn}")
        # Ищем data-атрибуты
        for attr, value in more_btn.attrs.items():
            logging.info(f"  {attr}: {value}")
    else:
        logging.info("Кнопка 'Показать еще' не найдена")
    
    # Ищем скрипты с API
    logging.info("\n=== Поиск API запросов ===")
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string and ('api' in script.string.lower() or 'ajax' in script.string.lower()):
            logging.info(f"Найден скрипт с API: {script.string[:200]}...")
    
    # Ищем все возможные контейнеры с выпусками
    logging.info("\n=== Поиск контейнеров с выпусками ===")
    
    # Попробуем разные селекторы
    selectors = [
        '.list-item',
        '.podcast-episode',
        '.episode',
        '.podcast-item',
        '.item',
        '[class*="episode"]',
        '[class*="podcast"]',
        'article',
        '.content-item'
    ]
    
    for selector in selectors:
        items = soup.select(selector)
        logging.info(f"Селектор '{selector}': найдено {len(items)} элементов")
        if items:
            logging.info(f"  Первый элемент: {items[0]}")
    
    # Ищем ссылки на аудио
    logging.info("\n=== Поиск ссылок на аудио ===")
    audio_links = soup.find_all('a', href=True)
    for link in audio_links[:10]:  # Первые 10 ссылок
        href = link.get('href')
        if href and ('audio' in str(href) or 'listen' in str(href)):
            logging.info(f"Найдена аудио ссылка: {href}")
    
    # Ищем заголовки
    logging.info("\n=== Поиск заголовков ===")
    titles = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    for title in titles[:5]:
        logging.info(f"Заголовок: {title.get_text(strip=True)}")
    
    # Сохраняем HTML для анализа
    with open('debug_page.html', 'w', encoding='utf-8') as f:
        f.write(str(soup.prettify()))
    logging.info("HTML сохранен в debug_page.html")

if __name__ == '__main__':
    debug_site_structure() 