"""
Filename:       supportMail.py
Version:        1.0
Authors:        Jason Huang, ECE4574_F25_Team8
Description:    This file deals with the email functionality of the project.
                Users will be able to send emails to the developer email and get
                email notifications if they want.
"""

import smtplib
import os
from dotenv import load_dotenv

# Address and password stored in an environment file not on the repo
load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def send_sup_msg(user_email: str, user_msg: str):
    """
    This function allows users to send an email to the developers for changes.
    The function essentially just sends an email from the developer email 
    with the subject being the user's email and the body being the user's message
    Prints out an error if email was unable to be sent.
    """

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASS)
        
        msg = f"Subject: {user_email}\n\n{user_msg}"
        server.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, msg)
        server.quit()
    except Exception as e:
        print(e)


def main():
    """Demos the support mail functionality"""
    send_sup_msg("Testemail@mail.com", "This is a test message")


if __name__ == "__main__":
    main()