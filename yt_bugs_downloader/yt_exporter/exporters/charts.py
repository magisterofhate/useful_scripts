from __future__ import annotations

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

def _is_hot_priority(value) -> bool:
    if pd.isna(value):
        return False

    normalized = str(value).strip().lower()
    return normalized in {"major", "critical", "неотложный"}


def _has_ps_link(value) -> bool:
    if pd.isna(value):
        return False
    return bool(str(value).strip())


def build_defects_dashboard_by_week(
    df: pd.DataFrame,
    output_path: str,
    *,
    created_col: str = "Created",
    resolved_col: str = "Resolved",
    priority_col: str = "Priority",
    ps_links_col: str = "PS links (IDs)",
    title_prefix: str = "",
) -> str:
    """
    Builds one PNG dashboard with 4 weekly charts:
      1. Open defects by week
      2. Created defects by week
      3. Resolved defects by week
      4. Net backlog delta by week

    Returns saved file path.
    """
    if created_col not in df.columns:
        raise RuntimeError(f"Не найдена колонка '{created_col}'")
    if resolved_col not in df.columns:
        raise RuntimeError(f"Не найдена колонка '{resolved_col}'")
    if priority_col not in df.columns:
        raise RuntimeError(f"Не найдена колонка '{priority_col}'")
    if ps_links_col not in df.columns:
        raise RuntimeError(f"Не найдена колонка '{ps_links_col}'")

    work_df = df.copy()

    work_df[created_col] = pd.to_datetime(work_df[created_col], errors="coerce")
    work_df[resolved_col] = pd.to_datetime(work_df[resolved_col], errors="coerce")
    work_df["__is_hot_priority__"] = work_df[priority_col].apply(_is_hot_priority)
    work_df["__is_ps__"] = work_df[ps_links_col].apply(_has_ps_link)

    work_df = work_df[work_df[created_col].notna()].copy()

    if work_df.empty:
        raise RuntimeError("Нет данных с заполненной датой Created для построения графиков")

    start_date = work_df[created_col].min().normalize()

    end_candidates = [pd.Timestamp.today().normalize()]
    if work_df[resolved_col].notna().any():
        end_candidates.append(work_df[resolved_col].max().normalize())

    end_date = max(end_candidates)

    # Недели по воскресеньям
    week_ends = pd.date_range(start=start_date, end=end_date, freq="W")

    open_counts = []
    open_hot_counts = []
    created_counts = []
    resolved_counts = []
    open_ps_counts = []

    for week_end in week_ends:
        week_start = week_end - pd.Timedelta(days=6)

        open_mask = (
            (work_df[created_col] <= week_end) &
            (
                work_df[resolved_col].isna() |
                (work_df[resolved_col] > week_end)
            )
        )

        open_hot_mask = open_mask & work_df["__is_hot_priority__"]
        open_ps_mask = open_mask & work_df["__is_ps__"]

        created_mask = (
            (work_df[created_col] >= week_start) &
            (work_df[created_col] <= week_end)
        )

        resolved_mask = (
            work_df[resolved_col].notna() &
            (work_df[resolved_col] >= week_start) &
            (work_df[resolved_col] <= week_end)
        )

        open_counts.append(int(open_mask.sum()))
        created_counts.append(int(created_mask.sum()))
        resolved_counts.append(int(resolved_mask.sum()))
        open_hot_counts.append(int(open_hot_mask.sum()))
        open_ps_counts.append(int(open_ps_mask.sum()))

    delta_counts = [c - r for c, r in zip(created_counts, resolved_counts)]

    chart_df = pd.DataFrame({
        "WeekEnd": week_ends,
        "OpenDefects": open_counts,
        "OpenHotDefects": open_hot_counts,
        "OpenPSDefects": open_ps_counts,
        "CreatedDefects": created_counts,
        "ResolvedDefects": resolved_counts,
        "BacklogDelta": delta_counts,
    })

    monthly_points = (
        chart_df
        .set_index("WeekEnd")
        .resample("ME")
        .last()
        .dropna()
        .reset_index()
    )

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    fig.suptitle(
        f"{title_prefix} Weekly defects dashboard".strip(),
        fontsize=14
    )

    # 1. Open defects
    open_ax = axes[0, 0]

    open_ax.plot(
        chart_df["WeekEnd"],
        chart_df["OpenDefects"],
        linewidth=2,
        label="All open defects",
    )

    open_ax.plot(
        chart_df["WeekEnd"],
        chart_df["OpenHotDefects"],
        linewidth=2,
        color="red",
        label="Major/Critical/Urgent",
    )

    open_ax.plot(
        chart_df["WeekEnd"],
        chart_df["OpenPSDefects"],
        linewidth=2,
        color="black",
        label="PS-linked defects",
    )

    for column, y_offset in [
        ("OpenDefects", 8),
        ("OpenHotDefects", -14),
        ("OpenPSDefects", 8),
    ]:
        open_ax.scatter(
            monthly_points["WeekEnd"],
            monthly_points[column],
            s=18,
        )

        for _, point in monthly_points.iterrows():
            open_ax.annotate(
                str(int(point[column])),
                xy=(point["WeekEnd"], point[column]),
                xytext=(0, y_offset),
                textcoords="offset points",
                ha="center",
                fontsize=8,
            )

    open_ax.set_title("Open defects by week")
    open_ax.set_xlabel("Week")
    open_ax.set_ylabel("Open defects")
    open_ax.tick_params(axis="x", rotation=45)
    open_ax.legend()

    # 2. Created defects
    axes[0, 1].plot(chart_df["WeekEnd"], chart_df["CreatedDefects"], linewidth=2)
    axes[0, 1].set_title("Created defects by week")
    axes[0, 1].set_xlabel("Week")
    axes[0, 1].set_ylabel("Created")
    axes[0, 1].tick_params(axis="x", rotation=45)

    # 3. Resolved defects
    axes[1, 0].plot(chart_df["WeekEnd"], chart_df["ResolvedDefects"], linewidth=2)
    axes[1, 0].set_title("Resolved defects by week")
    axes[1, 0].set_xlabel("Week")
    axes[1, 0].set_ylabel("Resolved")
    axes[1, 0].tick_params(axis="x", rotation=45)

    # 4. Net backlog delta
    axes[1, 1].plot(chart_df["WeekEnd"], chart_df["BacklogDelta"], linewidth=2)
    axes[1, 1].axhline(0, linewidth=1)
    axes[1, 1].set_title("Net backlog delta by week")
    axes[1, 1].set_xlabel("Week")
    axes[1, 1].set_ylabel("Created - Resolved")
    axes[1, 1].tick_params(axis="x", rotation=45)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    output = Path(output_path)
    plt.savefig(output, dpi=150)
    plt.close(fig)

    return str(output)


def build_open_vs_ps_linked_chart_by_week(
    df: pd.DataFrame,
    output_path: str,
    *,
    start_date: str,
    created_col: str = "Created",
    resolved_col: str = "Resolved",
    ps_links_col: str = "PS links (IDs)",
    title_prefix: str = "",
) -> str:
    if created_col not in df.columns:
        raise RuntimeError(f"Не найдена колонка '{created_col}'")
    if resolved_col not in df.columns:
        raise RuntimeError(f"Не найдена колонка '{resolved_col}'")
    if ps_links_col not in df.columns:
        raise RuntimeError(f"Не найдена колонка '{ps_links_col}'")

    work_df = df.copy()
    work_df[created_col] = pd.to_datetime(work_df[created_col], errors="coerce")
    work_df[resolved_col] = pd.to_datetime(work_df[resolved_col], errors="coerce")
    work_df["__is_ps__"] = work_df[ps_links_col].apply(_has_ps_link)

    work_df = work_df[work_df[created_col].notna()].copy()
    if work_df.empty:
        raise RuntimeError("Нет данных с заполненной датой Created для построения графика")

    start = pd.to_datetime(start_date, errors="coerce")
    if pd.isna(start):
        raise RuntimeError(f"Некорректная OPEN_PS_CHART_START_DATE: {start_date}")

    start = start.normalize()

    end_candidates = [pd.Timestamp.today().normalize()]
    if work_df[resolved_col].notna().any():
        end_candidates.append(work_df[resolved_col].max().normalize())
    end_date = max(end_candidates)

    week_ends = pd.date_range(start=start, end=end_date, freq="W")

    open_counts = []
    open_ps_counts = []

    for week_end in week_ends:
        open_mask = (
            (work_df[created_col] <= week_end)
            & (
                work_df[resolved_col].isna()
                | (work_df[resolved_col] > week_end)
            )
        )

        open_counts.append(int(open_mask.sum()))
        open_ps_counts.append(int((open_mask & work_df["__is_ps__"]).sum()))

    chart_df = pd.DataFrame({
        "WeekEnd": week_ends,
        "OpenDefects": open_counts,
        "OpenPSDefects": open_ps_counts,
    })

    fig, ax = plt.subplots(figsize=(14, 7))

    ax.plot(
        chart_df["WeekEnd"],
        chart_df["OpenDefects"],
        linewidth=2,
        label="All open defects",
    )

    ax.plot(
        chart_df["WeekEnd"],
        chart_df["OpenPSDefects"],
        linewidth=2,
        label="Open PS-linked defects",
    )

    # подписи старт/финиш для линии всех открытых дефектов
    x_vals = chart_df["WeekEnd"].tolist()

    open_vals = chart_df["OpenDefects"].tolist()
    ps_vals = chart_df["OpenPSDefects"].tolist()

    if x_vals:
        first_x = x_vals[0]
        last_x = x_vals[-1]

        # all open defects
        ax.annotate(
            str(open_vals[0]),
            xy=(first_x, open_vals[0]),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            fontsize=9,
            fontweight="bold",
        )

        ax.annotate(
            str(open_vals[-1]),
            xy=(last_x, open_vals[-1]),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            fontsize=9,
            fontweight="bold",
        )

        # ps-linked open defects
        ax.annotate(
            str(ps_vals[0]),
            xy=(first_x, ps_vals[0]),
            xytext=(0, -14),
            textcoords="offset points",
            ha="center",
            fontsize=9,
            fontweight="bold",
        )

        ax.annotate(
            str(ps_vals[-1]),
            xy=(last_x, ps_vals[-1]),
            xytext=(0, -14),
            textcoords="offset points",
            ha="center",
            fontsize=9,
            fontweight="bold",
        )

    ax.set_title(
        f"{title_prefix} Open defects vs PS-linked defects since {start.date()}".strip()
    )
    ax.set_xlabel("Week")
    ax.set_ylabel("Open defects")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()

    plt.tight_layout()

    output = Path(output_path)
    plt.savefig(output, dpi=150)
    plt.close(fig)

    return str(output)
