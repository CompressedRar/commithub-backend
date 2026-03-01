from flask_mail import Mail, Message
from flask import render_template
mail = Mail()

def send_email(recipient, message):
    sub = "Welcome to CommitHub – Let’s Get Started"
    bd = message

    try :
        msg = Message(subject = sub,recipients = [recipient], body = bd)
        mail.send(msg)
        print("email_sent")
        return "email sent"
    except Exception as a:
        print(a)
        return "sending email failed"
    
def send_reset_email(recipient, message):
    sub = "CommitHub Password Reset Request"
    bd = message

    try :
        msg = Message(subject = sub,recipients = [recipient], body = bd)
        mail.send(msg)
        return "email sent"
    except Exception as a:
        print(a)
        return "sending email failed"
    
def send_templated_reset_email(recipient, message):
    sub = "CommitHub Password Reset Request"
    bd = message

    html_body = render_template("reset_pass.html", YEAR = 2026)

    try :
        msg = Message(subject = sub,recipients = [recipient], html=html_body)
        mail.send(msg)
        return "email sent"
    except Exception as a:
        print(a)
        return a
    

def send_email_account_creation(recipient, message, password):
    sub = "Welcome to CommitHub – Let’s Get Started"
    bd = message

    html_body = render_template("email.html",  LOGIN_URL = "commithub.online", YEAR = 2026, password = password)

    try :
        msg = Message(subject = sub,recipients = [recipient], html=html_body)
        mail.send(msg)
        return "email sent"
    except Exception as a:
        print(a)
        return a
    
