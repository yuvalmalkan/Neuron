__author__ = "Yuval Malkan"

import smtplib
import ssl
import uuid
from email.message import EmailMessage
import os
import logging
from dotenv import load_dotenv

load_dotenv()

email_sender = os.getenv("EMAIL_SENDER_ADDRESS", "").strip()
email_password = os.getenv("EMAIL_PASSWORD", "").strip()


security_code = str(uuid.uuid4())
half_length = len(security_code) // 2
security_code = security_code[:half_length]


#debug
logging.debug(f"EMAIL_SENDER: {email_sender if email_sender else 'NOT SET'}")
logging.debug(f"EMAIL_PASSWORD: {'*' * len(email_password) if email_password else 'NOT SET'}")


def send_email(email_receiver, email_subject, email_body):

    global email_sender, email_password, email_password

    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['Subject'] = email_subject
    em.set_content(email_body)

    context = ssl.create_default_context()

    try:

        email_password = email_password.strip()

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(email_sender, email_password)
            smtp.sendmail(email_sender, email_receiver, em.as_string())
        logging.info(f"Email sent successfully to {email_receiver}")
    except smtplib.SMTPAuthenticationError as e:
        logging.error(f"Gmail authentication failed: Check your App Password (error: {e})")
        raise
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        raise




"""

email_to      = "jedpjsmvhcbcrblrug@enotj.com"
email_subject = "hello from python"
email_body    = "this is my first try to send an email from a script"

send_email(email_to, email_subject, email_body)

"""