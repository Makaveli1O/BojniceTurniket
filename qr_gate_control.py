import requests
import time

try:
    from periphery.gpio import GPIO
except ImportError:
    from GPIOStub import GPIOStub as GPIO
    

API_URL = "http://localhost:5000/qr-codes"
REFRESH_URL = "http://localhost:5000/refresh-token"
TURNSTILE_PIN = 0

ACCESS_TOKEN = "INITIAL_TOKEN"
REFRESH_TOKEN = "REFRESH_TOKEN"
QR_CODES_FIELD = "qr_codes"

turnstile = GPIO(TURNSTILE_PIN, "out")
turnstile.write(False)

def get_headers():
    return {"Authorization": f"Bearer {ACCESS_TOKEN}"}

def refresh_access_token():
    global ACCESS_TOKEN
    try:
        response = requests.post(REFRESH_URL, json={"refresh_token": REFRESH_TOKEN}, timeout=5)
        response.raise_for_status()
        data = response.json()
        ACCESS_TOKEN = data["access_token"]
        print("Access token refreshed 🔑")
    except Exception as e:
        print(f"Error refreshing token: {e}")

def validate_qr(qr_code: str) -> bool:
    """Downloads QRcodes list from API every time new QR code is proposed to scanner.
    If access_token is invalid, refresh it.
    Args:
        qr_code (str): input QR

    Returns:
        bool: True if qr is valid, false otherwise.
    """
    global ACCESS_TOKEN
    try:
        response = requests.get(API_URL, headers=get_headers(), timeout=5)

        if response.status_code in (401, 403):  # token expired
            print("Access token expired, refreshing...")
            refresh_access_token()
            # retry once
            response = requests.get(API_URL, headers=get_headers(), timeout=5)

        response.raise_for_status()
        data = response.json()
        valid_qrs = data.get(QR_CODES_FIELD, [])
        return qr_code in valid_qrs
    except Exception as e:
        print(f"Error validating QR: {e}")
        return False


def open_turnstile():
    print("Gate OPEN")
    turnstile.write(True)
    time.sleep(2)
    turnstile.write(False)

def main():
    while True:
        qr_code = input("Scan QR code: ").strip()
        
        if validate_qr(qr_code):
            print("QR code allowed ✅")
            open_turnstile()
        else:
            print("QR code denied ❌")

if __name__ == "__main__":
    try:
        main()
    finally:
        turnstile.close()
