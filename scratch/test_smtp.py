import os
from dotenv import load_dotenv
load_dotenv()

import smtplib
from email.mime.text import MIMEText

username = os.getenv('MAIL_USERNAME')
raw_password = os.getenv('MAIL_PASSWORD')
clean_password = raw_password.replace(" ", "") if raw_password else ""

print(f"Testing with username: {username}")
print(f"Raw password: '{raw_password}', Clean password: '{clean_password}'")

# Test 1: Port 587 STARTTLS with clean password
print("\n--- Test 1: Port 587 STARTTLS with clean password ---")
try:
    server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
    server.set_debuglevel(1)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(username, clean_password)
    print("SUCCESS on Port 587!")
    server.quit()
except Exception as e:
    print(f"FAILED on Port 587: {e}")

# Test 2: Port 465 SSL with clean password
print("\n--- Test 2: Port 465 SSL with clean password ---")
try:
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15)
    server.set_debuglevel(1)
    server.ehlo()
    server.login(username, clean_password)
    print("SUCCESS on Port 465!")
    server.quit()
except Exception as e:
    print(f"FAILED on Port 465: {e}")
