import configparser
import logging
from pathlib import Path
from smotrim_parser import get_episodes

# Заглушки для будущих модулей
# from audio_downloader import AudioDownloader
# from telegram_bot import TelegramAudioBot
# from file_manager import FileManager

CONFIG_PATH = 'config.ini'


def load_config(path=CONFIG_PATH):
    config = configparser.ConfigParser()
    config.read(path, encoding='utf-8')
    return config


def main():
    logging.basicConfig(level=logging.INFO)
    config = load_config()
    logging.info('Конфиг загружен')
    
    # Получить список новых выпусков
    episodes = get_episodes(min_episode_number=38)
    logging.info(f'Найдено {len(episodes)} выпусков')
    for episode in episodes[:3]:  # Показываем первые 3 для проверки
        logging.info(f'Выпуск: {episode["title"]} ({episode["date"]}) - {episode["audio_url"]}')
    
    # TODO: Скачать аудиофайл
    # TODO: Сжать аудиофайл при необходимости
    # TODO: Отправить в Telegram
    # TODO: Очистить временные файлы
    logging.info('Парсер завершил работу')


if __name__ == '__main__':
    main() 