import time

import jwt

from social_network.auth.schemas import TokenResponse
from social_network.settings import settings


def token_response(token):
    return TokenResponse(acess_token=token)


def sign_jwt(user_id):
    payload = {
        "user_id": user_id,
        "expires": time.time() + settings.JWT_EXPIRE_TIME_SECONDS,
    }

    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    return token_response(token)


def decode_jwt(token: str):
    decoded_token = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    return decoded_token if decoded_token["expires"] > time.time() else None
