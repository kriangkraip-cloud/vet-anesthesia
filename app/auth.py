import re
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from . import models

SECRET_KEY = "vet-anesthesia-secret-key-2024-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


# Pharmacy Staff may read everything, but may only write drug-related data.
# Every mutating request from a pharmacy account must match one of these patterns;
# anything else is rejected here, in the one dependency all routes share.
PHARMACY_WRITE_ALLOW = [
    (("PUT",), re.compile(r"^/api/records/\d+$")),                         # limited to drug fields in update_record
    (("POST", "PUT", "DELETE"), re.compile(r"^/api/records/\d+/drugs(/\d+)?$")),
    (("POST", "PUT", "DELETE"), re.compile(r"^/api/drug-presets(/\d+)?$")),
    (("POST", "PUT", "DELETE"), re.compile(r"^/api/stock/.+$")),
    (("PUT",), re.compile(r"^/api/users/\d+$")),                           # own password only (enforced in users.py)
]

# Fields of an anesthetic record that count as "drug information".
PHARMACY_RECORD_FIELDS = {"current_medications", "postop_pain_management"}


def _pharmacy_may_write(method: str, path: str) -> bool:
    return any(method in methods and rx.match(path) for methods, rx in PHARMACY_WRITE_ALLOW)


async def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, username)
    if user is None or not user.is_active:
        raise credentials_exception
    if (
        user.role == "pharmacy"
        and request.method not in ("GET", "HEAD", "OPTIONS")
        and not _pharmacy_may_write(request.method, request.url.path)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Pharmacy Staff accounts can only edit drug-related information",
        )
    return user


async def get_current_pharmacy_or_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role not in ("admin", "pharmacy"):
        raise HTTPException(status_code=403, detail="Pharmacy or admin access required")
    return current_user


async def get_current_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
