from datetime import datetime, timedelta      
from jose import JWTError, jwt                  
from passlib.context import CryptContext        
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from models import User
import os
from typing import List

SECRET_KEY = os.getenv("SECRET_KEY","fallback-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(password:str) -> str:
    return pwd_context.hash(password)

def verify_password(plain:str, hashed:str) -> bool:
    return pwd_context.verify(plain,hashed)

def create_access_token(data:dict) -> str:
    dict_copy = data.copy()
    expiry = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    dict_copy["exp"] = expiry
    result = jwt.encode(dict_copy, SECRET_KEY, algorithm=ALGORITHM)
    return result

def get_current_user(token:str = Depends(oauth2_scheme), db : Session = Depends(get_db)) -> User:
    credential_Exception = HTTPException(
    status_code=401,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"}
)
    try :
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    except JWTError:
        raise credential_Exception
    email = payload.get("sub")

    if not email:
        raise credential_Exception
        
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise credential_Exception
    return user



def require_role(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access forbidden. Required role: {allowed_roles}"
            )
        return current_user
    return role_checker

