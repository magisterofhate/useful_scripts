import re
import sys
from typing import List, Tuple, Optional

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://msg6.ispsystem.net/vm"
START_PAGE = 1
MAX_PAGES = 100  # предохранитель

VERSION_RE = re.compile(r"^\s*(\d{4}\.\d+\.\d+(?:-\d+)?)\s*$")

STABLE_DATE_RE = re.compile(
    r"Stable\s*date\s*:?\s*(\d{4}[-.]\d{2}[-.]\d{2})",
    re.IGNORECASE
)

RELEASE_DATE_RE = re.compile(
    r"Release\s*date\s*:?\s*(\d{4}[-.]\d{2}[-.]\d{2})",
    re.IGNORECASE
)


def fetch_page(page: int) -> str:
    url = f"{BASE_URL}?page={page}"
    r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.text


def extract_version_cells(soup: BeautifulSoup) -> List[BeautifulSoup]:
    """
    Возвращает список ячеек (td/th), которые являются "первой колонкой" строк таблицы.
    """
    cells = []
    for tr in soup.find_all("tr"):
        row_cells = tr.find_all(["td", "th"], recursive=False)
        if not row_cells:
            # на некоторых страницах td/th могут быть вложены глубже
            row_cells = tr.find_all(["td", "th"])
        if not row_cells:
            continue
        cells.append(row_cells[0])
    return cells


def parse_version_from_cell(cell_text: str) -> Optional[str]:
    """
    В первой колонке обычно есть версия (иногда только один раз на релиз из-за rowspan).
    Берём первую строку/токен, похожий на версию.
    """
    # Пробуем построчно (часто версия отдельной строкой)
    for line in cell_text.splitlines():
        line = line.strip()
        m = VERSION_RE.match(line)
        if m:
            return m.group(1)

    # Фолбэк: найти внутри текста что-то похожее на версию
    m = re.search(r"(\d{4}\.\d+\.\d+(?:-\d+)?)", cell_text)
    return m.group(1) if m else None


def parse_release_date_from_cell(cell_text: str) -> Optional[str]:
    """
    Приоритет:
    1. Stable date
    2. Release date
    """

    stable = STABLE_DATE_RE.search(cell_text)
    if stable:
        return stable.group(1)

    release = RELEASE_DATE_RE.search(cell_text)
    if release:
        return release.group(1)

    return None


def print_table(rows: List[Tuple[str, str]]):
    print(f"{'VERSION':<15} | {'RELEASE_DATE'}")
    print("-" * 34)
    for v, d in rows:
        print(f"{v:<15} | {d}")


def collect_versions() -> List[Tuple[str, str]]:
    """
    Возвращает список (version, release_date) по всем страницам до стоп-условия.
    """
    collected: List[Tuple[str, str]] = []
    seen_versions = set()

    for page in range(START_PAGE, MAX_PAGES + 1):
        html = fetch_page(page)
        soup = BeautifulSoup(html, "lxml")

        version_cells = extract_version_cells(soup)

        found_any_version = False
        stop = False

        for cell in version_cells:
            cell_text = cell.get_text("\n", strip=True)
            version = parse_version_from_cell(cell_text)
            if not version:
                continue

            found_any_version = True

            # стоп-условие: встретили 2023.*
            if version.startswith("2023"):
                stop = True
                break

            if version in seen_versions:
                continue

            stable_date = parse_release_date_from_cell(cell_text)
            if stable_date:
                seen_versions.add(version)
                collected.append((version, stable_date))

        if not found_any_version or stop:
            break

    return collected


def main():
    collected = collect_versions()
    if not collected:
        print("Ничего не нашли. Возможно, данные подгружаются иначе или нужна авторизация/cookie.")
        sys.exit(0)
    print_table(collected)


if __name__ == "__main__":
    main()