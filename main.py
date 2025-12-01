# main.py
from config import (
    USE_GROUP,
    USER_LOGINS,
)
from helpers import (
    get_group_users_from_hub,
    fetch_users_map,
    fetch_work_items_for_users,
    build_timesheet_matrix,
    build_details_sheet,
    write_excel_with_formatting,
)


def main():
    # Определяем, с кем работаем: явный список логинов или группа
    if USE_GROUP:
        user_logins = get_group_users_from_hub()
    else:
        user_logins = USER_LOGINS

    print("Пользователи (логины):", user_logins)

    # logins -> ФИО
    users_map = fetch_users_map()

    # work items за период по выбранным пользователям
    work_items = fetch_work_items_for_users(user_logins)
    print(f"Всего work items: {len(work_items)}")

    # Матрица timesheet (ФИО × даты)
    timesheet_df = build_timesheet_matrix(work_items, user_logins, users_map)

    # Детализация
    details_df = build_details_sheet(work_items, users_map)

    # Excel + форматирование (выходные оранжевые, нули красные)
    write_excel_with_formatting(timesheet_df, details_df)


if __name__ == "__main__":
    main()
