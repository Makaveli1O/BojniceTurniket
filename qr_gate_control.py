import requests
import time

try:
    from periphery.gpio import GPIO
except ImportError:
    """This is for testing purposes mostly on windows machines. For this script
    to work, periphery.gpio library must be installed (it is linux onlny).
    """
    print("WARNING: Periphery.gpio module could not be resolved. ❌\n Running the script in test mode.\n")
    from GPIOStub import GPIOStub as GPIO


class TurnstileController:
    def __init__(self, turnstile_pin: int, api_url: str, refresh_url: str,
                 access_token: str, refresh_token: str, qr_codes_field: str = "qr_codes"):
        try:
            self.turnstile = GPIO(turnstile_pin, "out")
        except:
            print("ERROR: Could not access GPIO. Try running the script in sudo mode.❌\n")
            exit()

        self.turnstile.write(False)
        
        self.api_url = api_url
        self.refresh_url = refresh_url
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.qr_codes_field = qr_codes_field

    def get_headers(self):
        return {"Authorization": f"Bearer {self.access_token}"}

    def refresh_access_token(self):
        try:
            response = requests.post(self.refresh_url, json={"refresh_token": self.refresh_token}, timeout=5)
            response.raise_for_status()
            data = response.json()
            self.access_token = data["access_token"]
            print("Access token refreshed 🔑")
        except Exception as e:
            print(f"Error refreshing token: {e}")

    def validate_qr(self, qr_code: str) -> bool:
        """Check QR code validity by fetching list from API."""
        try:
            response = requests.get(self.api_url, headers=self.get_headers(), timeout=5)

            if response.status_code in (401, 403):
                print("Access token expired, refreshing...")
                self.refresh_access_token()
                # retry once
                response = requests.get(self.api_url, headers=self.get_headers(), timeout=5)

            response.raise_for_status()
            data = response.json()
            valid_qrs = data.get(self.qr_codes_field, [])
            return qr_code in valid_qrs
        except Exception as e:
            print(f"Error validating QR: {e}")
            return False

    def open_turnstile(self, duration: int = 2):
        print("Gate OPEN")
        self.turnstile.write(True)
        time.sleep(duration)
        self.turnstile.write(False)

    def close(self):
        self.turnstile.close()


class QRScannerApp:
    def __init__(self, controller: TurnstileController):
        self.controller = controller

    def run(self):
        try:
            while True:
                qr_code = input("Scan QR code: ").strip()
                if self.controller.validate_qr(qr_code):
                    print("QR code allowed ✅")
                    self.controller.open_turnstile()
                else:
                    print("QR code denied ❌")
        finally:
            self.controller.close()


if __name__ == "__main__":
    controller = TurnstileController(
        turnstile_pin=0,
        api_url="http://localhost:5000/qr-codes",
        refresh_url="http://localhost:5000/refresh-token",
        access_token="INITIAL_TOKEN",
        refresh_token="REFRESH_TOKEN"
    )
    app = QRScannerApp(controller)
    app.run()
