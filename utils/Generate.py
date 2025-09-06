import random
import string

def generate_default_password(length = 10):
    if length < 8:
        raise ValueError("Password length should be at least 8 characters")
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits

    password = [
        random.choice(lowercase),
        random.choice(uppercase),
        random.choice(digits),
    ]

      
    all_chars = lowercase + uppercase + digits
    password += random.choices(all_chars, k=length - len(password))

    random.shuffle(password)

    return "".join(password)