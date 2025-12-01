# ==== CONFIG =================================================================

# URL YouTrack
BASE_URL = "https://youtrack.ispsystem.net/"

# Персональный токен из профиля YouTrack
API_TOKEN = "perm-YS5taWxpbmV2c2tpaQ==.NTgtOTU=.vkjYV9lHy4hFn2HrNvXfzAtSSNUbSM"

# Фильтр по задачам (можно оставить пустым)
ISSUE_QUERY = "" # "project: VMmanager"

# ID группы по умолчанию (из Hub),
# используется, если НЕ указаны ни --hub-group, ни --users.
DEFAULT_HUB_GROUP_ID = "5ef86c95-89e1-453f-8e20-d6f19e30f646"  # если USE_GROUP=True

# Базовое имя файла отчёта (без дат и расширения)
# Итоговый файл будет вида: timesheet_YYYY-MM-DD_YYYY-MM-DD.xlsx
BASE_FILE_NAME = "timesheet"

# ==== END CONFIG =============================================================