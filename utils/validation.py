import re 
from utils.exceptions import ValidationError

def validate_email(email: str) -> bool:
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        raise ValidationError(detail="Invalid email format")
    return True

def validate_password(password: str) -> bool:
    return len(password) >= 8

def validate_amount(amount: float) -> bool:
    if amount <= 0:
        raise ValidationError(detail="Amount must be greater than zero")
    return True