import json
import os
import urllib.request
from datetime import datetime, timezone, timedelta

DOMAIN = "janda4dqztv.xyz"

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

WIB = timezone(timedelta(hours=7))
STATE_FILE = "status.json"

API_URL = (
    "https://apiv1.aethercloud.web.id/check"
    "?domain=" + DOMAIN
)


def check_domain():

    try:
        request = urllib.request.Request(
            API_URL,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            }
        )

        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")

        print("API RESPONSE:")
        print(raw)

        data = json.loads(raw)

        results = data.get("results", [])

        if not results:
            return "ERROR", "API tidak mengembalikan hasil domain"

        result = results[0]

        status = str(result.get("status", "")).upper()

        if status == "BLOCKED":
            return "BLOCKED", "Domain terdeteksi TERBLOKIR"

        if status == "SAFE":
            return "NOT_BLOCKED", "Domain terdeteksi TIDAK TERBLOKIR"

        if status == "UNKNOWN":
            return "ERROR", "Status domain UNKNOWN"

        return "ERROR", "Status API: " + status

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

    waktu = datetime.now(WIB).strftime(
        "%d-%m-%Y %H:%M:%S"
    )

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

Sumber:
Nawala / TrustPositif checker
"""


    send_telegram(message)

    save_status(status)

    print(message)


if __name__ == "__main__":
    main()
