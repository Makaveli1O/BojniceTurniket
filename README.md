# QR Turnstile Access Control

Jednoduchá Python aplikácia pre Rockchip (napr. ROCK Pi), ktorá:
- načíta QR kód zo skenera (HID/USB alebo stdin),
- validuje ho voči API endpointu pomocou `access_token`,
- ak je QR kód povolený, vyšle signál na GPIO pin a otvorí turniket,
- pri expirovaní tokenu použije refresh endpoint.

## Požiadavky

- Rockchip SBC s Ubuntu/Debian
- Python 3.8+
- pripojený turniket na GPIO pin (default: `PIN=16`)
- prístup k API (endpoint + refresh token)

## Inštalácia

```bash
git clone https://github.com/your-org/qr-turnstile.git
cd qr-turnstile
make install
```


## Spustenie
```
make run
```

alebo priamo (neodporúčané)

```
python3 qr_turnstile.py
```

## Testovanie
Pre testovanie (napr. na windows), treba:
```
make testrun
```
