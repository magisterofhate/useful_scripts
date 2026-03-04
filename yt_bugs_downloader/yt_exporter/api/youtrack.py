from __future__ import annotations

from typing import Any, Dict, List, Optional
import requests


class YouTrackClient:
    def __init__(self, base_url: str, token: str, timeout: int = 60) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        })
        self.timeout = timeout

    def fetch_issues(
        self,
        query: str,
        fields: str,
        page_size: int = 100,
        max_pages: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        GET /api/issues with pagination ($top/$skip).
        """
        url = f"{self.base_url}/api/issues"
        results: List[Dict[str, Any]] = []
        skip = 0
        page = 0

        while True:
            if max_pages is not None and page >= max_pages:
                break

            params = {
                "query": query,
                "fields": fields,
                "$top": page_size,
                "$skip": skip,
            }

            r = self.session.get(url, params=params, timeout=self.timeout)
            if r.status_code >= 400:
                # полезно оставить диагностический текст
                raise RuntimeError(f"HTTP {r.status_code}: {r.text}")

            batch = r.json()
            if not batch:
                break

            results.extend(batch)

            if len(batch) < page_size:
                break

            skip += page_size
            page += 1

        return results