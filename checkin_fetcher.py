import requests
import json

import time
import requests


class GoOutAPIClient:
    def __init__(self, base_url: str, token: str, refresh_url: str, refresh_token: str, delay: float = 0.01):
        self.base_url = base_url
        self.token = token
        self.refresh_url = refresh_url
        self.refresh_token = refresh_token
        self.delay = delay
        self.headers = self._make_headers(token)
        self.last_page_index = 0

    # -------------------------------
    # AUTH & TOKEN HANDLING
    # -------------------------------
    def _make_headers(self, token: str) -> dict:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }

    def _refresh_token(self) -> None:
        print("🔄 Token expired, refreshing...")
        response = requests.post(self.refresh_url, json={"refresh_token": self.refresh_token})
        response.raise_for_status()

        new_token = response.json().get("access_token")
        if not new_token:
            raise RuntimeError("Failed to refresh token")

        self.token = new_token
        self.headers = self._make_headers(new_token)
        print("✅ Token refreshed")

    # -------------------------------
    # PAGE FETCHING
    # -------------------------------
    def _fetch_page(self, page_index: int) -> dict:
        url = f"{self.base_url}?pageIndex={page_index}"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 401:
            self._refresh_token()
            response = requests.get(url, headers=self.headers)

        response.raise_for_status()
        return response.json()

    # -------------------------------
    # FETCH METHODS
    # -------------------------------
    def fetch_all_checkins(self) -> list:
        """Načíta všetky záznamy."""
        all_entries = []
        page_index = 0

        while True:
            data = self._fetch_page(page_index)
            entries = data.get("checkInEntries", [])
            all_entries.extend(entries)

            meta = data.get("meta", {})
            print(f"Načítaná stránka {page_index}, počet záznamov: {len(entries)}")

            if not meta.get("hasNext"):
                break

            page_index += 1
            time.sleep(self.delay)

        self.last_page_index = page_index
        return all_entries

    def fetch_last_pages(self, count: int) -> list:
        """Načíta len posledných N strán (napr. 2)."""
        start_page = self.last_page_index + 1 - count

        all_entries = []
        for i in range(start_page, self.last_page_index + 1):
            data = self._fetch_page(i)
            entries = data.get("checkInEntries", [])
            all_entries.extend(entries)
            print(f"Načítaná stránka {i}, počet záznamov: {len(entries)}")
            time.sleep(self.delay)

        return all_entries

class CheckinExporter:
    def __init__(self, filename: str):
        self.filename = filename

    def export_to_json(self, records: list) -> None:
        with open(self.filename, "w", encoding="utf-8") as file:
            json.dump(records, file, ensure_ascii=False, indent=2)
        print(f"Hotovo! Spolu uložených záznamov: {len(records)}")