# config.py
import os
from dotenv import load_dotenv

# Загружаем переменные из .env (если он есть рядом)
load_dotenv()

# URL твоего YouTrack (БЕЗ /api в конце)
# Примеры:
#   https://example.youtrack.cloud
#   https://example.myjetbrains.com/youtrack
BASE_URL = os.getenv("YOUTRACK_BASE_URL")

# Персональный токен из профиля YouTrack (scope: YouTrack, Hub)
API_TOKEN = os.getenv("YOUTRACK_API_TOKEN")

if not BASE_URL:
    raise RuntimeError("Не задан YOUTRACK_BASE_URL в .env или окружении")

if not API_TOKEN:
    raise RuntimeError("Не задан YOUTRACK_API_TOKEN в .env или окружении")

# Фильтр по задачам, как в поисковой строке YouTrack.
# Можно оставить пустым "" или, например, "project: VMmanager"
ISSUE_QUERY = os.getenv("YOUTRACK_ISSUE_QUERY", "project: VMmanager")

# Базовое имя файла отчёта (без дат и расширения)
# Итоговый файл будет вида: timesheet_YYYY-MM-DD_YYYY-MM-DD.xlsx
BASE_FILE_NAME = os.getenv("TIMESHEET_BASE_NAME", "timesheet")

# ID группы по умолчанию (из Hub),
# используется, если НЕ указаны ни --hub-group, ни --users.
DEFAULT_HUB_GROUP_ID = os.getenv("DEFAULT_HUB_GROUP_ID")
if not DEFAULT_HUB_GROUP_ID:
    raise RuntimeError("Не задан DEFAULT_HUB_GROUP_ID в .env или окружении")
