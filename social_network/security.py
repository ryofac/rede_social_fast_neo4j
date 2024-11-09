from pwdlib import PasswordHash

pwd_context = PasswordHash.recommended()


def get_password_hash(password: str):
    return pwd_context.hash(password)


def verify_password(unhashed_password: str, hashed_password: str):
    return pwd_context.verify(unhashed_password, hashed_password)
