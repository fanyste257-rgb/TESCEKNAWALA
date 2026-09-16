import json
import os
import urllib.request
from datetime import datetime, timezone, timedelta

DOMAIN = "janda4dqztv.xyz"

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

WIB = timezone(timedelta(hours=7))
STATE_FILE = "status.json"

API_URL = f"https://trustpositif.glng.my.id/check/{DOMAIN}"


def check_domain():
    try:
        request = urllib.request.Request(
            API_URL,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))

        print("API RESPONSE:")
        print(json.dumps(data, indent=2))

        if "blocked" not in data:
            return "ERROR", "Format API tidak dikenal"

        if data["blocked"] is True:
            return "BLOCKED", "Domain terdeteksi dalam database blokir"

        if data["blocked"] is False:
            return "NOT_BLOCKED", "Domain tidak ditemukan dalam database blokir"

        return "ERROR", "Status tidak dapat ditentukan"

    except Exception as e:
        return "ERROR", str(e)


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        response.read()


def load_previous_status():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("status")
    except Exception:
        return None


def save_status(status):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "domain": DOMAIN,
                "status": status,
                "checked_at": datetime.now(WIB).isoformat()
            },
            f,
            indent=2
        )


def main():
    status, detail = check_domain()

    waktu = datetime.now(WIB).strftime("%d-%m-%Y %H:%M:%S")

    if status == "BLOCKED":
        status_text = "🔴 TERBLOKIR"

    elif status == "NOT_BLOCKED":
        status_text = "🟢 TIDAK TERBLOKIR"

    else:
        status_text = "🟡 TIDAK DAPAT DIVERIFIKASI"

    message = f"""🛡️ TRUSTPOSITIF MONITOR

Domain: {DOMAIN}

Status: {status_text}

Detail:
{detail}

Waktu: {waktu} WIB

Sumber pemeriksaan:
TrustPositif / Nawala relay
"""

    previous_status = load_previous_status()

    # Kirim selalu untuk sementara, supaya kita bisa memastikan
    # hasil pemeriksaan benar-benar masuk ke Telegram.
    send_telegram(message)

    save_status(status)

    print(message)
    print(f"Previous status: {previous_status}")
    print(f"Current status: {status}")


if __name__ == "__main__":
    main()
