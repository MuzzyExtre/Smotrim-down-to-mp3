import requests
from bs4 import BeautifulSoup
import logging
import time
import re
import json
from colorama import init, Fore, Back, Style
import os
from pathlib import Path
import configparser
import ffmpeg
from datetime import datetime

# Настройка логирования
def setup_logging():
    """Настраивает систему логирования"""
    try:
        # Получаем настройки логирования из конфигурации
        log_level = config.get('logging', 'log_level', fallback='INFO')
        save_logs = config.getboolean('logging', 'save_logs', fallback=True)
    except:
        # Если не удалось прочитать конфигурацию, используем значения по умолчанию
        log_level = 'INFO'
        save_logs = True
    
    # Преобразуем строку уровня логирования в константу
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    log_level = level_map.get(log_level.upper(), logging.INFO)
    
    # Создаем папку для логов если её нет
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Простое имя файла лога
    log_filename = "logs/smotrim_parser.log"
    
    # Настраиваем обработчики
    handlers = []
    handlers.append(logging.StreamHandler())  # Всегда выводим в консоль
    
    if save_logs:
        # Простой файловый обработчик
        file_handler = logging.FileHandler(log_filename, encoding='utf-8', mode='a')
        handlers.append(file_handler)
    
    # Настраиваем логирование
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    return logging.getLogger(__name__)

# Инициализируем логгер
logger = setup_logging()

# Инициализация colorama для Windows
init(autoreset=True)

# Загружаем конфигурацию
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

# Получаем пути к FFmpeg из конфигурации
def get_ffmpeg_config_path():
    """Получает путь к ffmpeg из конфигурации"""
    try:
        ffmpeg_path = config.get('ffmpeg', 'ffmpeg_path', fallback='')
        if ffmpeg_path:
            return ffmpeg_path
    except:
        pass
    return None

def get_ffprobe_config_path():
    """Получает путь к ffprobe из конфигурации"""
    try:
        ffprobe_path = config.get('ffmpeg', 'ffprobe_path', fallback='')
        if ffprobe_path:
            return ffprobe_path
    except:
        pass
    return None

# Настраиваем ffmpeg-python для использования наших путей
import subprocess
import shutil

def get_ffmpeg_path():
    """Возвращает путь к ffmpeg, проверяя сначала конфигурацию, потом локальные файлы, потом системный PATH"""
    # 1. Проверяем путь из конфигурации
    config_path = get_ffmpeg_config_path()
    if config_path and os.path.exists(config_path):
        logger.info(f"Используем FFmpeg из конфигурации: {config_path}")
        return config_path
    
    # 2. Проверяем локальные файлы (в той же папке что и EXE)
    local_paths = ["ffmpeg.exe", "./ffmpeg.exe", "ffmpeg", "./ffmpeg"]
    for local_path in local_paths:
        if os.path.exists(local_path):
            logger.info(f"Используем локальный FFmpeg: {local_path}")
            return local_path
    
    # 3. Проверяем системный PATH
    system_path = shutil.which('ffmpeg')
    if system_path:
        logger.info(f"Используем системный FFmpeg: {system_path}")
        return system_path
    
    # 4. Если ничего не найдено
    logger.error("FFmpeg не найден ни в конфигурации, ни локально, ни в системном PATH")
    raise FileNotFoundError("FFmpeg не найден. Установите FFmpeg или укажите путь в config.ini")

def get_ffprobe_path():
    """Возвращает путь к ffprobe, проверяя сначала конфигурацию, потом локальные файлы, потом системный PATH"""
    # 1. Проверяем путь из конфигурации
    config_path = get_ffprobe_config_path()
    if config_path and os.path.exists(config_path):
        logger.info(f"Используем FFprobe из конфигурации: {config_path}")
        return config_path
    
    # 2. Проверяем локальные файлы (в той же папке что и EXE)
    local_paths = ["ffprobe.exe", "./ffprobe.exe", "ffprobe", "./ffprobe"]
    for local_path in local_paths:
        if os.path.exists(local_path):
            logger.info(f"Используем локальный FFprobe: {local_path}")
            return local_path
    
    # 3. Проверяем системный PATH
    system_path = shutil.which('ffprobe')
    if system_path:
        logger.info(f"Используем системный FFprobe: {system_path}")
        return system_path
    
    # 4. Если ничего не найдено
    logger.error("FFprobe не найден ни в конфигурации, ни локально, ни в системном PATH")
    raise FileNotFoundError("FFprobe не найден. Установите FFmpeg или укажите путь в config.ini")

# Переопределяем функции ffmpeg для использования наших путей
def custom_ffmpeg_run(stream, **kwargs):
    """Кастомная функция для запуска ffmpeg с нашим путем"""
    ffmpeg_path = get_ffmpeg_path()
    if ffmpeg_path is None:
        raise FileNotFoundError("FFmpeg не найден")
    cmd = ffmpeg.compile(stream, cmd=ffmpeg_path)
    
    # Добавляем флаг -y для автоматической перезаписи
    if isinstance(cmd, list):
        cmd.insert(1, '-y')  # Вставляем -y после ffmpeg
    else:
        cmd = [cmd[0], '-y'] + cmd[1:]  # Для строки команды
    
    # Убираем неподдерживаемые аргументы
    run_kwargs = {}
    if 'quiet' in kwargs:
        del kwargs['quiet']
    if 'overwrite_output' in kwargs:
        del kwargs['overwrite_output']
    
    return subprocess.run(cmd, **kwargs)

def custom_ffmpeg_probe(filename, **kwargs):
    """Кастомная функция для probe с нашим путем"""
    ffprobe_path = get_ffprobe_path()
    if ffprobe_path is None:
        raise FileNotFoundError("FFprobe не найден")
    cmd = [ffprobe_path, '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', filename]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

BASE_URL = 'https://smotrim.ru/podcast/7741'
API_URL = 'https://smotrim.ru/api/audios'
EPISODE_AUDIO_URL = 'https://vgtrk-podcast.cdnvideo.ru/audio/listen?id={}'


def print_header():
    """Выводит красивый заголовок"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}🎧 ПАРСЕР ПОДКАСТА 'ПРОВОКАЦИЯ' 🎧")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    logger.info("Парсер подкаста 'Провокация' запущен")


def print_episode_info(episode, index):
    """Красиво выводит информацию о выпуске"""
    episode_num = episode.get('episode_number', 'N/A')
    title = episode.get('title', 'Без названия')
    date = episode.get('date', 'Дата не указана')
    audio_url = episode.get('audio_url', '')
    
    print(f"{Fore.GREEN}📻 Выпуск #{episode_num:2d} {Fore.YELLOW}({date})")
    print(f"{Fore.WHITE}   Название: {title}")
    print(f"{Fore.BLUE}   Ссылка: {audio_url}")
    print(f"{Fore.CYAN}{'─'*50}{Style.RESET_ALL}")


def print_progress(current, total, page):
    """Выводит прогресс парсинга"""
    progress = (current / total) * 100 if total > 0 else 0
    bar_length = 30
    filled_length = int(bar_length * current // total) if total > 0 else 0
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    print(f"\n{Fore.MAGENTA}📊 Прогресс: [{bar}] {progress:.1f}% ({current}/{total})")
    print(f"{Fore.CYAN}📄 Страница: {page}{Style.RESET_ALL}")


def print_summary(episodes, min_episode):
    """Выводит итоговую сводку"""
    print(f"\n{Fore.GREEN}{'='*60}")
    print(f"{Fore.GREEN}✅ ПАРСИНГ ЗАВЕРШЕН")
    print(f"{Fore.GREEN}{'='*60}")
    print(f"{Fore.YELLOW}📈 Статистика:")
    print(f"{Fore.WHITE}   • Всего найдено выпусков: {len(episodes)}")
    print(f"{Fore.WHITE}   • Начиная с выпуска: #{min_episode}")
    print(f"{Fore.WHITE}   • Диапазон выпусков: #{min_episode} - #{max([e.get('episode_number', 0) for e in episodes]) if episodes else 'N/A'}")
    print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")


def get_episodes(min_episode_number=38, delay=2):
    """
    Парсит выпуски подкаста через API, начиная с min_episode_number.
    Возвращает список словарей: {'id', 'title', 'date', 'audio_url', 'episode_number'}
    """
    print_header()
    
    episodes = []
    page = 1
    seen_ids = set()
    total_processed = 0
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
        'Referer': 'https://smotrim.ru/podcast/7741'
    }
    
    print(f"{Fore.CYAN}🔍 Начинаем парсинг с выпуска #{min_episode_number}...{Style.RESET_ALL}\n")
    
    while True:
        # Используем API для получения выпусков
        api_params = {
            'page': page,
            'rubricId': '7741'
        }
        
        print(f"{Fore.BLUE}📡 Загружаем страницу {page} через API...{Style.RESET_ALL}")
        
        try:
            resp = requests.get(API_URL, params=api_params, headers=headers)
            if resp.status_code != 200:
                print(f"{Fore.RED}❌ Ошибка API запроса: {resp.status_code}{Style.RESET_ALL}")
                break
                
            data = resp.json()
            
            # Проверяем структуру ответа
            if 'contents' not in data or not data['contents']:
                print(f"{Fore.YELLOW}⚠️  Нет данных в ответе API{Style.RESET_ALL}")
                break
                
            content = data['contents'][0]
            if 'list' not in content:
                print(f"{Fore.YELLOW}⚠️  Нет списка выпусков в ответе{Style.RESET_ALL}")
                break
                
            items = content['list']
            if not items:
                print(f"{Fore.YELLOW}📭 Больше выпусков нет{Style.RESET_ALL}")
                break
                
            print(f"{Fore.GREEN}✅ Получено {len(items)} выпусков с API{Style.RESET_ALL}")
            
            page_episodes = 0
            for item in items:
                try:
                    episode_id = str(item.get('id'))
                    if not episode_id or episode_id in seen_ids:
                        continue
                    seen_ids.add(episode_id)

                    anons = item.get('anons', '')
                    episode_match = re.search(r'Выпуск\s*#?(\d+)', anons)
                    if not episode_match:
                        continue
                    episode_num = int(episode_match.group(1))
                    if episode_num < min_episode_number:
                        continue

                    title = item.get('title', f"Выпуск #{episode_num}")
                    date = item.get('published', 'Дата не указана')
                    audio_url = EPISODE_AUDIO_URL.format(episode_id)

                    episode_data = {
                        'id': episode_id,
                        'title': title,
                        'date': date,
                        'audio_url': audio_url,
                        'episode_number': episode_num
                    }
                    episodes.append(episode_data)
                    page_episodes += 1
                    total_processed += 1
                    
                    # Выводим информацию о найденном выпуске
                    print_episode_info(episode_data, total_processed)
                    
                except Exception as e:
                    print(f"{Fore.RED}❌ Ошибка обработки выпуска: {e}{Style.RESET_ALL}")
            
            if page_episodes > 0:
                print(f"{Fore.GREEN}📊 На странице {page} найдено {page_episodes} подходящих выпусков{Style.RESET_ALL}")
            
            # Проверяем, есть ли еще страницы
            content_control = content.get('contentControl')
            if not content_control or not isinstance(content_control, dict):
                print(f"{Fore.YELLOW}📄 Достигнут конец списка{Style.RESET_ALL}")
                break
            more_info = content_control.get('more')
            if not more_info or not isinstance(more_info, dict) or not more_info.get('url'):
                print(f"{Fore.YELLOW}📄 Больше страниц нет{Style.RESET_ALL}")
                break
            page += 1
            time.sleep(delay)
            
        except Exception as e:
            print(f"{Fore.RED}❌ Ошибка API запроса: {e}{Style.RESET_ALL}")
            break
    
    print_summary(episodes, min_episode_number)
    return episodes


def download_audio(episode, dest_folder="downloads", max_retries=None):
    """
    Скачивает аудиофайл по ссылке из episode['audio_url'] в папку dest_folder.
    Возвращает путь к файлу или None в случае ошибки.
    Повторяет попытки до успешного скачивания.
    """
    from colorama import Fore, Style
    import os
    os.makedirs(dest_folder, exist_ok=True)
    episode_num = episode.get('episode_number', 'N/A')
    title = episode.get('title', 'Провокация')
    # Формируем имя файла
    safe_title = re.sub(r'[^\w\d_\-]', '_', title)
    filename = f"{safe_title}_Выпуск_{episode_num}.mp3"
    filepath = os.path.join(dest_folder, filename)
    url = episode.get('audio_url')
    if not url:
        print(f"{Fore.RED}❌ Нет ссылки для скачивания у выпуска #{episode_num}{Style.RESET_ALL}")
        return None
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'audio',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'cross-site'
    }
    
    # Настройки сессии для более стабильного соединения
    session = requests.Session()
    session.headers.update(headers)
    
    attempt = 0
    while True:  # Бесконечные повторные попытки
        attempt += 1
        try:
            print(f"{Fore.CYAN}⬇️  Скачиваем: {filename} (попытка {attempt}){Style.RESET_ALL}")
            
            # Увеличенные таймауты
            resp = session.get(url, stream=True, timeout=(60, 600))  # (connect_timeout, read_timeout) - 1 минута на подключение, 10 минут на чтение
            
            if resp.status_code != 200:
                print(f"{Fore.RED}❌ Ошибка скачивания ({resp.status_code}): {url}{Style.RESET_ALL}")
                delay = 10 + (attempt * 5)
                print(f"{Fore.YELLOW}🔄 Повторная попытка через {delay} секунд...{Style.RESET_ALL}")
                time.sleep(delay)
                continue
            
            total = int(resp.headers.get('content-length', 0))
            
            # Улучшенное скачивание с обработкой IncompleteRead
            with open(filepath, 'wb') as f:
                downloaded = 0
                chunk_size = 8192  # Оптимальный размер чанка
                
                try:
                    for chunk in resp.iter_content(chunk_size=chunk_size):
                        if chunk:  # фильтруем keep-alive новые строки
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total:
                                done = int(30 * downloaded / total)
                                bar = '█' * done + '░' * (30 - done)
                                print(f"\r{Fore.MAGENTA}[{bar}] {downloaded//1024} KB / {total//1024} KB", end='')
                    print()
                    
                except requests.exceptions.ChunkedEncodingError as e:
                    print(f"{Fore.YELLOW}⚠️  Ошибка кодирования чанков: {e}{Style.RESET_ALL}")
                    # Всегда повторяем попытку при ошибках кодирования
                    raise e
                
                except Exception as e:
                    if "IncompleteRead" in str(e) or "Connection broken" in str(e):
                        print(f"{Fore.YELLOW}⚠️  Соединение прервано: {e}{Style.RESET_ALL}")
                        # Всегда повторяем попытку при прерывании соединения
                        raise e
                    else:
                        raise e
            
            # Проверяем, что файл скачался полностью
            if total > 0:
                actual_size = os.path.getsize(filepath)
                if actual_size < total * 0.98:  # Допускаем только 2% погрешность
                    print(f"{Fore.YELLOW}⚠️  Файл скачан не полностью ({actual_size} из {total} байт), повторяем...{Style.RESET_ALL}")
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    delay = 10 + (attempt * 5)
                    print(f"{Fore.YELLOW}🔄 Повторная попытка через {delay} секунд...{Style.RESET_ALL}")
                    time.sleep(delay)
                    continue
                else:
                    print(f"{Fore.GREEN}✅ Скачано: {filepath} ({actual_size//1024//1024:.1f} МБ){Style.RESET_ALL}")
            else:
                # Если content-length не указан, проверяем минимальный размер
                actual_size = os.path.getsize(filepath)
                if actual_size < 1024:  # Минимум 1KB
                    print(f"{Fore.YELLOW}⚠️  Файл слишком маленький ({actual_size} байт), повторяем...{Style.RESET_ALL}")
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    delay = 10 + (attempt * 5)
                    print(f"{Fore.YELLOW}🔄 Повторная попытка через {delay} секунд...{Style.RESET_ALL}")
                    time.sleep(delay)
                    continue
                else:
                    print(f"{Fore.GREEN}✅ Скачано: {filepath} ({actual_size//1024//1024:.1f} МБ){Style.RESET_ALL}")
            
            return filepath
            
        except requests.exceptions.ConnectionError as e:
            print(f"{Fore.RED}❌ Ошибка соединения: {e}{Style.RESET_ALL}")
            if os.path.exists(filepath):
                os.remove(filepath)
            delay = 15 + (attempt * 5)
            print(f"{Fore.YELLOW}🔄 Повторная попытка через {delay} секунд...{Style.RESET_ALL}")
            time.sleep(delay)
            continue
            
        except requests.exceptions.Timeout as e:
            print(f"{Fore.RED}❌ Таймаут соединения: {e}{Style.RESET_ALL}")
            if os.path.exists(filepath):
                os.remove(filepath)
            delay = 20 + (attempt * 5)
            print(f"{Fore.YELLOW}🔄 Повторная попытка через {delay} секунд...{Style.RESET_ALL}")
            time.sleep(delay)
            continue
            
        except Exception as e:
            print(f"{Fore.RED}❌ Ошибка при скачивании: {e}{Style.RESET_ALL}")
            if os.path.exists(filepath):
                os.remove(filepath)
            delay = 10 + (attempt * 3)
            print(f"{Fore.YELLOW}🔄 Повторная попытка через {delay} секунд...{Style.RESET_ALL}")
            time.sleep(delay)
            continue
    
    return None


def compress_audio(input_path, output_path, target_size_mb=45):
    """
    Сжимает аудиофайл до размера меньше target_size_mb МБ используя FFmpeg.
    Возвращает True если сжатие успешно, False если не удалось.
    """
    from colorama import Fore, Style
    import os
    
    try:
        print(f"{Fore.YELLOW}🔧 Сжимаем файл: {os.path.basename(input_path)}{Style.RESET_ALL}")
        
        # Удаляем выходной файл, если он существует
        if os.path.exists(output_path):
            os.remove(output_path)
            print(f"{Fore.CYAN}🗑️  Удален существующий временный файл{Style.RESET_ALL}")
        
        # Получаем информацию о файле
        probe = custom_ffmpeg_probe(input_path)
        duration = float(probe['streams'][0]['duration'])
        current_size_mb = os.path.getsize(input_path) / (1024 * 1024)
        
        print(f"{Fore.CYAN}📊 Исходный размер: {current_size_mb:.1f} МБ{Style.RESET_ALL}")
        
        # Рассчитываем битрейт для целевого размера с большим запасом
        target_size_bytes = (target_size_mb - 3) * 1024 * 1024  # Запас 3 МБ
        target_bitrate = int((target_size_bytes * 8) / duration)  # битрейт в битах/сек
        
        # Ограничиваем битрейт разумными пределами
        target_bitrate = max(32000, min(target_bitrate, 320000))  # от 32 до 320 kbps
        
        print(f"{Fore.CYAN}🎵 Битрейт: {target_bitrate//1000} kbps{Style.RESET_ALL}")
        
        # Сжимаем файл
        stream = ffmpeg.input(input_path)
        stream = ffmpeg.output(stream, output_path, 
                             acodec='mp3', 
                             ab=target_bitrate,
                             ac=2,  # 2 канала
                             ar='44100')  # частота дискретизации
        
        custom_ffmpeg_run(stream, overwrite_output=True, quiet=True)
        
        # Проверяем результат
        compressed_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"{Fore.GREEN}✅ Сжато до: {compressed_size_mb:.1f} МБ{Style.RESET_ALL}")
        
        # Если файл все еще больше целевого размера, сжимаем еще больше
        if compressed_size_mb > target_size_mb:
            print(f"{Fore.YELLOW}⚠️  Файл все еще слишком большой, сжимаем еще больше...{Style.RESET_ALL}")
            
            # Удаляем текущий сжатый файл
            os.remove(output_path)
            
            # Сжимаем с еще меньшим битрейтом
            target_size_bytes = (target_size_mb - 2) * 1024 * 1024  # Запас 2 МБ
            target_bitrate = int((target_size_bytes * 8) / duration)
            target_bitrate = max(32000, min(target_bitrate, 320000))
            
            print(f"{Fore.CYAN}🎵 Новый битрейт: {target_bitrate//1000} kbps{Style.RESET_ALL}")
            
            stream = ffmpeg.input(input_path)
            stream = ffmpeg.output(stream, output_path, 
                                 acodec='mp3', 
                                 ab=target_bitrate,
                                 ac=2,
                                 ar='44100')
            
            custom_ffmpeg_run(stream, overwrite_output=True, quiet=True)
            
            compressed_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"{Fore.GREEN}✅ Финальное сжатие до: {compressed_size_mb:.1f} МБ{Style.RESET_ALL}")
        
        return True
        
    except Exception as e:
        print(f"{Fore.RED}❌ Ошибка сжатия: {e}{Style.RESET_ALL}")
        return False

def load_sent_episodes():
    """Загружает список уже отправленных выпусков из JSON файла"""
    sent_file = "sent_episodes.json"
    if os.path.exists(sent_file):
        try:
            with open(sent_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️  Ошибка загрузки списка отправленных: {e}{Style.RESET_ALL}")
    return []

def save_sent_episode(episode_num):
    """Сохраняет номер выпуска в список отправленных"""
    sent_file = "sent_episodes.json"
    sent_episodes = load_sent_episodes()
    
    if episode_num not in sent_episodes:
        sent_episodes.append(episode_num)
        try:
            with open(sent_file, 'w', encoding='utf-8') as f:
                json.dump(sent_episodes, f, indent=2, ensure_ascii=False)
            print(f"{Fore.GREEN}✅ Выпуск #{episode_num} добавлен в список отправленных{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Ошибка сохранения списка отправленных: {e}{Style.RESET_ALL}")

def is_episode_sent(episode_num):
    """Проверяет, был ли выпуск уже отправлен"""
    sent_episodes = load_sent_episodes()
    return episode_num in sent_episodes

def send_audio_to_telegram(filepath, episode, config, max_retries=None):
    """
    Отправляет аудиофайл в Telegram-канал через Bot API.
    Автоматически сжимает файлы больше 50 МБ.
    Повторяет попытки до успешной отправки.
    """
    from colorama import Fore, Style
    import requests
    import os
    import tempfile
    import time
    
    episode_num = episode.get('episode_number', 'N/A')
    
    # Проверяем, не был ли выпуск уже отправлен
    if is_episode_sent(episode_num):
        print(f"{Fore.YELLOW}⏭️  Выпуск #{episode_num} уже был отправлен, пропускаем{Style.RESET_ALL}")
        return True  # Возвращаем True, так как это не ошибка
    
    bot_token = config.get('telegram', 'bot_token').replace('"', '').strip()
    channel_id = config.get('telegram', 'channel_id').replace('"', '').strip()
    max_size_mb = int(config.get('audio', 'max_file_size_mb', fallback=50))
    filesize_mb = os.path.getsize(filepath) / (1024 * 1024)
    
    # Если файл больше лимита, сжимаем его
    if filesize_mb > max_size_mb:
        print(f"{Fore.YELLOW}⚠️  Файл {os.path.basename(filepath)} больше {max_size_mb} МБ, сжимаем...{Style.RESET_ALL}")
        
        # Создаем временный файл для сжатой версии
        temp_dir = tempfile.gettempdir()
        compressed_filename = f"compressed_{os.path.basename(filepath)}"
        compressed_path = os.path.join(temp_dir, compressed_filename)
        
        # Сжатие до 45 МБ для гарантии попадания в лимит Telegram (50 МБ)
        target_size = 45  # Фиксированный размер с большим запасом
        
        # Если файл очень большой, сжимаем еще больше
        if filesize_mb > 100:
            target_size = 40  # Для очень больших файлов сжимаем до 40 МБ
        
        if compress_audio(filepath, compressed_path, target_size_mb=target_size):
            filepath = compressed_path  # Используем сжатую версию
            filesize_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"{Fore.GREEN}✅ Файл сжат до {filesize_mb:.1f} МБ{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Не удалось сжать файл, пропускаем{Style.RESET_ALL}")
            return False
    
    # Всегда используем sendAudio для аудиофайлов
    url = f"https://api.telegram.org/bot{bot_token}/sendAudio"
    
    # Красивое форматирование
    date = episode.get('date', 'Дата не указана')
    title = f"Выпуск #{episode_num}"
    caption = f"""📅 <b>Дата:</b> {date}"""
    
    # Простые настройки для прямого API запроса
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # Отключаем предупреждения
    
    attempt = 0
    while True:  # Бесконечные повторные попытки
        attempt += 1
        try:
            print(f"{Fore.CYAN}🚀 Отправляю в Telegram: {title} (попытка {attempt}){Style.RESET_ALL}")
            
            # Прямой API запрос в Telegram (основной метод)
            with open(filepath, 'rb') as audio_file:
                files = {'audio': audio_file}
                data = {
                    'chat_id': channel_id,
                    'caption': caption,
                    'parse_mode': 'HTML',
                    'title': title,
                    'performer': 'Провокация'
                }
                
                # Используем максимально простые настройки для прямого API
                simple_session = requests.Session()
                simple_session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Connection': 'close',
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate'
                })
                
                # Отправляем с минимальными настройками и большим таймаутом
                resp = simple_session.post(
                    url,
                    data=data,
                    files=files,
                    timeout=1800,  # 30 минут для больших файлов
                    verify=False,
                    allow_redirects=False
                )
            
            if resp.status_code == 200:
                print(f"{Fore.GREEN}✅ Успешно отправлено в Telegram!{Style.RESET_ALL}")
                logger.info(f"Выпуск #{episode_num} успешно отправлен в Telegram")
                save_sent_episode(episode_num)
                
                # Удаляем временный сжатый файл
                if filepath != episode.get('original_filepath'):
                    try:
                        os.remove(filepath)
                        logger.info(f"Временный файл {os.path.basename(filepath)} удален")
                    except:
                        logger.warning(f"Не удалось удалить временный файл {os.path.basename(filepath)}")
                
                # Добавляем задержку после успешной отправки для ограничения скорости
                print(f"{Fore.CYAN}⏳ Пауза 10 секунд для стабилизации...{Style.RESET_ALL}")
                time.sleep(10)
                
                return True
            else:
                print(f"{Fore.RED}❌ Ошибка Telegram API: {resp.status_code} — {resp.text}{Style.RESET_ALL}")
                delay = 10 + (attempt * 5)
                print(f"{Fore.YELLOW}🔄 Повторная попытка через {delay} секунд...{Style.RESET_ALL}")
                time.sleep(delay)
                continue
                
        except requests.exceptions.Timeout as e:
            print(f"{Fore.RED}❌ Таймаут отправки в Telegram: {e}{Style.RESET_ALL}")
            delay = 30 + (attempt * 10)
            print(f"{Fore.YELLOW}🔄 Повторная попытка через {delay} секунд...{Style.RESET_ALL}")
            time.sleep(delay)
            continue
            
        except requests.exceptions.ConnectionError as e:
            print(f"{Fore.RED}❌ Ошибка соединения с Telegram: {e}{Style.RESET_ALL}")
            delay = 30 + (attempt * 10)
            print(f"{Fore.YELLOW}🔄 Повторная попытка через {delay} секунд...{Style.RESET_ALL}")
            time.sleep(delay)
            continue
            
        except Exception as e:
            print(f"{Fore.RED}❌ Ошибка отправки в Telegram: {e}{Style.RESET_ALL}")
            delay = 15 + (attempt * 5)
            print(f"{Fore.YELLOW}🔄 Повторная попытка через {delay} секунд...{Style.RESET_ALL}")
            time.sleep(delay)
            continue
    
    return False


if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Загрузка конфига
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    
    # Запуск парсера
    episodes = get_episodes(min_episode_number=38)
    
    # Выводим итоговый список
    if episodes:
        print(f"\n{Fore.CYAN}📋 ИТОГОВЫЙ СПИСОК ВЫПУСКОВ:{Style.RESET_ALL}")
        for i, episode in enumerate(episodes, 1):
            print(f"{Fore.WHITE}{i:2d}. {Fore.GREEN}Выпуск #{episode['episode_number']:2d} {Fore.YELLOW}({episode['date']})")
            print(f"{Fore.WHITE}    {episode['title']}")
            print(f"{Fore.BLUE}    {episode['audio_url']}")
            print()
        
        # Показываем статистику отправленных
        sent_episodes = load_sent_episodes()
        if sent_episodes:
            print(f"{Fore.CYAN}📊 Уже отправлено выпусков: {len(sent_episodes)}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📋 Список отправленных: {sorted(sent_episodes)}{Style.RESET_ALL}\n")
        
        # Скачиваем и отправляем все выпуски
        print(f"\n{Fore.CYAN}{'='*60}\n⬇️  НАЧИНАЕМ ЗАГРУЗКУ И ОТПРАВКУ АУДИОФАЙЛОВ\n{'='*60}{Style.RESET_ALL}")
        
        # Сортируем выпуски по номеру (от 38 до текущего)
        episodes_sorted = sorted(episodes, key=lambda x: x.get('episode_number', 0))
        
        for i, episode in enumerate(episodes_sorted, 1):
            episode_num = episode.get('episode_number', 'N/A')
            print(f"{Fore.CYAN}📋 Обрабатываем {i}/{len(episodes_sorted)}: Выпуск #{episode_num}{Style.RESET_ALL}")
            
            # Проверяем, не был ли уже отправлен
            if is_episode_sent(episode_num):
                print(f"{Fore.YELLOW}⏭️  Выпуск #{episode_num} уже отправлен, пропускаем{Style.RESET_ALL}")
                continue
            
            filepath = download_audio(episode, dest_folder="downloads")
            if filepath:
                send_audio_to_telegram(filepath, episode, config)
    else:
        print(f"{Fore.RED}❌ Выпуски не найдены{Style.RESET_ALL}") 