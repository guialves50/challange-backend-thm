from pydantic import BaseModel, EmailStr
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str
    
class TokenData(BaseModel):
    email: Optional[str] = None
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
class UserRegistration(BaseModel):
    nome_ong: Optional[str] = None
    cnpj: str
    nome_representante: str
    email: EmailStr
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    descricao: Optional[str] = None
    password: str 