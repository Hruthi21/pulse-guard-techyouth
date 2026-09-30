import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)

with app.app_context():
    try:
        msg = Message("PulseGuard Live SMTP Test", recipients=["jayanthgowda1406@gmail.com"])
        msg.body = "Hello Dr. Jayanth,\n\nPulseGuard AI SMTP email connection is now 100% verified and operational!"
        mail.send(msg)
        print("EMAIL SENT SUCCESSFULLY!")
    except Exception as e:
        print("ERROR:", e)
