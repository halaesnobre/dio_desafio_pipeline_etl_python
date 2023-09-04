import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from conections import (email_smtp_server, email_smtp_port, email_smtp_user,
                        email_smtp_password, email_sender,
                        BAGY_ORDERS_API_BASE_URL, BAGY_HEADERS_API)
import requests


def send_email(email, subject, body, order_id, tag):
    # configurar as informações do seu e-mail
    emailFrom = email_sender
    emailTo = email
    emailSubject = subject
    emailHTMLBody = body
    msg = MIMEMultipart("alternative")
    msg["Subject"] = emailSubject
    msg["From"] = emailFrom
    msg["To"] = emailTo
    rcpt = [emailTo] + [emailFrom]
    msg.attach(MIMEText(emailHTMLBody, "html"))
    # Send the message via local SMTP server.
    mail = smtplib.SMTP(email_smtp_server, int(email_smtp_port))
    mail.ehlo()
    mail.starttls()
    mail.login(email_smtp_user, email_smtp_password)
    mail.sendmail(emailFrom, rcpt, msg.as_string())
    mail.quit()
    requests.put(f"{BAGY_ORDERS_API_BASE_URL}/{order_id}",
                 json=tag,
                 headers=BAGY_HEADERS_API)
    time.sleep(10)
