from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Dict, Set

from dotenv import load_dotenv


def _to_int_or_none(v: Optional[str]) -> Optional[int]:
    if v is None:
        return None
    v = v.strip()
    return int(v) if v else None


@dataclass(frozen=True)
class Settings:
    base_url: str
    token: str

    # Pagination
    page_size: int
    max_pages: Optional[int]

    # Filters / business rules
    resolved_cutoff: str          # YYYY-MM-DD
    created_from: Optional[str]   # YYYY-MM-DD or None

    # Allowed projects + filename prefixes
    allowed_projects: Set[str]
    file_prefix_by_project: Dict[str, str]

    # Field names (as in UI)
    field_status: str
    field_priority: str
    field_release: str

    field_bill_subsystem: str
    field_bill_category: str
    field_bill_tags: str

    ps_project: str
    ps_version_field: str
    issue_type_defect: str        # "Ошибка" / "Bug" etc.


def load_settings() -> Settings:
    """
    Reads config from:
      1) .env file (if present)
      2) environment variables
    """
    load_dotenv(override=False)

    allowed_projects = {"VM", "BA", "DCI6"}
    file_prefix_by_project = {"VM": "vm", "BA": "bill", "DCI6": "dci"}

    base_url = os.getenv("YT_BASE_URL", "").strip()
    token = os.getenv("YT_TOKEN", "").strip()

    if not base_url or not token:
        raise RuntimeError(
            "Не заданы YT_BASE_URL/YT_TOKEN. Укажи их в .env или переменных окружения."
        )

    page_size = int(os.getenv("PAGE_SIZE", "100"))
    max_pages = _to_int_or_none(os.getenv("MAX_PAGES"))

    return Settings(
        base_url=base_url,
        token=token,

        page_size=page_size,
        max_pages=max_pages,

        resolved_cutoff=os.getenv("RESOLVED_CUTOFF", "2024-07-01").strip(),
        created_from=os.getenv("CREATED_FROM", "").strip() or None,

        allowed_projects=allowed_projects,
        file_prefix_by_project=file_prefix_by_project,

        field_bill_subsystem=os.getenv("FIELD_BILL_SUBSYSTEM", "Подсистема"),
        field_bill_category=os.getenv("FIELD_BILL_CATEGORY", "Категория BILL"),
        field_bill_tags=os.getenv("FIELD_BILL_TAGS", "Тэги"),

        field_status=os.getenv("FIELD_STATUS", "State"),
        field_priority=os.getenv("FIELD_PRIORITY", "Priority"),
        field_release=os.getenv("FIELD_RELEASE", "Релиз"),
        ps_project=os.getenv("PS_PROJECT", "PS"),
        ps_version_field=os.getenv("PS_VERSION_FIELD", "Версия"),
        issue_type_defect=os.getenv("ISSUE_TYPE_DEFECT", "Ошибка"),
    )