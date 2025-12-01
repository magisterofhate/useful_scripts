import requests
import pandas as pd
from datetime import datetime, date, timedelta, timezone

# ==== CONFIG =================================================================

# URL твоего YouTrack (БЕЗ /api в конце)
# Примеры:
#   https://example.youtrack.cloud
#   https://example.myjetbrains.com/youtrack
BASE_URL = "https://youtrack.ispsystem.net/"

# Персональный токен из профиля YouTrack (scope: YouTrack, Hub)
API_TOKEN = "perm-YS5taWxpbmV2c2tpaQ==.NTgtOTU=.vkjYV9lHy4hFn2HrNvXfzAtSSNUbSM"

# Период timesheet'а
START_DATE = "2025-11-01"
END_DATE = "2025-11-30"

# Фильтр по задачам, как в поисковой строке YouTrack (можно оставить пустым "")
ISSUE_QUERY = "" # "project: VMmanager"

# Вариант 1: явно перечислить логины пользователей (проще всего)
USER_LOGINS = ["ivanov", "petrov", "sidorov"]

# Вариант 2 (опционально): взять пользователей из группы Hub
USE_GROUP = True
HUB_GROUP_ID = "5ef86c95-89e1-453f-8e20-d6f19e30f646"  # если USE_GROUP=True

# Имя файла с итоговым отчётом
OUTPUT_XLSX = f"timesheet_{START_DATE}_{END_DATE}.xlsx"

# ==== END CONFIG =============================================================

HEADERS_YT = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/json"
}


def get_group_users_from_hub():
    """
    Получаем логины пользователей из группы Hub.
    Для YouTrack Cloud hub-URL обычно: BASE_URL + '/hub'
    """
    hub_base = BASE_URL.rstrip("/") + "/hub"
    url = f"{hub_base}/api/rest/usergroups/{HUB_GROUP_ID}"
    params = {"fields": "id,name,users(login,name)"}
    resp = requests.get(url, headers=HEADERS_YT, params=params)
    resp.raise_for_status()
    data = resp.json()
    users = data.get("users", [])
    logins = [u["login"] for u in users if "login" in u]
    print(f"Найдено {len(logins)} пользователей в группе {data.get('name')}")
    return logins


def fetch_work_items_for_users(user_logins):
    """
    Тянем work items по всем пользователям за период START_DATE..END_DATE,
    с фильтром по задачам ISSUE_QUERY.
    """
    all_items = []
    for login in user_logins:
        skip = 0
        while True:
            params = {
                "fields": "author(login,fullName),date,duration(minutes),"
                          "issue(idReadable,summary)",
                "author": login,
                "startDate": START_DATE,
                "endDate": END_DATE,
                "query": ISSUE_QUERY,
                "$top": 100,
                "$skip": skip,
            }
            url = BASE_URL.rstrip("/") + "/api/workItems"
            resp = requests.get(url, headers=HEADERS_YT, params=params)
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break

            for wi in batch:
                all_items.append(wi)

            if len(batch) < 100:
                break
            skip += len(batch)

        print(f"{login}: загружено {skip}+ work items")

    return all_items


def build_timesheet_matrix(work_items, user_logins):
    """
    Из списка work items строим pandas-DataFrame вида:
        user × date → часы
    + добавляем строку Total.
    """
    records = []
    for wi in work_items:
        author = wi.get("author") or {}
        login = author.get("login", "unknown")
        duration = (wi.get("duration") or {}).get("minutes", 0)

        # date — это timestamp в мс UTC, приводим к дате
        ts = wi.get("date")
        if ts is None:
            continue
        d = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).date()

        records.append({
            "login": login,
            "date": d,
            "minutes": duration,
        })

    if not records:
        print("Нет записей о работе за указанный период.")
        # создаём пустую таблицу с нулями для всех пользователей и дат
        start = datetime.strptime(START_DATE, "%Y-%m-%d").date()
        end = datetime.strptime(END_DATE, "%Y-%m-%d").date()
        days = []
        cur = start
        while cur <= end:
            days.append(cur)
            cur += timedelta(days=1)
        empty = pd.DataFrame(0, index=user_logins, columns=days)
        empty.index.name = "login"
        return empty

    df = pd.DataFrame(records)

    # сводная таблица: минуты → часы, нули, если нет списаний
    pivot = df.pivot_table(
        index="login",
        columns="date",
        values="minutes",
        aggfunc="sum",
        fill_value=0
    ) / 60.0  # переводим в часы

    # убедимся, что в матрице есть все пользователи и все дни периода
    start = datetime.strptime(START_DATE, "%Y-%m-%d").date()
    end = datetime.strptime(END_DATE, "%Y-%m-%d").date()
    all_days = []
    cur = start
    while cur <= end:
        all_days.append(cur)
        cur += timedelta(days=1)

    # добавляем отсутствующие даты
    for d in all_days:
        if d not in pivot.columns:
            pivot[d] = 0.0

    # добавляем отсутствующих пользователей (с нулями)
    for login in user_logins:
        if login not in pivot.index:
            pivot.loc[login] = 0.0

    # сортируем по дате и логину
    pivot = pivot.sort_index(axis=0).sort_index(axis=1)

    # добавляем итог по строке
    pivot["Total"] = pivot.sum(axis=1)

    return pivot


def main():
    if USE_GROUP:
        user_logins = get_group_users_from_hub()
    else:
        user_logins = USER_LOGINS

    print("Пользователи:", user_logins)

    work_items = fetch_work_items_for_users(user_logins)
    print(f"Всего work items: {len(work_items)}")

    timesheet = build_timesheet_matrix(work_items, user_logins)

    # сохраняем в Excel: один лист — матрица, второй — детализация
    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        timesheet.to_excel(writer, sheet_name="Timesheet")

        # детализация (по строкам)
        detail_records = []
        for wi in work_items:
            author = wi.get("author") or {}
            issue = wi.get("issue") or {}
            ts = wi.get("date")
            if ts is None:
                continue
            d = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).date()
            minutes = (wi.get("duration") or {}).get("minutes", 0)
            detail_records.append({
                "login": author.get("login", ""),
                "date": d,
                "hours": minutes / 60.0,
                "issue": issue.get("idReadable", ""),
                "summary": issue.get("summary", ""),
            })
        if detail_records:
            pd.DataFrame(detail_records).to_excel(
                writer, sheet_name="Details", index=False
            )

    print(f"Готово, файл сохранён как {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()
