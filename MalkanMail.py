__author__ = "Yuval Malkan"

import smtplib
import ssl
import uuid
from email.message import EmailMessage
import os



email_sender = os.getenv("EMAIL_SENDER_ADDRESS")
email_password = os.getenv("EMAIL_PASSWORD")

security_code = str(uuid.uuid4())
half_length = len(security_code) // 2
security_code = security_code[:half_length]

def send_email(email_receiver, email_subject, email_body):
    em = EmailMessage()
    em['From']    = email_sender
    em['To']      = email_receiver
    em['Subject'] = email_subject
    em.set_content(email_body)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, em.as_string())





"""

email_to      = "jedpjsmvhcbcrblrug@enotj.com"
email_subject = "hello from python"
email_body    = "this is my first try to send an email from a script"

send_email(email_to, email_subject, email_body)

"""