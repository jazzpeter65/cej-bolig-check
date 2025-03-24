import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import os
import logging
import difflib

logging.basicConfig(level=logging.INFO, format='%(message)s')

logging.info("Starter CEJ bolig-tjek...")

FROM_EMAIL = os.environ.get("FROM_EMAIL")
FROM_PASSWORD = os.environ.get("FROM_PASSWORD")
TO_EMAIL = os.environ.get("TO_EMAIL") + ", dortheskovgaard@dadlnet.dk, dskovgaard@hotmail.com"

if not FROM_EMAIL or not FROM_PASSWORD or not TO_EMAIL:
    logging.error("❌ En eller flere environment-variabler mangler!")
    exit(1)

URL = "https://udlejning.cej.dk/find-bolig/overblik?collection=residences&monthlyPrice=0-8000&p=sj%C3%A6lland%2Ck%C3%B8benhavn&types=apartment"
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

def send_sms(message_body):
    logging.info("🔔 Sender besked...")
    msg = MIMEText(message_body)
    msg["Subject"] = "Ny CEJ-lejlighed(er)!"
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(FROM_EMAIL, FROM_PASSWORD)
        server.send_message(msg)
    logging.info("✅ Besked sendt til mobil og e-mail!")

def check_site():
    logging.info("🔍 Tjekker CEJ-siden...")
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "html.parser")

    listings = soup.find_all("div", class_="property-list__item")
    current_lines = [item.get_text(strip=True) for item in listings]
    previous_lines = get_previous_lines()

    logging.info(f"📦 Fundet {len(current_lines)} opslag.")
    if current_lines != previous_lines and previous_lines:
        diff = list(difflib.unified_diff(previous_lines, current_lines, lineterm=''))
        changes = []
        for line in diff:
            if line.startswith("+ ") and not line.startswith("+++"):
                changes.append(f"+ {line[2:]}")
            elif line.startswith("- ") and not line.startswith("---"):
                changes.append(f"- {line[2:]}")
        if changes:
            body = "\n".join(changes[:10])  # max 10 linjer i besked
            logging.info("🚨 Ændringer fundet:\n" + body)
            send_sms(body)
    else:
        logging.info("✅ Ingen ændringer.")
    save_current_lines(current_lines)

check_site()
