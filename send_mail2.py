import os
import requests
from dotenv import load_dotenv

# Carica variabili da .env
load_dotenv()

# Verifica se l'invio è abilitato
if os.getenv("ALERT_EMAIL_ENABLED") != "1":
    print("Invio email disabilitato.")
    exit()

# Parametri da .env
sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
print (sendgrid_api_key)
smtp_from = os.getenv("SMTP_FROM")
smtp_to = os.getenv("ALERT_TO")
subject = os.getenv("EMAIL_SUBJECT", "Alert dal sistema")
body = os.getenv("EMAIL_BODY", "Questo è un messaggio di test inviato via SendGrid API da uno script Python.")

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
            "type": "text/plain",
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
