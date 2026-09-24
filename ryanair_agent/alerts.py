
import os
import ssl
import smtplib
import requests
from email.message import EmailMessage
from typing import List, Optional
from dotenv import load_dotenv

def get_email_config_from_env():
    return {
        "host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "user": os.environ.get("SMTP_USERNAME"),
        "password": os.environ.get("SMTP_PASSWORD"),
        "from_addr": os.environ.get("SMTP_FROM"),
        "to_addrs": [a.strip() for a in os.environ.get("ALERT_TO", "").split(",") if a.strip()],
        "use_tls": os.environ.get("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes"),
    }

def send_email_sendgrid( subject: str,
    html_body: str,
    text_body: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    from_addr: Optional[str] = None,
    to_addrs: Optional[List[str]] = None,
    use_tls: bool = True,
):
    # Carica variabili da .env
    load_dotenv()

    # Verifica se l'invio è abilitato
    if os.getenv("ALERT_EMAIL_ENABLED") != "1":
        print("Invio email disabilitato.")
        exit()

    # Parametri da .env
    smtp_from = os.getenv("SMTP_FROM")
    smtp_to = os.getenv("ALERT_TO")


    if html_body:
       body=html_body


    # Costruzione del payload per SendGrid
    data = {
        "personalizations": [
            {
                "to": [{"email": smtp_to}],
                "subject": subject
            }
        ],
        "from": {"email": smtp_from},
        "content": [
            {
                "type": "text/html",
                "value": body
            }
        ]
    }

    # Invio della richiesta
    response = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {sendgrid_api_key}",
            "Content-Type": "application/json"
        },
        json=data
    )
    print(data)
    # Risultato
    if response.status_code == 202:
        print("Email inviata con successo tramite SendGrid.")
    else:
        print(f"Errore durante l'invio dell'email: {response.status_code} - {response.text}")


def send_email(
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    from_addr: Optional[str] = None,
    to_addrs: Optional[List[str]] = None,
    use_tls: bool = True,
):
    try:
        # Carica variabili da .env
        load_dotenv()

        # Verifica se l'invio è abilitato
        if os.getenv("ALERT_EMAIL_ENABLED") != "1":
            print("Invio email disabilitato.")
            exit()

        port = os.getenv("SMTP_PORT")
        host = os.getenv("SMTP_HOST")
        user = os.getenv("SMTP_USERNAME")
        password = os.getenv("SMTP_PASSWORD")
        from_addr = os.getenv("SMTP_FROM")
        to_addrs = os.getenv("ALERT_TO")
        use_tls = os.getenv("SMTP_USE_TLS")

        if not (host and port and from_addr and to_addrs):
            raise ValueError("Email config incompleta: controlla SMTP_HOST/PORT, SMTP_FROM, ALERT_TO")
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addrs

        if text_body:
            msg.set_content(text_body)
        else:
            msg.set_content("Vedi versione HTML")

        if html_body:
            msg.add_alternative(html_body, subtype="html")

        if use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(host, port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                if user and password:
                    server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP_SSL(host, port) as server:
                if user and password:
                    server.login(user, password)
                server.send_message(msg)
    except Exception as e:
        print(e)



def send_telegram(body):
    TOKEN = "8925200975:AAE-Q3DNo-beMnSjlyjcZ9fSf-CV4_FeFcI"
    CHAT_ID = "8661312122"
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": body,
        "parse_mode": "Markdown"
    }

    response = requests.post(url, json=payload)
    return response.json()
