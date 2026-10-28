import passlib.hash
from core.config import settings
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone

def hash_password(password: str) -> str:
    return passlib.hash.bcrypt.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return passlib.hash.bcrypt.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None