from __future__ import annotations

import re
from typing import List, Optional, Tuple

import requests
from bs4 import BeautifulSoup


START_PAGE = 1
MAX_PAGES = 100

PROJECT_VERSIONS_URLS = {
    "VM": "https://msg6.ispsystem.net/vm",
    "BA": "https://msg6.ispsystem.net/bill",
    "DCI6": "https://msg6.ispsystem.net/dci",
}

PROJECT_VERSION_PATTERNS = {
    # Пример: 2026.02.2 / 2026.02.2-1
    "VM": re.compile(r"^\s*(\d{4}\.\d{2}\.\d+(?:-\d+)?)\s*$"),
    "DCI6": re.compile(r"^\s*(\d{4}\.\d{2}\.\d+(?:-\d+)?)\s*$"),

    # Пример: 6.136.1 / 6.136.1-1
    "BA": re.compile(r"^\s*(\d+\.\d+\.\d+(?:-\d+)?)\s*$"),
}

DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")


def fetch_page(base_url: str, page: int) -> str:
    """
    Загружает HTML страницы.
    """
    url = f"{base_url}?page={page}"
    response = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    response.raise_for_status()
    return response.text


def extract_rows(soup: BeautifulSoup):
    """
    Возвращает строки таблиц как список списков ячеек.
    """
    rows = []
    for tr in soup.find_all("tr"):
        cells = tr.find_all(["td", "th"], recursive=False)
        if not cells:
            cells = tr.find_all(["td", "th"])
        if not cells:
            continue
        rows.append(cells)
    return rows


def parse_version_from_cell(cell_text: str, version_re: re.Pattern) -> Optional[str]:
    """
    В первой колонке ищем версию по regex, зависящему от проекта.
    """
    for line in cell_text.splitlines():
        line = line.strip()
        match = version_re.match(line)
        if match:
            return match.group(1)

    match = version_re.search(cell_text)
    return match.group(1) if match else None


def parse_release_date_from_text(text: str) -> Optional[str]:
    """
    Логика дат:
    1. Если есть дата после 'Stable date' -> берём её
    2. Иначе если есть дата после 'Release date' -> берём её
    3. Иначе None
    """
    stable_match = re.search(r"Stable date\s*:?\s*(\d{4}-\d{2}-\d{2})", text, flags=re.IGNORECASE)
    if stable_match:
        return stable_match.group(1)

    release_match = re.search(r"Release date\s*:?\s*(\d{4}-\d{2}-\d{2})", text, flags=re.IGNORECASE)
    if release_match:
        return release_match.group(1)

    # fallback: если по каким-то причинам текст размечен иначе
    all_dates = DATE_RE.findall(text)
    if all_dates:
        return all_dates[0]

    return None


def has_data_in_adjacent_cell(row_cells) -> bool:
    """
    Проверяем, что во второй колонке строки есть хоть какие-то данные.
    Если второй колонки нет или она пустая -> версия не учитывается.
    """
    if len(row_cells) < 2:
        return False

    adjacent_text = row_cells[1].get_text(" ", strip=True)
    return bool(adjacent_text)


def collect_versions(project: str) -> List[Tuple[str, str]]:
    """
    Возвращает список (version, release_date).

    Условия:
    - URL зависит от проекта
    - regex версии зависит от проекта
    - версия учитывается только если во второй колонке строки есть данные
    - стоп по 2023.* только для VM/DCI6
    """
    if project not in PROJECT_VERSIONS_URLS:
        raise RuntimeError(f"Неизвестный проект для versions: {project}")

    base_url = PROJECT_VERSIONS_URLS[project]
    version_re = PROJECT_VERSION_PATTERNS[project]

    collected: List[Tuple[str, str]] = []
    seen_versions = set()

    for page in range(START_PAGE, MAX_PAGES + 1):
        html = fetch_page(base_url, page)
        soup = BeautifulSoup(html, "lxml")

        rows = extract_rows(soup)

        found_any_version = False
        stop = False

        for row_cells in rows:
            first_cell_text = row_cells[0].get_text("\n", strip=True)
            version = parse_version_from_cell(first_cell_text, version_re)
            if not version:
                continue

            found_any_version = True

            # стоп-условие только для VM/DCI6
            if project in {"VM", "DCI6"} and version.startswith("2023"):
                stop = True
                break

            if version in seen_versions:
                continue

            # во второй колонке должны быть данные
            if not has_data_in_adjacent_cell(row_cells):
                continue

            # дату ищем по всей строке, а не только по первой ячейке
            row_text = "\n".join(cell.get_text("\n", strip=True) for cell in row_cells)
            release_date = parse_release_date_from_text(row_text)
            if not release_date:
                continue

            seen_versions.add(version)
            collected.append((version, release_date))

        if not found_any_version or stop:
            break

    return collected