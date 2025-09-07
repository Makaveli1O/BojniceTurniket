from flask import Flask, request, jsonify
import time
import secrets

app = Flask(__name__)

TOKENS = {}
QR_CODES = ["QRCODE-123", "QRCODE-456", "QRCODE-789"]

@app.route("/refresh-token", methods=["POST"])
def refresh_token():
    new_token = secrets.token_hex(16)
    expires_at = int(time.time()) + 60  # platnosť 60s pre testovaci eúčely
    TOKENS[new_token] = expires_at
    return jsonify({
        "access_token": new_token,
        "expires_at": expires_at
    })

@app.route("/qr-codes", methods=["GET"])
def get_qr_codes():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid token"}), 401

    token = auth_header.split(" ")[1]
    expiry = TOKENS.get(token)
    if not expiry or expiry < time.time():
        return jsonify({"error": "Token expired or invalid"}), 401

    return jsonify({"qr_codes": QR_CODES})

if __name__ == "__main__":
    app.run(port=5000, debug=True)
