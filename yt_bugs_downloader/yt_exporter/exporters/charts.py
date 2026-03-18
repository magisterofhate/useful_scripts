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

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    fig.suptitle(
        f"{title_prefix} Weekly defects dashboard".strip(),
        fontsize=14
    )

    # 1. Open defects
    axes[0, 0].plot(
        chart_df["WeekEnd"],
        chart_df["OpenDefects"],
        linewidth=2,
        label="All open defects",
    )

    axes[0, 0].plot(
        chart_df["WeekEnd"],
        chart_df["OpenHotDefects"],
        linewidth=2,
        color="red",
        label="Major/Critical/Urgent",
    )

    axes[0, 0].plot(
        chart_df["WeekEnd"],
        chart_df["OpenPSDefects"],
        linewidth=2,
        color="black",
        label="PS-linked defects",
    )

    axes[0, 0].set_title("Open defects by week")
    axes[0, 0].set_xlabel("Week")
    axes[0, 0].set_ylabel("Open defects")
    axes[0, 0].tick_params(axis="x", rotation=45)
    axes[0, 0].legend()

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
