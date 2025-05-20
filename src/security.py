from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from models import User
from database import users_collection
from bson import json_util
import json
import os

# Configurações de segurança
SECRET_KEY = os.environ.get("SECRET_KEY", "seuSegredoSuperSecretoAqui123!@#")  # Em produção, deve ser uma variável de ambiente
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Contexto para hash de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Funções para gerenciar senhas
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# Funções de autenticação e JWT
def get_user_by_email(email: str):
    user = users_collection.find_one({"email": email})
    if user:
        return json.loads(json_util.dumps(user))
    return None

def authenticate_user(email: str, password: str):
    user_data = get_user_by_email(email)
    if not user_data:
        return False
    if not verify_password(password, user_data["password"]):
        return False
    return user_data

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_email(email)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)):
    if not current_user.get("active", False):
        raise HTTPException(status_code=400, detail="Usuário inativo")
    return current_user 