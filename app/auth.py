import uuid
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from .dependencies import get_db
from . import crud, models

import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = "30"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_data: timedelta = None):
    to_encode = data.copy()
    if expires_data:
        expire = datetime.utcnow() + expires_data
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    jti = str(uuid.uuid4())
    to_encode.update({"exp": expire, "jti": jti, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_data: timedelta = None):
    to_encode = data.copy()
    if expires_data:
        expire = datetime.utcnow() + expires_data
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    jti = str(uuid.uuid4())
    to_encode.update({"exp": expire, "jti": jti, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # if crud.is_revoked(payload.get("jti", True)):
            # raise credentials_exception
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username

def get_jti(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        if jti is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return jti


def verify_refresh_token(token: str, db: Session):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh-token",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        if jti:
            if db.query(models.RevokedToken).filter(models.RevokedToken.jti == jti).first():
                raise credentials_exception
        else:
            raise credentials_exception
        token_type = payload.get("type")
        username = payload.get("sub")
        if token_type != "refresh" or not username:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username
