from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime, timezone, date
import re

import numpy as np
import pandas as pd


@dataclass
class ExportStats:
    total_fetched: int = 0
    filtered_out_resolved_before_cutoff: int = 0
    kept_total: int = 0
    kept_unresolved: int = 0
    kept_with_ps_links: int = 0


def yt_dt(ms: Optional[int]) -> Optional[str]:
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date().isoformat()


def parse_iso_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def cf_value_to_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, dict):
        for k in ("name", "localizedName", "fullName", "login", "idReadable"):
            if v.get(k):
                return str(v[k])
        if "values" in v and isinstance(v["values"], list):
            return ", ".join(cf_value_to_str(x) for x in v["values"])
        return str(v)
    if isinstance(v, list):
        return ", ".join(cf_value_to_str(x) for x in v)
    return str(v)


def get_custom_field(issue: Dict[str, Any], field_name: str) -> str:
    for cf in issue.get("customFields", []) or []:
        if cf.get("name") == field_name:
            return cf_value_to_str(cf.get("value"))
    return ""


def normalize_ps_version(v: str) -> str:
    if not v:
        return ""
    v = v.strip()
    v = v.split(",", 1)[0].strip()
    v = re.split(r"\s+", v, 1)[0].strip()
    return v


def calc_lifetime(created_str: Optional[str], resolved_str: Optional[str]) -> str:
    if not created_str or not resolved_str:
        return ""
    created = np.datetime64(created_str)
    resolved = np.datetime64(resolved_str)
    return str(int(np.busday_count(created, resolved)))


def calc_quarter_month(created_str: Optional[str]) -> Tuple[str, str]:
    if not created_str:
        return "", ""
    dt = datetime.strptime(created_str, "%Y-%m-%d").date()
    q = (dt.month - 1) // 3 + 1
    quarter = f"Q{q} {dt.year}"
    month = dt.strftime("%b %Y")
    return quarter, month


def build_defects_dataframe(
    issues: List[Dict[str, Any]],
    *,
    resolved_cutoff: str,
    field_status: str,
    field_priority: str,
    field_release: str,
    ps_project: str,
    ps_version_field: str,
) -> Tuple[pd.DataFrame, ExportStats]:
    """
    From raw issues JSON -> DataFrame with required columns + stats.
    Filtering rule:
      - exclude issues where Resolved < cutoff
      - include issues where Resolved is empty
    """
    cutoff = parse_iso_date(resolved_cutoff)
    stats = ExportStats(total_fetched=len(issues))

    rows: List[Dict[str, Any]] = []

    for it in issues:
        issue_id = it.get("idReadable") or it.get("id")
        summary = it.get("summary", "")

        created = yt_dt(it.get("created"))
        resolved_str = yt_dt(it.get("resolved"))
        resolved_dt = parse_iso_date(resolved_str) if resolved_str else None

        if resolved_dt is not None and resolved_dt < cutoff:
            stats.filtered_out_resolved_before_cutoff += 1
            continue

        stats.kept_total += 1
        if resolved_dt is None:
            stats.kept_unresolved += 1

        status = get_custom_field(it, field_status)
        priority = get_custom_field(it, field_priority)
        release = get_custom_field(it, field_release)

        quarter, month = calc_quarter_month(created)
        lifetime = calc_lifetime(created, resolved_str)

        ps_ids: List[str] = []
        ps_versions: List[str] = []

        for link in it.get("links", []) or []:
            for linked in link.get("issues", []) or []:
                prj = (linked.get("project") or {}).get("shortName")
                if prj != ps_project:
                    continue
                linked_id = linked.get("idReadable", "")
                if linked_id:
                    ps_ids.append(linked_id)

                v_raw = get_custom_field(linked, ps_version_field)
                v = normalize_ps_version(v_raw)
                if v:
                    ps_versions.append(v)

        # dedupe keep order
        ps_ids = list(dict.fromkeys(ps_ids))
        ps_versions = list(dict.fromkeys(ps_versions))

        if ps_ids:
            stats.kept_with_ps_links += 1

        rows.append({
            "id": issue_id,
            "summary": summary,
            "Статус": status,
            "Приоритет": priority,
            "Created": created or "",
            "Quarter": quarter,
            "Month": month,
            "Resolved": resolved_str or "",
            "Lifetime": lifetime,
            "Релиз": release,
            "PS links (IDs)": ", ".join(ps_ids),
            ps_version_field: ", ".join(ps_versions),
        })

    df = pd.DataFrame(rows)
    return df, stats