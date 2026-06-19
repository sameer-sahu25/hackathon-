from passlib.context import CryptContext
import re
import random
import string
import warnings
from typing import Dict

# Ignore passlib bcrypt deprecated warning
warnings.filterwarnings("ignore", category=DeprecationWarning)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Common passwords list (top 100)
COMMON_PASSWORDS = [
    "password", "123456", "123456789", "12345678", "12345",
    "qwerty", "abc123", "password1", "111111", "123123",
    "admin", "letmein", "welcome", "monkey", "dragon",
    "master", "1234", "login", "princess", "sunshine",
    "qwerty123", "iloveyou", "trustno1", "starwars", "password123",
    "welcome1", "admin123", "superman", "123qwe", "666666"
]


class PasswordHandler:
    @staticmethod
    def hash_password(plain_password: str) -> str:
        return pwd_context.hash(plain_password, rounds=12)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def check_password_strength(password: str, username_or_email: str = None) -> Dict:
        feedback = []
        score = 0

        if len(password) < 8:
            feedback.append("Password must be at least 8 characters long")
        else:
            score += 1

        if len(password) > 128:
            feedback.append("Password must not exceed 128 characters")
        else:
            score += 1

        if not re.search(r'[A-Z]', password):
            feedback.append("Password must contain at least one uppercase letter")
        else:
            score += 1

        if not re.search(r'[a-z]', password):
            feedback.append("Password must contain at least one lowercase letter")
        else:
            score += 1

        if not re.search(r'[0-9]', password):
            feedback.append("Password must contain at least one number")
        else:
            score += 1

        if not re.search(r'[!@#$%^&*]', password):
            feedback.append("Password must contain at least one special character (!@#$%^&*)")
        else:
            score += 1

        if password.lower() in COMMON_PASSWORDS:
            feedback.append("Password is too common, choose something more unique")
            score = 0

        if username_or_email:
            if username_or_email.lower() in password.lower():
                feedback.append("Password must not contain your email or username")
                score = max(0, score - 2)

        return {
            "is_strong": len(feedback) == 0 and score >= 4,
            "score": score,
            "feedback": feedback
        }

    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        all_chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password_chars = [
            random.choice(string.ascii_lowercase),
            random.choice(string.ascii_uppercase),
            random.choice(string.digits),
            random.choice("!@#$%^&*")
        ]
        password_chars += [random.choice(all_chars) for _ in range(length - 4)]
        random.shuffle(password_chars)
        return "".join(password_chars)
