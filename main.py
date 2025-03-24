import requests
from bs4 import BeautifulSoup
import time
import smtplib
from email.mime.text import MIMEText

TO_EMAIL = "30753602@sms.telenor.dk"
FROM_EMAIL = "jazzpeter65@gmail.com"
FROM_PASSWORD = "hrtp ewvo lgro fxbn"

URL = "https://udlejning.cej.dk/find-bolig/overblik?p=sj%C3%A6lland"

previous = ""

def send_sms(message_body):
    msg = MIMEText(message_body)
    msg['Subject'] = "Ny CEJ-lejlighed tilbydes!"
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(FROM_EMAIL, FROM_PASSWORD)
        server.send_message(msg)

while True:
    try:
        print("Checker siden...")
        response = requests.get(URL)
        soup = BeautifulSoup(response.text, 'html.parser')

        listings = soup.find_all("div", class_="property-list__item")
        current = "\n".join([item.get_text(strip=True) for item in listings])

        if current != previous and previous != "":
            print("Ny bolig fundet – sender SMS!")
            send_sms("Ny bolig på CEJ – check siden nu!")
        else:
            print("Ingen ændringer.")

        previous = current
        time.sleep(60)

    except Exception as e:
        print("Fejl:", e)
        time.sleep(60)
