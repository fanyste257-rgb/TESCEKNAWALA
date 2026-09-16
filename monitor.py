import json
import os
import socket
import subprocess
from datetime import datetime, timezone, timedelta
import urllib.parse
import urllib.request

DOMAIN = "janda4dqztv.xyz"

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

WIB = timezone(timedelta(hours=7))
STATE_FILE = "status.json"

DNS_SERVERS = [
    "103.155.26.28",
    "103.155.26.29",
]


def check_dns(server):
    """
    Query DNS TrustPositif/Komdigi using dig.
    We inspect the complete response for:
    - EDE 15 (Blocked)
    - trustpositif.komdigi.go.id
    - komdigi
    """

    command = [
        "dig",
        f"@{server}",
        DOMAIN,
        "A",
        "+comments",
        "+answer",
        "+time=5",
        "+tries=1",
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=15
    )

    output = (
        result.stdout +
        "\n" +
        result.stderr
    ).lower()

    if "ede: 15" in output:
        return "BLOCKED", output

    if "trustpositif.komdigi.go.id" in output:
        return "BLOCKED", output

    if "block-list-zone" in output:
        return "BLOCKED", output

    if result.returncode != 0:
        return "ERROR", output

    # If DNS returned an answer without a block indicator
    if "answer section" in output:
        return "NOT_BLOCKED", output

    return "ERROR", output


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(status):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "status": status,
                "domain": DOMAIN
            },
            f,
            indent=2
        )


def send_telegram(message):
    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/sendMessage"
    )

    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }).encode()

    request = urllib.request.Request(
        url,
        data=data,
        method="POST"
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:
        return response.read()


def main():

    now = datetime.now(WIB)
    previous = load_state()

    results = []

    for server in DNS_SERVERS:

        try:
            status, raw = check_dns(server)

            results.append({
                "server": server,
                "status": status
            })

        except Exception as error:

            results.append({
                "server": server,
                "status": "ERROR",
                "error": str(error)
            })

    blocked_count = sum(
        1 for r in results
        if r["status"] == "BLOCKED"
    )

    error_count = sum(
        1 for r in results
        if r["status"] == "ERROR"
    )

    if blocked_count >= 1:

        overall_status = "BLOCKED"
        emoji = "🔴"
        description = "TERINDIKASI DIBLOKIR"

    elif error_count == len(results):

        overall_status = "ERROR"
        emoji = "🟡"
        description = "TIDAK DAPAT DIVERIFIKASI"

    else:

        overall_status = "NOT_BLOCKED"
        emoji = "🟢"
        description = "TIDAK TERINDIKASI DIBLOKIR"

    lines = [
        "🛡️ TRUSTPOSITIF MONITOR",
        "",
        f"Domain:",
        DOMAIN,
        "",
        f"Status:",
        f"{emoji} {description}",
        "",
        "DNS TrustPositif/Komdigi:"
    ]

    for result in results:

        if result["status"] == "BLOCKED":
            icon = "🔴"

        elif result["status"] == "NOT_BLOCKED":
            icon = "🟢"

        else:
            icon = "🟡"

        lines.append(
            f"{icon} {result['server']} — "
            f"{result['status']}"
        )

    lines.extend([
        "",
        f"Waktu:",
        now.strftime("%d-%m-%Y %H:%M:%S") + " WIB",
        "",
        "Patokan:",
        "TrustPositif Komdigi"
    ])

    send_telegram("\n".join(lines))

    old_status = previous.get("status")

    if old_status and old_status != overall_status:

        change_message = (
            "🚨 STATUS TRUSTPOSITIF BERUBAH\n\n"
            f"Domain:\n{DOMAIN}\n\n"
            f"Sebelumnya:\n{old_status}\n\n"
            f"Sekarang:\n{overall_status}\n\n"
            f"Waktu:\n"
            f"{now.strftime('%d-%m-%Y %H:%M:%S')} WIB"
        )

        send_telegram(change_message)

    save_state(overall_status)


if __name__ == "__main__":
    main()
