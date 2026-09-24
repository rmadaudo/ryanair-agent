import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configurazioni
smtp_server = "smtp.gmail.com"
port = 587  # Porta per TLS
sender_email = "madaudo.rosario@gmail.com"
password = "ytghsdyefkbqzrzh"  # Senza spazi
receiver_email = "madaudo.rosario@gmail.com"

# Creazione del messaggio
message = MIMEMultipart("alternative")
message["Subject"] = "Alert di sistema da PythonAnywhere"
message["From"] = sender_email
message["To"] = receiver_email

text = "Questo è un messaggio di test inviato da PythonAnywhere usando il server SMTP di Gmail."
part = MIMEText(text, "plain")
message.attach(part)

try:
    # Connessione al server SMTP di Gmail
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()  # Abilita la crittografia TLS
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
    print("Email inviata con successo tramite Gmail!")
except Exception as e:
    print(f"Errore durante l'invio: {e}")
