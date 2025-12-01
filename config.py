# ==== CONFIG =================================================================

# URL YouTrack
BASE_URL = "https://youtrack.ispsystem.net/"

# Персональный токен из профиля YouTrack
API_TOKEN = "perm-YS5taWxpbmV2c2tpaQ==.NTgtOTU=.vkjYV9lHy4hFn2HrNvXfzAtSSNUbSM"

# Период timesheet'а
START_DATE = "2025-11-01"
END_DATE = "2025-11-30"

# Фильтр по задачам (можно оставить пустым)
ISSUE_QUERY = "" # "project: VMmanager"

# Вариант 1: явно перечислить логины пользователей
USER_LOGINS = ["ivanov", "petrov", "sidorov"]

# Вариант 2 (опционально): взять пользователей из группы
USE_GROUP = True
GROUP_ID = "5ef86c95-89e1-453f-8e20-d6f19e30f646"  # если USE_GROUP=True

# Имя файла с итоговым отчётом
OUTPUT_XLSX = f"timesheet_{START_DATE}_{END_DATE}.xlsx"

# ==== END CONFIG =============================================================