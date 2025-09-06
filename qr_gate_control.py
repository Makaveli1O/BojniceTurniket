import requests
import time
from periphery import GPIO

API_URL = "https://example.com/api/qr-codes/validate"
REFRESH_URL = "https://example.com/api/auth/refresh"
TURNSTILE_PIN = 0  

ACCESS_TOKEN = "INITIAL_TOKEN"
REFRESH_TOKEN = "REFRESH_TOKEN"

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
    global ACCESS_TOKEN
    try:
        response = requests.post(API_URL, json={"qr": qr_code}, headers=get_headers(), timeout=5)

        if response.status_code in (401, 403):  # token expiroval
            print("Access token expired, refreshing...")
            refresh_access_token()
            # retry once
            response = requests.post(API_URL, json={"qr": qr_code}, headers=get_headers(), timeout=5)

        response.raise_for_status()
        data = response.json()
        return data.get("allowed", False)
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
