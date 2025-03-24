import requests
import smtplib
from email.mime.text import MIMEText
import os
import logging
import difflib

logging.basicConfig(level=logging.INFO, format='%(message)s')

logging.info("Starter CEJ API-baseret bolig-tjek...")

FROM_EMAIL = os.environ.get("FROM_EMAIL")
FROM_PASSWORD = os.environ.get("FROM_PASSWORD")
TO_EMAIL = os.environ.get("TO_EMAIL") + ", dortheskovgaard@dadlnet.dk, dskovgaard@hotmail.com"

if not FROM_EMAIL or not FROM_PASSWORD or not TO_EMAIL:
    logging.error("❌ En eller flere environment-variabler mangler!")
    exit(1)

API_URL = "https://udlejning.cej.dk/api/residences?collection=residences&page=1&pageSize=1000"
PREVIOUS_FILE = "previous.txt"

def get_previous_lines():
    try:
        with open(PREVIOUS_FILE, "r") as f:
            return f.read().splitlines()
    except FileNotFoundError:
        return []

def save_current_lines(lines):
    with open(PREVIOUS_FILE, "w") as f:
        f.write("\n".join(lines))

def send_email(message_body):
    logging.info("🔔 Sender besked...")
    msg = MIMEText(message_body)
    msg["Subject"] = "Ændringer på CEJ.dk"
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(FROM_EMAIL, FROM_PASSWORD)
        server.send_message(msg)
    logging.info("✅ Besked sendt til mobil og e-mail!")

def fetch_listings():
    headers = {"User-Agent": "Mozilla/5.0"}  # ← vigtig for CEJ-serveren
    response = requests.get(API_URL, headers=headers)

    logging.info(f"🌐 Statuskode: {response.status_code}")
    logging.info("📄 Rå JSON-udsnit (første 1000 tegn):")
    logging.info(response.text[:1000])

    try:
        data = response.json()
        listings = data.get("items", [])
    except Exception as e:
        logging.error(f"❌ Fejl ved JSON-afkodning: {e}")
        listings = []

    lines = []
    for item in listings:
        address = item.get("address", {}).get("streetName", "") + " " + str(item.get("address", {}).get("streetNumber", ""))
        size = item.get("area", "")
        rent = item.get("monthlyPrice", "")
        rooms = item.get("numberOfRooms", "")
        line = f"{address} – {rooms} vær – {size} m² – {rent} kr"
        lines.append(line)
    return lines

def check_site():
    logging.info("🔍 Henter data fra CEJ API...")
    current_lines = fetch_listings()
    previous_lines = get_previous_lines()

    logging.info(f"📦 Fundet {len(current_lines)} boliger.")

    force_send = True  # ← slå fra bagefter

    if current_lines != previous_lines and previous_lines or force_send:
        diff = list(difflib.unified_diff(previous_lines, current_lines, lineterm=''))
        changes = []
        for line in diff:
            if line.startswith("+ ") and not line.startswith("+++"):
                changes.append(f"+ {line[2:]}")
            elif line.startswith("- ") and not line.startswith("---"):
                changes.append(f"- {line[2:]}")
        if not changes and force_send:
            changes = current_lines[:5]  # Brug de første 5 som test
        if changes:
            body = "\n".join(changes[:10])  # maks 10 linjer i besked
            logging.info("🚨 (Tvunget) beskedindhold:\n" + body)
            send_email(body)
    else:
        logging.info("✅ Ingen ændringer.")
    save_current_lines(current_lines)

check_site()

