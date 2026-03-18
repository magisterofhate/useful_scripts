from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd


def _has_ps_link(value) -> bool:
    if pd.isna(value):
        return False
    return bool(str(value).strip())


def _is_cancelled_status(value) -> bool:
    if pd.isna(value):
        return False
    return str(value).strip().lower().startswith("аннули")


def _parse_quarter(value):
    """
    Преобразует строку вида 'Q2 2025' -> (2025, 2)
    Это нужно для правильной сортировки кварталов.
    """
    try:
        q_part, year_part = str(value).strip().split()
        quarter = int(q_part.replace("Q", ""))
        year = int(year_part)
        return (year, quarter)
    except Exception:
        return (9999, 9)


def _is_target_priority(value) -> bool:
    if pd.isna(value):
        return False

    normalized = str(value).strip().lower()
    return normalized in {"неотложный", "critical", "major"}


def build_der_tables(
    df: pd.DataFrame,
    *,
    affected_version_col: str = "Affected version",
    quarter_col: str = "C_Qtr",
    ps_links_col: str = "PS links (IDs)",
    status_col: str = "Status",
    priority_col: str = "Приоритет",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    required_cols = [affected_version_col, quarter_col, ps_links_col, status_col, priority_col]
    for col in required_cols:
        if col not in df.columns:
            raise RuntimeError(f"Не найдена колонка '{col}' для расчёта DER")

    work_df = df.copy()

    work_df[affected_version_col] = work_df[affected_version_col].fillna("").astype(str).str.strip()
    work_df[quarter_col] = work_df[quarter_col].fillna("").astype(str).str.strip()
    work_df[status_col] = work_df[status_col].fillna("").astype(str).str.strip()

    work_df["__is_escape__"] = work_df[ps_links_col].apply(_has_ps_link)
    work_df["__is_cancelled__"] = work_df[status_col].apply(_is_cancelled_status)
    work_df["__is_target_priority__"] = work_df[priority_col].apply(_is_target_priority)

    # Total = все дефекты, кроме аннулированных
    total_df = work_df[~work_df["__is_cancelled__"]].copy()
    priority_df = total_df[total_df["__is_target_priority__"]].copy()

    # ---------- DER by affected version ----------
    by_version_df = total_df[total_df[affected_version_col] != ""].copy()

    if by_version_df.empty:
        der_by_version = pd.DataFrame(columns=[
            "Affected version", "Total defects", "Escapes", "DER", "DER %"
        ])
    else:
        der_by_version = (
            by_version_df
            .groupby(affected_version_col, dropna=False)
            .agg(
                **{
                    "Total defects": ("__is_escape__", "size"),
                    "Escapes": ("__is_escape__", "sum"),
                }
            )
            .reset_index()
            .rename(columns={affected_version_col: "Affected version"})
        )

        der_by_version["DER"] = der_by_version["Escapes"] / der_by_version["Total defects"]
        der_by_version["DER %"] = (der_by_version["DER"] * 100).round(2)
        der_by_version["DER"] = der_by_version["DER"].round(4)

        der_by_version = der_by_version.sort_values("Affected version").reset_index(drop=True)

    # ---------- DER by quarter ----------
    by_quarter_df = total_df[total_df[quarter_col] != ""].copy()

    if by_quarter_df.empty:
        der_by_quarter = pd.DataFrame(columns=[
            "Quarter", "Total defects", "Escapes", "DER", "DER %"
        ])
    else:
        der_by_quarter = (
            by_quarter_df
            .groupby(quarter_col, dropna=False)
            .agg(
                **{
                    "Total defects": ("__is_escape__", "size"),
                    "Escapes": ("__is_escape__", "sum"),
                }
            )
            .reset_index()
            .rename(columns={quarter_col: "Quarter"})
        )

        der_by_quarter["DER"] = der_by_quarter["Escapes"] / der_by_quarter["Total defects"]
        der_by_quarter["DER %"] = (der_by_quarter["DER"] * 100).round(2)
        der_by_quarter["DER"] = der_by_quarter["DER"].round(4)

        der_by_quarter["__sort__"] = der_by_quarter["Quarter"].apply(_parse_quarter)

        der_by_quarter = (
            der_by_quarter
            .sort_values("__sort__")
            .drop(columns="__sort__")
            .reset_index(drop=True)
        )

    # ---------- DER by affected version (Urg+Crit+Maj) ----------
    by_version_prio_df = priority_df[priority_df[affected_version_col] != ""].copy()

    if by_version_prio_df.empty:
        der_by_version_prio = pd.DataFrame(columns=[
            "Affected version", "Total defects", "Escapes", "DER", "DER %"
        ])
    else:
        der_by_version_prio = (
            by_version_prio_df
            .groupby(affected_version_col, dropna=False)
            .agg(
                **{
                    "Total defects": ("__is_escape__", "size"),
                    "Escapes": ("__is_escape__", "sum"),
                }
            )
            .reset_index()
            .rename(columns={affected_version_col: "Affected version"})
        )

        der_by_version_prio["DER"] = der_by_version_prio["Escapes"] / der_by_version_prio["Total defects"]
        der_by_version_prio["DER %"] = (der_by_version_prio["DER"] * 100).round(2)
        der_by_version_prio["DER"] = der_by_version_prio["DER"].round(4)

        der_by_version_prio = der_by_version_prio.sort_values("Affected version").reset_index(drop=True)

    # ---------- DER by quarter (Urg+Crit+Maj) ----------
    by_quarter_prio_df = priority_df[priority_df[quarter_col] != ""].copy()

    if by_quarter_prio_df.empty:
        der_by_quarter_prio = pd.DataFrame(columns=[
            "Quarter", "Total defects", "Escapes", "DER", "DER %"
        ])
    else:
        der_by_quarter_prio = (
            by_quarter_prio_df
            .groupby(quarter_col, dropna=False)
            .agg(
                **{
                    "Total defects": ("__is_escape__", "size"),
                    "Escapes": ("__is_escape__", "sum"),
                }
            )
            .reset_index()
            .rename(columns={quarter_col: "Quarter"})
        )

        der_by_quarter_prio["DER"] = der_by_quarter_prio["Escapes"] / der_by_quarter_prio["Total defects"]
        der_by_quarter_prio["DER %"] = (der_by_quarter_prio["DER"] * 100).round(2)
        der_by_quarter_prio["DER"] = der_by_quarter_prio["DER"].round(4)

        der_by_quarter_prio["__sort__"] = der_by_quarter_prio["Quarter"].apply(_parse_quarter)

        der_by_quarter_prio = (
            der_by_quarter_prio
            .sort_values("__sort__")
            .drop(columns="__sort__")
            .reset_index(drop=True)
        )


    return der_by_version, der_by_quarter, der_by_version_prio, der_by_quarter_prio


def export_der_excel(
    df: pd.DataFrame,
    output_path: str,
    *,
    affected_version_col: str = "Affected version",
    quarter_col: str = "C_Qtr",
    ps_links_col: str = "PS links (IDs)",
    status_col: str = "Status",
    priority_col: str = "Приоритет",
) -> str:
    der_by_version, der_by_quarter, der_by_version_prio, der_by_quarter_prio = build_der_tables(
        df,
        affected_version_col=affected_version_col,
        quarter_col=quarter_col,
        ps_links_col=ps_links_col,
        status_col=status_col,
        priority_col=priority_col,
    )

    output = Path(output_path)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        der_by_version.to_excel(writer, index=False, sheet_name="DER by affected version")
        der_by_quarter.to_excel(writer, index=False, sheet_name="DER by quarter")
        der_by_version_prio.to_excel(writer, index=False, sheet_name="DER by aff ver U_C_M")
        der_by_quarter_prio.to_excel(writer, index=False, sheet_name="DER by quarter U_C_M")

    return str(output)
