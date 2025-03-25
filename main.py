import os
import logging
import smtplib
from email.mime.text import MIMEText
import difflib
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(message)s')

FROM_EMAIL = os.environ.get("FROM_EMAIL")
FROM_PASSWORD = os.environ.get("FROM_PASSWORD")
TO_EMAIL = os.environ.get("TO_EMAIL") + ", dortheskovgaard@dadlnet.dk, dskovgaard@hotmail.com"

if not FROM_EMAIL or not FROM_PASSWORD or not TO_EMAIL:
    logging.error("❌ Manglende environment-variabler.")
    exit(1)

URL = "https://udlejning.cej.dk/find-bolig/overblik"
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
    logging.info("✅ Besked sendt!")

def fetch_listings():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL)
        page.wait_for_timeout(5000)  # vent 5 sek på rendering
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    listings = soup.find_all("div", class_="property-list__item")  # OBS: opdater denne hvis CEJ ændrer layout
    lines = []

    for item in listings:
        text = item.get_text(separator=" – ", strip=True)
        lines.append(text)

    logging.info(f"📦 Fundet {len(lines)} boliger.")
    return lines

def check_site():
    logging.info("🔍 Loader CEJ-siden via Playwright...")
    current_lines = fetch_listings()
    previous_lines = get_previous_lines()

    force_send = True  # True mens du tester

    if current_lines != previous_lines and previous_lines or force_send:
        diff = list(difflib.unified_diff(previous_lines, current_lines, lineterm=''))
        changes = []
        for line in diff:
            if line.startswith("+ ") and not line.startswith("+++"):
                changes.append(f"+ {line[2:]}")
            elif line.startswith("- ") and not line.startswith("---"):
                changes.append(f"- {line[2:]}")
        if not changes and force_send:
            changes = current_lines[:5]
        if changes:
            body = "\n".join(changes[:10])
            logging.info("🚨 Ændringer:\n" + body)
            send_email(body)
    else:
        logging.info("✅ Ingen ændringer.")
    save_current_lines(current_lines)

check_site()
