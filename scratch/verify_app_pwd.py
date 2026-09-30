import smtplib

password = "rgduikncslwmjlyx"
accounts = ["jayanthgowda1406@gmail.com", "shabdhai69@gmail.com"]

for email in accounts:
    print(f"Testing {email}...")
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(email, password)
        print(f"SUCCESS: Valid credentials for {email}!")
        server.quit()
        break
    except Exception as e:
        print(f"FAILED for {email}: {e}")
