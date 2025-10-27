import time
import requests

try:
    from periphery.gpio import GPIO
except ImportError:
    print("WARNING: Periphery.gpio module not found. Running in test mode. ❌\n")
    from GPIOStub import GPIOStub as GPIO

from checkin_fetcher import GoOutAPIClient, CheckinExporter
from ticket_checker import TicketExtractor, FileExporter 


class TurnstileController:
    def __init__(self, turnstile_pin: int):
        try:
            self.turnstile = GPIO(turnstile_pin, "out")
        except Exception:
            print("ERROR: Could not access GPIO. Try running with sudo. ❌")
            exit(1)
        self.turnstile.write(False)

    def open_gate(self, duration: int = 2):
        print("Gate OPEN")
        self.turnstile.write(True)
        time.sleep(duration)
        self.turnstile.write(False)

    def close(self):
        self.turnstile.close()


class QRValidator:
    """Validačný modul – aktualizuje a porovnáva QR kódy z API."""

    def __init__(self, api_client: GoOutAPIClient, cache_file: str = "checkin_entries.json"):
        self.api_client = api_client
        self.cache_file = cache_file
        self.valid_qr_codes = set()

    def update_local_cache(self, pages: int | None = None):
        """Načíta všetky záznamy z API alebo len posledné X strán."""
        print("Sťahujem platné QR kódy z GoOut API...")
        data = self.api_client.fetch_all_checkins()
        CheckinExporter(self.cache_file).export_to_json(data)

        extractor = TicketExtractor(self.cache_file)
        self.valid_qr_codes = extractor.extract_ticket_ids()
        print(f"Načítaných platných QR: {len(self.valid_qr_codes)} ✅")

    def is_valid(self, qr_code: str) -> bool:
        if qr_code in self.valid_qr_codes:
            return True

        print("⚠️ QR kód nenájdený – aktualizujem posledné 2 strany...")
        new_data = self.api_client.fetch_last_pages(2)

        if not new_data:
            return False

        extractor = TicketExtractor.from_data(new_data)
        new_codes = extractor.extract_ticket_ids()
        self.valid_qr_codes.update(new_codes)

        return qr_code in self.valid_qr_codes



class QRScannerApp:
    def __init__(self, controller: TurnstileController, validator: QRValidator):
        self.controller = controller
        self.validator = validator

    def run(self):
        self.validator.update_local_cache()
        try:
            while True:
                qr_code = input("Scan QR code: ").strip()
                if not qr_code:
                    continue

                if self.validator.is_valid(qr_code):
                    print("✅ QR code allowed")
                    self.controller.open_gate()
                else:
                    # self.validator.update_local_cache()
                    print("❌ QR code denied")

        except KeyboardInterrupt:
            print("\nUkončené používateľom.")
        finally:
            self.controller.close()


if __name__ == "__main__":
    api_client = GoOutAPIClient(
        base_url="https://goout.net/services/entitystore/v1/checkin-entries",
        token="eyJhbGciOiJIUzUxMiJ9.eyJpYXQiOjE3NjE1NzgyOTYsInN1YiI6IjM2OTQ4NDkifQ.30gTaik-K4elsqV8iyfMKFdlPqWwN87b2y2qAgCrJx9iG03lNqU2Y6Fxa-EdE_xPTSRnZvPXx90PDrUM7OXOQQ",
        refresh_url="https://goout.net/services/user/v3/refresh-tokens",
        refresh_token="eyJhbGciOiJIUzUxMiJ9.eyJpYXQiOjE3NjE1NzgyOTYsInN1YiI6IjM2OTQ4NDkifQ.Wply03BsAwr7ESq3FMAcb-MIOS4z5y3qyEEqH6J_FAFVrS4egWr9rqmKNTRJLBRvnADfYjr3sjn4SnbX5SXzAw"
    )

    controller = TurnstileController(turnstile_pin=0)
    validator = QRValidator(api_client)

    app = QRScannerApp(controller, validator)
    app.run()

