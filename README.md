# Smotrim Podcast Downloader to MP3

Автоматический парсер подкастов с сайта [smotrim.ru](https://smotrim.ru), скачивание аудио в MP3 и отправка в Telegram-канал.

## Возможности

- Парсинг выпусков подкаста через API smotrim.ru
- Скачивание аудиофайлов с автоматическими повторными попытками
- Сжатие аудио через FFmpeg (если файл превышает лимит Telegram 50 МБ)
- Отправка MP3 в Telegram-канал через Bot API
- Отслеживание уже отправленных выпусков (дедупликация)
- Цветной вывод прогресса в консоль

## Требования

- Python 3.8+
- FFmpeg (установлен в PATH или указан путь в конфиге)
- Telegram-бот (токен от [@BotFather](https://t.me/BotFather))

## Установка

```bash
git clone https://github.com/MuzzyExtre/Smotrim-down-to-mp3.git
cd Smotrim-down-to-mp3
pip install -r requirements.txt
```

## Настройка

Скопируйте пример конфигурации и заполните свои данные:

```bash
cp config.ini.example config.ini
```

Отредактируйте `config.ini`:

```ini
[telegram]
bot_token = "ВАШ_ТОКЕН_БОТА"
channel_id = "@ВАШ_КАНАЛ"
```

## Запуск

```bash
python smotrim_parser.py
```

## Зависимости

| Пакет | Назначение |
|-------|-----------|
| `requests` | HTTP-запросы к API и скачивание файлов |
| `beautifulsoup4` | Парсинг HTML |
| `ffmpeg-python` | Сжатие аудиофайлов |
| `colorama` | Цветной вывод в консоль |
| `python-telegram-bot` | Telegram Bot API |
| `pydub` | Работа с аудио |
| `mutagen` | Метаданные аудиофайлов |
| `schedule` / `apscheduler` | Планировщик задач |

## Лицензия

MIT
