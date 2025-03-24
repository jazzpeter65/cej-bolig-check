import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import os

print("Starter CEJ bolig-tjek...", flush=True)

FROM_EMAIL = os.environ.get("FROM_EMAIL")
FROM_PASSWORD = os.environ.get("FROM_PASSWORD")
TO_EMAIL = os.environ.get("TO_EMAIL")

if not FROM_EMAIL or not FROM_PASSWORD or not TO_EMAIL:
    print("❌ En eller flere environment-variabler mangler!", flush=True)
    exit(1)

URL = "https://udlejning.cej.dk/find-bolig/overblik?collection=residences&monthlyPrice=0-50000&p=sj%C3%A6lland%2Ck%C3%B8benhavn&types=apartment"
PREVIOUS_FILE = "previous.txt"

def get_previous():
    try:
        with open(PREVIOUS_FILE, "r") as f:
            return f.read()
    except FileNotFoundError:
        return ""

def save_current(content):
    with open(PREVIOUS_FILE, "w") as f:
        f.write(content)

def send_sms(message_body):
    print("🔔 Sender SMS...", flush=True)
    msg = MIMEText(message_body)
    msg["Subject"] = "Ny CEJ-lejlighed!"
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(FROM_EMAIL, FROM_PASSWORD)
        server.send_message(msg)
    print("✅ SMS sendt!", flush=True)

def check_site():
    print("🔍 Tjekker CEJ-siden...", flush=True)
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "html.parser")

    listings = soup.find_all("div", class_="property-list__item")
    current = "\n".join([item.get_text(strip=True) for item in listings])
    previous = get_previous()

    print(f"📦 Fundet {len(listings)} opslag.", flush=True)
    if current != previous and previous != "":
        print("🚨 Ændring fundet – sender SMS!", flush=True)
        send_sms("Ny bolig under 8000 kr – tjek CEJ nu!")
    else:
        print("✅ Ingen ændringer.", flush=True)
    save_current(current)

check_site()
