from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd
import matplotlib.pyplot as plt


def build_open_defects_by_week(
    df: pd.DataFrame,
    output_path: str,
    *,
    created_col: str = "Created",
    resolved_col: str = "Resolved",
    title: str = "Open defects by week",
) -> str:
    """
    Builds weekly open defects trend and saves it as PNG.

    A defect is considered open on week_end if:
      Created <= week_end
      and (Resolved is empty or Resolved > week_end)

    Returns path to saved chart.
    """
    if created_col not in df.columns:
        raise RuntimeError(f"Не найдена колонка '{created_col}'")
    if resolved_col not in df.columns:
        raise RuntimeError(f"Не найдена колонка '{resolved_col}'")

    work_df = df.copy()

    work_df[created_col] = pd.to_datetime(work_df[created_col], errors="coerce")
    work_df[resolved_col] = pd.to_datetime(work_df[resolved_col], errors="coerce")

    work_df = work_df[work_df[created_col].notna()].copy()

    if work_df.empty:
        raise RuntimeError("Нет данных с заполненной датой Created для построения графика")

    start_date = work_df[created_col].min().normalize()
    end_candidates = [work_df[resolved_col].max()]
    end_candidates = [d for d in end_candidates if pd.notna(d)]

    if end_candidates:
        end_date = max(pd.Timestamp.today().normalize(), max(end_candidates).normalize())
    else:
        end_date = pd.Timestamp.today().normalize()

    # Недели по воскресеньям; можно поменять на W-MON, если захочешь
    week_ends = pd.date_range(start=start_date, end=end_date, freq="W")

    open_counts = []
    for week_end in week_ends:
        mask = (
            (work_df[created_col] <= week_end) &
            (
                work_df[resolved_col].isna() |
                (work_df[resolved_col] > week_end)
            )
        )
        open_counts.append(int(mask.sum()))

    chart_df = pd.DataFrame({
        "WeekEnd": week_ends,
        "OpenDefects": open_counts,
    })

    plt.figure(figsize=(14, 6))
    plt.plot(chart_df["WeekEnd"], chart_df["OpenDefects"], linewidth=2)
    plt.title(title)
    plt.xlabel("Week")
    plt.ylabel("Open defects")
    plt.xticks(rotation=45)
    plt.tight_layout()

    output = Path(output_path)
    plt.savefig(output, dpi=150)
    plt.close()

    return str(output)
