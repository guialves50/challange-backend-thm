from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from typing import Optional, Any, Dict, Union
from bson import ObjectId
import json
import re

# Classes auxiliares para trabalhar com ObjectId
class CustomObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type,
        _handler,
    ):
        from pydantic_core import core_schema
        return core_schema.with_info_plain_validator_function(cls.validate)
    
    @classmethod
    def validate(cls, value, info):
        if not isinstance(value, (str, ObjectId)):
            raise ValueError("ID inválido")
            
        if isinstance(value, str):
            try:
                value = ObjectId(value)
            except Exception:
                raise ValueError("ID inválido")
                
        return str(value)

# Modelo para respostas de usuário (sem password)
class UserResponse(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    nome_ong: Optional[str] = None
    cnpj: str
    nome_representante: str
    email: EmailStr
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    descricao: Optional[str] = None
    active: bool = True
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "5f8d0eee5e5c5d6e5e5c5d6e",
                "nome_ong": "ONG Amigos dos Animais",
                "cnpj": "12.345.678/0001-90",
                "nome_representante": "João Silva",
                "email": "contato@amigosanimais.org",
                "telefone": "(11) 98765-4321",
                "endereco": "Rua das Flores, 123 - São Paulo/SP",
                "descricao": "ONG dedicada ao resgate e proteção de animais abandonados",
                "active": True
            }
        }
    )

# Modelo para criar usuário
class UserCreate(BaseModel):
    nome_ong: Optional[str] = None
    cnpj: str
    nome_representante: str
    email: EmailStr
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    descricao: Optional[str] = None
    password: str
    active: bool = True
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome_ong": "ONG Amigos dos Animais",
                "cnpj": "12.345.678/0001-90",
                "nome_representante": "João Silva",
                "email": "contato@amigosanimais.org",
                "telefone": "(11) 98765-4321",
                "endereco": "Rua das Flores, 123 - São Paulo/SP",
                "descricao": "ONG dedicada ao resgate e proteção de animais abandonados",
                "password": "Senha@123",
                "active": True
            }
        }
    )
    
    @field_validator("cnpj")
    def validate_cnpj(cls, v):
        # Remove caracteres não numéricos
        cnpj = ''.join(filter(str.isdigit, v))
        
        # Verifica se o CNPJ tem 14 dígitos
        if len(cnpj) != 14:
            raise ValueError('CNPJ deve conter 14 dígitos')
        
        # Verifica se todos os dígitos são iguais
        if len(set(cnpj)) == 1:
            raise ValueError('CNPJ inválido (todos os dígitos são iguais)')
        
        # Algoritmo de validação de CNPJ
        # 1º dígito verificador
        soma = 0
        peso = 5
        for i in range(12):
            soma += int(cnpj[i]) * peso
            peso = 9 if peso == 2 else peso - 1
        
        digito1 = 11 - (soma % 11)
        digito1 = 0 if digito1 > 9 else digito1
        
        if int(cnpj[12]) != digito1:
            raise ValueError('CNPJ inválido (primeiro dígito verificador incorreto)')
        
        # 2º dígito verificador
        soma = 0
        peso = 6
        for i in range(13):
            soma += int(cnpj[i]) * peso
            peso = 9 if peso == 2 else peso - 1
        
        digito2 = 11 - (soma % 11)
        digito2 = 0 if digito2 > 9 else digito2
        
        if int(cnpj[13]) != digito2:
            raise ValueError('CNPJ inválido (segundo dígito verificador incorreto)')
        
        # Formata o CNPJ
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    
    @field_validator("password")
    def validate_password(cls, v):
        # Verifica se a senha tem pelo menos 8 caracteres
        if len(v) < 8:
            raise ValueError('A senha deve ter pelo menos 8 caracteres')
        
        # Verificar se contém pelo menos uma letra maiúscula
        if not any(c.isupper() for c in v):
            raise ValueError('A senha deve conter pelo menos uma letra maiúscula')
        
        # Verificar se contém pelo menos um número
        if not any(c.isdigit() for c in v):
            raise ValueError('A senha deve conter pelo menos um número')
        
        # Verificar se contém pelo menos um caractere especial
        special_chars = "!@#$%^&*()-_=+[]{}|;:,.<>?/"
        if not any(c in special_chars for c in v):
            raise ValueError('A senha deve conter pelo menos um caractere especial')
        
        return v

# Modelo para atualizar usuário
class UserUpdate(UserCreate):
    password: Optional[str] = None

# Modelo Pydantic para usuários (internamente no banco de dados)
class User(BaseModel):
    id: Optional[CustomObjectId] = Field(default=None, alias="_id")
    nome_ong: Optional[str] = None
    cnpj: str
    nome_representante: str
    email: EmailStr
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    descricao: Optional[str] = None
    password: str
    active: bool = True
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "nome_ong": "ONG Amigos dos Animais",
                "cnpj": "12.345.678/0001-90",
                "nome_representante": "João Silva",
                "email": "contato@amigosanimais.org",
                "telefone": "(11) 98765-4321",
                "endereco": "Rua das Flores, 123 - São Paulo/SP",
                "descricao": "ONG dedicada ao resgate e proteção de animais abandonados",
                "password": "Senha@123",
                "active": True
            }
        }
    )
    
    # Método para converter modelo em dicionário compatível com MongoDB
    def model_dump_for_db(self) -> Dict[str, Any]:
        data = self.model_dump(by_alias=True, exclude={"id"})
        if self.id:
            data["_id"] = ObjectId(self.id)
        return data
    
    # Método para criar User a partir de UserCreate
    @classmethod
    def from_user_create(cls, user_create: UserCreate):
        return cls(**user_create.model_dump())
    
    # Método para criar User a partir de UserUpdate
    @classmethod
    def from_user_update(cls, user_update: UserUpdate, existing_user: Dict[str, Any] = None):
        if existing_user:
            # Copiar os dados existentes
            update_data = {**existing_user}
            # Remover campos que não devem ser incluídos
            if "_id" in update_data:
                update_data["id"] = update_data.pop("_id")
            
            # Compatibilidade com schema antigo
            if "name" in update_data and "nome_ong" not in update_data:
                update_data["nome_ong"] = update_data.pop("name")
            
            # Garantir que campos obrigatórios existam
            if "nome_representante" not in update_data:
                update_data["nome_representante"] = "Representante"
            
            # Atualizar apenas os campos não nulos do UserUpdate
            update_dict = {k: v for k, v in user_update.model_dump(exclude_unset=True).items() 
                          if v is not None}
            update_data.update(update_dict)
            
            # Se não houver nova senha, manter a antiga
            if not user_update.password:
                update_data.pop("password", None)
            
            return cls(**update_data)
        else:
            # Se não tiver dados existentes, apenas usar os dados do update
            return cls(**user_update.model_dump()) 