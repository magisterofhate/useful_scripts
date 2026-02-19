# app.py
import os
from datetime import date, timedelta

from flask import Flask, render_template, request, send_file, redirect, url_for, flash

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

app = Flask(__name__)
# секрет для flash-сообщений, можно вынести в .env при желании
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me-please")

GROUP_PRESETS = {
    "BILL": ["billQA"],
    "DCI": ["dciQA"],
    "VM": ["vmQA"],
    "AQA": ["ispAQA"],
    "All": ["billQA", "dciQA", "vmQA", "ispAQA"],
}


def compute_period(period, start_str=None, end_str=None):
    """
    period:
      - 'last_week'  -> за прошлую календарную неделю (Пн-Вс),
      - 'last_month' -> за прошлый календарный месяц,
      - 'custom'     -> берём даты из start_str / end_str (YYYY-MM-DD).
    """
    today = date.today()

    if period == "last_week":
        current_week_start = today - timedelta(days=today.weekday())  # Пн текущей недели
        last_week_start = current_week_start - timedelta(days=7)
        last_week_end = current_week_start - timedelta(days=1)  # Вс прошлой недели
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
            raise ValueError("Для периода 'Произвольный' нужно указать даты начала и конца.")
        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str)
        if end < start:
            raise ValueError("Дата окончания не может быть раньше даты начала.")
        return start, end

    raise ValueError(f"Неизвестный период: {period}")


@app.route("/timesheet", methods=["GET", "POST"], strict_slashes=False)
def index():
    if request.method == "POST":
        period = request.form.get("period")
        start_str = request.form.get("start_date") or None
        end_str = request.form.get("end_date") or None
        group_preset = request.form.get("group_preset")  # обязательно

        # 1. Период
        try:
            start_date, end_date = compute_period(period, start_str, end_str)
        except Exception as e:
            flash(str(e), "error")
            return redirect(url_for("index"))

        # 2. Формирование списка пользователей и мапы login -> группа
        login_to_group = {}
        user_logins: list[str] = []

        # Группа обязательна: берём выбранный preset
        if not group_preset or group_preset not in GROUP_PRESETS:
            flash("Выберите группу (обязательное поле).", "error")
            return redirect(url_for("index"))

        group_names = GROUP_PRESETS[group_preset]

        # Несколько групп: пользователи идут блоками по группам, без дублей
        for group_name in group_names:
            try:
                logins = get_group_users_by_name(group_name)
            except Exception as e:
                flash(f"Ошибка при загрузке группы '{group_name}': {e}", "error")
                return redirect(url_for("index"))

            for login in logins:
                if login not in login_to_group:
                    login_to_group[login] = group_name
                    user_logins.append(login)

        # 3. Справочник login -> ФИО
        try:
            users_map = fetch_users_map()
        except Exception as e:
            flash(f"Ошибка при загрузке пользователей: {e}", "error")
            return redirect(url_for("index"))

        # 4. Work items из YouTrack
        try:
            work_items = fetch_work_items_for_users(
                user_logins=user_logins,
                start_date=start_date,
                end_date=end_date,
                issue_query=ISSUE_QUERY,
            )
        except Exception as e:
            flash(f"Ошибка при загрузке work items: {e}", "error")
            return redirect(url_for("index"))

        # 5. Матрица timesheet (ФИО × даты)
        timesheet_df = build_timesheet_matrix(
            work_items=work_items,
            user_logins=user_logins,
            users_map=users_map,
            start_date=start_date,
            end_date=end_date,
        )

        # Вставляем колонку "Группа" справа от ФИО (первая колонка данных)
        group_column = [login_to_group.get(login, "") for login in user_logins]
        timesheet_df.insert(0, "Группа", group_column)

        # 6. Детализация
        details_df = build_details_sheet(work_items, users_map)

        # 7. Генерация Excel-файла (helpers возвращает путь к файлу)
        try:
            filename = write_excel_with_formatting(timesheet_df, details_df, start_date, end_date)
        except Exception as e:
            flash(f"Ошибка при генерации Excel: {e}", "error")
            return redirect(url_for("index"))

        # 8. Отдаём файл на скачивание
        download_name = os.path.basename(filename)
        return send_file(
            filename,
            as_attachment=True,
            download_name=download_name,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    # GET-запрос — просто показываем форму
    return render_template("index.html")


if __name__ == "__main__":
    # для простоты — debug=True; на проде убрать
    app.run(host="127.0.0.1", port=5000, debug=False)
