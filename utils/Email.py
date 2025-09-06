from flask_mail import Mail, Message

mail = Mail()

def send_email(recipient, message):
    sub = "Welcome to CommitHub!!"
    bd = message

    try :
        msg = Message(subject = sub,recipients = [recipient], body = bd)
        mail.send(msg)
        return "email sent"
    except Exception as a:
        print(a)
        return "sending email failed"