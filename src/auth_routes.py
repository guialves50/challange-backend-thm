from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Dict, Any

from models import User, UserResponse
from auth_models import Token, UserRegistration, UserLogin
from security import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_active_user
)
from database import users_collection
from bson import json_util
import json
from pymongo.errors import DuplicateKeyError

router = APIRouter(tags=["auth"])

# Parsear JSON do MongoDB para Python
def parse_json(data):
    json_data = json.loads(json_util.dumps(data))
    
    # Converter o ObjectId de formato {$oid: '...'} para string simples
    if isinstance(json_data, dict):
        if "_id" in json_data and isinstance(json_data["_id"], dict) and "$oid" in json_data["_id"]:
            json_data["_id"] = json_data["_id"]["$oid"]
        # Converter campos antigos para o novo schema
        _handle_schema_compatibility(json_data)
            
    # Se for uma lista, processar cada item
    elif isinstance(json_data, list):
        for item in json_data:
            if isinstance(item, dict):
                if "_id" in item and isinstance(item["_id"], dict) and "$oid" in item["_id"]:
                    item["_id"] = item["_id"]["$oid"]
                # Converter campos antigos para o novo schema
                _handle_schema_compatibility(item)
                
    return json_data

# Função para garantir compatibilidade entre schemas antigo e novo
def _handle_schema_compatibility(user_dict):
    # Campo 'name' antigo para 'nome_ong' novo
    if "name" in user_dict and "nome_ong" not in user_dict:
        user_dict["nome_ong"] = user_dict.pop("name")
    
    # Garantir que campo obrigatório 'nome_representante' exista
    if "nome_representante" not in user_dict:
        user_dict["nome_representante"] = "Representante"  # Valor padrão
        
    # Garantir que outros campos opcionais estejam presentes com valores nulos
    if "telefone" not in user_dict:
        user_dict["telefone"] = None
        
    if "endereco" not in user_dict:
        user_dict["endereco"] = None
        
    if "descricao" not in user_dict:
        user_dict["descricao"] = None

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Aqui tratamos username como email
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login_json(login_data: UserLogin):
    # Endpoint que aceita login via JSON no formato: {"email": "email@exemplo.com", "password": "senha"}
    user = authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegistration):
    # Verificar se o email já existe
    if users_collection.find_one({"email": user_data.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Usuário com email {user_data.email} já existe"
        )
    
    # Criar um novo usuário
    user_dict = {
        "cnpj": user_data.cnpj,
        "nome_representante": user_data.nome_representante,
        "email": user_data.email,
        "password": get_password_hash(user_data.password),
        "active": True
    }
    
    # Adicionar campos opcionais somente se estiverem presentes
    if user_data.nome_ong:
        user_dict["nome_ong"] = user_data.nome_ong
    if user_data.telefone:
        user_dict["telefone"] = user_data.telefone
    if user_data.endereco:
        user_dict["endereco"] = user_data.endereco
    if user_data.descricao:
        user_dict["descricao"] = user_data.descricao
    
    # Criar o objeto User
    user = User(**user_dict)
    
    try:
        user_dict = user.model_dump_for_db()
        result = users_collection.insert_one(user_dict)
        created_user = users_collection.find_one({"_id": result.inserted_id})
        
        # Remove a senha do resultado
        user_result = parse_json(created_user)
        user_result.pop("password", None)
        
        return user_result
    except DuplicateKeyError:
        # Verificar qual campo está duplicado
        if users_collection.find_one({"cnpj": user_data.cnpj}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CNPJ {user_data.cnpj} já está em uso"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao criar usuário"
        )

@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    # Remove a senha do resultado
    user_result = current_user.copy()
    user_result.pop("password", None)
    # Usar a função parse_json para garantir conversão correta do ObjectId
    return parse_json(user_result) 