import json
import os
import urllib.request
from datetime import datetime, timezone, timedelta

DOMAIN = "janda4dqztv.xyz"

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

WIB = timezone(timedelta(hours=7))
STATE_FILE = "status.json"

API_URL = "https://trustpositif.id/api/v1/check"


def check_domain():
    try:
        payload = json.dumps({
            "domains": DOMAIN
        }).encode("utf-8")

        request = urllib.request.Request(
            API_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0"
            },
            method="POST"
        )

        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")

        print("API RESPONSE:")
        print(raw)

        data = json.loads(raw)

        # Cari hasil domain dari berbagai kemungkinan format respons
        result = None

        if isinstance(data, dict):
            if DOMAIN in data:
                result = data[DOMAIN]

            elif "results" in data and isinstance(data["results"], list):
                for item in data["results"]:
                    if isinstance(item, dict):
                        if item.get("domain") == DOMAIN:
                            result = item
                            break

            elif "data" in data:
                if isinstance(data["data"], list):
                    for item in data["data"]:
                        if isinstance(item, dict):
                            if item.get("domain") == DOMAIN:
                                result = item
                                break
                elif isinstance(data["data"], dict):
                    result = data["data"]

        if result is None:
            return "ERROR", "Format respons API tidak dikenali: " + raw[:1000]

        # Periksa nilai blocked
        blocked = result.get("blocked")

        if blocked is True:
            return "BLOCKED", "Domain terdeteksi dalam database blokir TrustPositif"

        if blocked is False:
            return "NOT_BLOCKED", "Domain tidak ditemukan dalam database blokir TrustPositif"

        # Beberapa API menggunakan status
        status = str(result.get("status", "")).lower()

        if status in ["blocked", "terblokir"]:
            return "BLOCKED", "Domain terdeteksi terblokir"

        if status in ["safe", "allowed", "not_blocked", "aman"]:
            return "NOT_BLOCKED", "Domain tidak terdeteksi terblokir"

        return "ERROR", "Status API tidak dikenali: " + str(result)

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

Patokan:
TrustPositif Komdigi
"""

    send_telegram(message)

    save_status(status)

    print(message)


if __name__ == "__main__":
    main()
