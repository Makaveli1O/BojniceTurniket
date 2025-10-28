import time
import requests
from typing import Optional

try:
    import mraa
except ImportError:
    print("WARNING: mraa gpio module not found. Running in test mode. ❌\n")
    from GPIOStub import GPIOStub as GPIO

from checkin_fetcher import GoOutAPIClient, CheckinExporter
from ticket_checker import TicketExtractor, FileExporter


class TurnstileController:
    def __init__(self, turnstile_pin: int):
        try:
            self.turnstile = mraa.Gpio(turnstile_pin)
            # self.turnstile.dir(mraa.DIR_OUT) # set mode as input
        except Exception:
            print("ERROR: Could not access GPIO. Try running with sudo. ❌")
            exit(1)
        self.turnstile.write(0)

    def open_gate(self, duration: int = 2):
        print("Gate OPEN")
        self.turnstile.write(1)
        time.sleep(duration)
        self.turnstile.write(0)

    def close(self):
        self.turnstile.write(0)


class QRValidator:
    """Validačný modul – aktualizuje a porovnáva QR kódy z API."""

    def __init__(self, api_client: GoOutAPIClient, cache_file: str = "checkin_entries.json"):
        self.api_client = api_client
        self.cache_file = cache_file
        self.valid_qr_codes = set()

    def update_local_cache(self, pages: Optional[int] = None):
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
                    print("❌ QR code denied")

        except KeyboardInterrupt:
            print("\nUkončené používateľom.")
        finally:
            self.controller.close()


if __name__ == "__main__":
    api_client = GoOutAPIClient(
        base_url="https://goout.net/services/entitystore/v1/checkin-entries",
        token="YOUR_TOKEN",
        refresh_url="https://goout.net/services/user/v3/refresh-tokens",
        refresh_token="YOUR_REFRESH_TOKEN"
    )

    controller = TurnstileController(turnstile_pin=0)
    validator = QRValidator(api_client)
    app = QRScannerApp(controller, validator)
    app.run()
