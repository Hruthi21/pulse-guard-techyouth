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

print("Config:")
print("Server:", app.config['MAIL_SERVER'])
print("Port:", app.config['MAIL_PORT'])
print("TLS:", app.config['MAIL_USE_TLS'])
print("Username:", app.config['MAIL_USERNAME'])
print("Password length:", len(app.config['MAIL_PASSWORD']) if app.config['MAIL_PASSWORD'] else 0)

mail = Mail(app)

with app.app_context():
    try:
        msg = Message("Test Subject from PulseGuard", recipients=["jayanthgowda1406@gmail.com"])
        msg.body = "This is a test email."
        mail.send(msg)
        print("SUCCESS: Mail sent!")
    except Exception as e:
        import traceback
        print("FAILED to send mail:")
        traceback.print_exc()
