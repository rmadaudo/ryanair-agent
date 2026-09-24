import os
import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv

# Carica variabili da .env
load_dotenv()

# Controlla se l'invio è abilitato
if os.getenv("ALERT_EMAIL_ENABLED") != "1":
    print("Invio email disabilitato.")
    exit()

# Parametri da .env
smtp_host = os.getenv("SMTP_HOST")
smtp_port = int(os.getenv("SMTP_PORT"))
smtp_user = os.getenv("SMTP_USERNAME")
smtp_pass = os.getenv("SMTP_PASSWORD")
smtp_from = os.getenv("SMTP_FROM")
smtp_to = os.getenv("ALERT_TO")
use_tls = os.getenv("SMTP_USE_TLS", "false").lower() == "true"

# Contenuto dell'email
subject = "Alert dal sistema"
body = "Questo è un messaggio di test inviato via SMTP da uno script Python."

# Crea il messaggio
msg = EmailMessage()
msg.set_content(body)
msg['Subject'] = subject
msg['From'] = smtp_from
msg['To'] = smtp_to

# Invio email
try:
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        if use_tls:
            context = ssl.create_default_context()
            server.starttls(context=context)
            server.ehlo()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        print("Email inviata con successo.")
except Exception as e:
    print(f"Errore durante l'invio dell'email: {e}")
