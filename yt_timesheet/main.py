# main.py
import argparse
from datetime import date, timedelta

from config import DEFAULT_HUB_GROUP_ID, ISSUE_QUERY
from helpers import (
    get_group_users_by_id,
    get_group_users_by_name,
    fetch_users_map,
    fetch_work_items_for_users,
    build_timesheet_matrix,
    build_details_sheet,
    write_excel_with_formatting,
)


def compute_period(period, start_str=None, end_str=None):
    """
    period:
      - 'last_week'  -> за прошлую календарную неделю (Пн-Вс),
      - 'last_month' -> за прошлый календарный месяц,
      - 'custom'     -> берём даты из start_str / end_str (YYYY-MM-DD).
    """
    today = date.today()

    if period == "last_week":
        # понедельник текущей недели
        current_week_start = today - timedelta(days=today.weekday())
        # прошлый понедельник
        last_week_start = current_week_start - timedelta(days=7)
        # прошлая неделя до воскресенья
        last_week_end = current_week_start - timedelta(days=1)
        return last_week_start, last_week_end

    if period == "last_month":
        first_this_month = date(today.year, today.month, 1)
        if today.month == 1:
            last_month_year = today.year - 1
            last_month_month = 12
        else:
            last_month_year = today.year
            last_month_month = today.month - 1
        last_month_start = date(last_month_year, last_month_month, 1)
        last_month_end = first_this_month - timedelta(days=1)
        return last_month_start, last_month_end

    if period == "custom":
        if not start_str or not end_str:
            raise SystemExit("Для period=custom нужно указать --start-date и --end-date")
        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str)
        if end < start:
            raise SystemExit("end-date не может быть раньше start-date")
        return start, end

    raise SystemExit(f"Неизвестное значение period: {period}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Генерация timesheet-отчёта по YouTrack (через REST API)."
    )

    parser.add_argument(
        "--period",
        choices=["last_week", "last_month", "custom"],
        required=True,
        help=(
            "Период отчёта: "
            "last_week — за прошлую неделю (Пн–Вс), "
            "last_month — за прошлый календарный месяц, "
            "custom — задать даты вручную."
        ),
    )
    parser.add_argument(
        "--start-date",
        help="Дата начала периода (YYYY-MM-DD). Используется, если --period=custom",
    )
    parser.add_argument(
        "--end-date",
        help="Дата окончания периода (YYYY-MM-DD). Используется, если --period=custom",
    )

    parser.add_argument(
        "--hub-group",
        action="append",
        help=(
            "Имя группы пользователей в Hub. "
            "Можно указать несколько раз: "
            '--hub-group "QA" --hub-group "Developers". '
            "Если не указано и нет --users, используется DEFAULT_HUB_GROUP_ID из config.py."
        ),
    )
    parser.add_argument(
        "--users",
        help=(
            "Список логинов пользователей через запятую, например: "
            '"ivanov,petrov,sidorov". '
            "Используется, если не передан --hub-group."
        ),
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # 1. Период
    start_date, end_date = compute_period(args.period, args.start_date, args.end_date)
    print(f"Период отчёта: {start_date} .. {end_date}")

    # 2. Определяем, каких пользователей брать и в каком порядке
    login_to_group: dict[str, str] = {}

    if args.users:
        # Явный список логинов — приоритетнее всего
        user_logins = [u.strip() for u in args.users.split(",") if u.strip()]
        print(f"Используем логины из --users: {user_logins}")
        # Для явного списка можно поставить группу, например 'manual' или пустую строку
        for login in user_logins:
            login_to_group[login] = ""

    elif args.hub_group:
        # Несколько групп по имени. Пользователи из одной группы
        # идут подряд, группы — в порядке указания в CLI.
        user_logins: list[str] = []
        print(f"Ищем группы по именам: {args.hub_group}")
        for group_name in args.hub_group:
            logins = get_group_users_by_name(group_name)
            for login in logins:
                if login not in login_to_group:
                    login_to_group[login] = group_name
                    user_logins.append(login)
        print(f"Итоговый список логинов по группам: {user_logins}")

    else:
        # Ни users, ни hub-group не указаны — берём default-группу по ID
        print("Группы и явные пользователи не указаны → используем DEFAULT_HUB_GROUP_ID из config.py")
        user_logins = get_group_users_by_id(DEFAULT_HUB_GROUP_ID)
        for login in user_logins:
            login_to_group[login] = DEFAULT_HUB_GROUP_ID  # или можно руками вписать читабельное имя

    if not user_logins:
        raise SystemExit("Список пользователей пуст — отчёт генерировать не из чего.")

    # 3. Справочник login -> ФИО
    users_map = fetch_users_map()

    # 4. Work items из YouTrack
    work_items = fetch_work_items_for_users(
        user_logins=user_logins,
        start_date=start_date,
        end_date=end_date,
        issue_query=ISSUE_QUERY,
    )
    print(f"Всего work items: {len(work_items)}")

    # 5. Матрица timesheet (ФИО × даты)
    timesheet_df = build_timesheet_matrix(
        work_items=work_items,
        user_logins=user_logins,
        users_map=users_map,
        start_date=start_date,
        end_date=end_date,
    )

    # Вставляем колонку "Группа" сразу справа от ФИО.
    # Порядок строк в timesheet_df такой же, как в user_logins,
    # потому что build_timesheet_matrix делает reindex по target_names.
    group_column = [login_to_group.get(login, "") for login in user_logins]
    timesheet_df.insert(0, "Группа", group_column)

    # 6. Детализация
    details_df = build_details_sheet(work_items, users_map)

    # 7. Excel + форматирование и именем файла с датами периода
    write_excel_with_formatting(timesheet_df, details_df, start_date, end_date)



if __name__ == "__main__":
    main()
