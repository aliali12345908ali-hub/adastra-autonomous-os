import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email_report():
    # إعدادات البريد الإلكتروني (يمكنك تعديلها)
    sender_email = "your.email@gmail.com"
    app_password = "your_app_password_here"  # كلمة مرور التطبيقات من جوجل
    recipient_email = "your.email@gmail.com" # البريد المستلم

    subject = "📊 ADASTRA OS - Rapport Financier Automatique"
    
    body = """Bonjour Mr ABDALLAH BEN BELGACEM,

Voici le résumé financier automatique de votre activité Micro-entrepreneur :

- Chiffre d'Affaires Total Collecté : 3,480.00 EUR
- Statut des Factures (4/4) :
  1. ADASTRA-2026-001 : 900.00 EUR [ PAYÉ sur Nickel ]
  2. ADASTRA-2026-002 : 1,020.00 EUR [ PAYÉ sur Nickel ]
  3. ADASTRA-2026-003 : 540.00 EUR [ PAYÉ sur Nickel ]
  4. ADASTRA-2026-004 : 1,020.00 EUR [ PAYÉ sur Nickel ]

Toutes les factures sont validées à 100%.

Cordialement,
ADASTRA Autonomous OS
"""

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        print("⏳ Connexion au serveur SMTP...")
        # استخدام خادم Gmail كمثال
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        # server.login(sender_email, app_password)
        # server.send_message(msg)
        # server.quit()
        print("✅ Rapport financier préparé avec succès !")
        print(f"📧 Destinataire : {recipient_email}")
        print("💡 Pour activer l'envoi réel, ajoutez votre Mot de Passe d'application Gmail dans email_notifier.py.")
    except Exception as e:
        print(f"❌ Erreur d'envoi : {e}")

if __name__ == "__main__":
    send_email_report()
