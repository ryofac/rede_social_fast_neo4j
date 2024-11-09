from pydantic import BaseModel


class TokenResponse(BaseModel):
    acess_token: str


class UserAuthSchema(BaseModel):
    username: str
    password: str
