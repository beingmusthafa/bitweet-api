
import http.client
import json
import os

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL")
BREVO_SENDER_NAME = os.getenv("BREVO_SENDER_NAME", "Bitweet - Connect and build networks")

def send_brevo_email(to_email: str, subject: str, html_content: str):
    conn = http.client.HTTPSConnection("api.brevo.com")

    payload = {
        "sender": {"name": BREVO_SENDER_NAME, "email": BREVO_SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content,
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY,
    }

    try:
        conn.request("POST", "/v3/smtp/email", json.dumps(payload), headers)
        res = conn.getresponse()
        data = res.read()

        if 200 <= res.status < 300:
            print("data : ", data.decode("utf-8"))
            print(f"Email sent successfully to {to_email}")
            return True
        else:
            print(f"Failed to send email. Status: {res.status}")
            print(data.decode("utf-8"))
            return False
    except Exception as e:
        print(f"An error occurred while sending email: {e}")
        return False
    finally:
        conn.close()
