import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

DOMAIN = "janda4dqztv.xyz"

TRUSTPOSITIF_URL = "https://trustpositif.komdigi.go.id/assets/db/domains_isp"

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

WIB = timezone(timedelta(hours=7))
STATE_FILE = "status.json"


def download_blocklist():
    request = urllib.request.Request(
        TRUSTPOSITIF_URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="ignore")


def normalize(value):
    return value.strip().lower().rstrip(".")


def check_domain(data):
    target = normalize(DOMAIN)

    for line in data.splitlines():
        value = normalize(line)

        if not value:
            continue

        value = value.split()[0]

        if value == target:
            return True

    return False


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def save_state(status):
    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump({"status": status}, file)


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }).encode()

    request = urllib.request.Request(
        url,
        data=data,
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def main():
    now = datetime.now(WIB)
    previous = load_state()

    try:
        database = download_blocklist()
        blocked = check_domain(database)

        status = "BLOCKED" if blocked else "NOT_BLOCKED"

        if blocked:
            emoji = "🔴"
            description = "TERDAFTAR / TERINDIKASI DIBLOKIR"
        else:
            emoji = "🟢"
            description = "TIDAK TERDAFTAR"

        message = (
            "🛡️ TRUSTPOSITIF MONITOR\n\n"
            f"Domain:\n{DOMAIN}\n\n"
            f"Status:\n{emoji} {description}\n\n"
            f"Waktu:\n{now.strftime('%d-%m-%Y %H:%M:%S')} WIB\n\n"
            "Sumber:\n"
            "TrustPositif Komdigi"
        )

        send_telegram(message)

        if previous.get("status") and previous["status"] != status:
            change_message = (
                "🚨 STATUS TRUSTPOSITIF BERUBAH\n\n"
                f"Domain:\n{DOMAIN}\n\n"
                f"Sebelumnya:\n{previous['status']}\n\n"
                f"Sekarang:\n{status}\n\n"
                f"Waktu:\n{now.strftime('%d-%m-%Y %H:%M:%S')} WIB"
            )

            send_telegram(change_message)

        save_state(status)

    except Exception as error:
        error_message = (
            "⚠️ TRUSTPOSITIF MONITOR ERROR\n\n"
            f"Domain:\n{DOMAIN}\n\n"
            f"Waktu:\n{now.strftime('%d-%m-%Y %H:%M:%S')} WIB\n\n"
            "Status:\n"
            "🟡 TIDAK DAPAT DIVERIFIKASI\n\n"
            f"Error:\n{str(error)[:1000]}"
        )

        send_telegram(error_message)
        raise


if __name__ == "__main__":
    main()
