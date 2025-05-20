from fastapi import APIRouter, Query, Path, HTTPException, status, Depends
from typing import List, Optional, Any, Dict
from models import User, UserResponse, UserCreate, UserUpdate
from database import users_collection
from bson import json_util, ObjectId
import json
from pymongo.errors import DuplicateKeyError
from security import get_current_active_user

router = APIRouter(prefix="/users", tags=["users"])

# Criar índices para garantir unicidade
users_collection.create_index("cnpj", unique=True)
users_collection.create_index("email", unique=True)

# Função auxiliar para converter documentos do MongoDB para objetos Python
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

@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0, 
    limit: int = 10,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    users = list(users_collection.find().skip(skip).limit(limit))
    # Remover senhas da resposta
    for user in users:
        user.pop("password", None)
    return parse_json(users)

@router.get("/search", response_model=List[UserResponse])
async def search_users(
    email: Optional[str] = Query(None),
    cnpj: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    # Construir o filtro de consulta com base nos parâmetros fornecidos
    query = {}
    
    if email:
        query["email"] = {"$regex": email, "$options": "i"}
    
    if cnpj:
        query["cnpj"] = {"$regex": cnpj}
    
    if active is not None:
        query["active"] = active
    
    # Executar a consulta
    users = list(users_collection.find(query))
    # Remover senhas da resposta
    for user in users:
        user.pop("password", None)
    return parse_json(users)

@router.get("/{user_cnpj}", response_model=UserResponse)
async def get_user(
    user_cnpj: str = Path(..., title="CNPJ do usuário"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    user = users_collection.find_one({"cnpj": user_cnpj})
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Remover senha da resposta
    user.pop("password", None)
    return parse_json(user)

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    try:
        # Converter para o modelo User
        user = User.from_user_create(user_data)
        
        # Inserir o usuário no MongoDB usando o método model_dump_for_db
        user_dict = user.model_dump_for_db()
        result = users_collection.insert_one(user_dict)
        
        # Recuperar o usuário recém-criado
        created_user = users_collection.find_one({"_id": result.inserted_id})
        # Remover senha da resposta
        created_user.pop("password", None)
        return parse_json(created_user)
    except DuplicateKeyError:
        # Verificar qual campo está duplicado
        existing_cnpj = users_collection.find_one({"cnpj": user_data.cnpj})
        if existing_cnpj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Usuário com CNPJ {user_data.cnpj} já existe"
            )
        
        # Se não for o CNPJ, deve ser o email
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Usuário com email {user_data.email} já existe"
        )

@router.put("/{user_cnpj}", response_model=UserResponse)
async def update_user(
    user_cnpj: str = Path(..., title="CNPJ do usuário"), 
    user_data: UserUpdate = None,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    if user_data.cnpj != user_cnpj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CNPJ do path não corresponde ao CNPJ do usuário"
        )
    
    # Verificar se o usuário existe
    existing_user = users_collection.find_one({"cnpj": user_cnpj})
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Verificar se o email já está em uso por outro usuário
    email_conflict = users_collection.find_one({
        "email": user_data.email,
        "cnpj": {"$ne": user_cnpj}
    })
    
    if email_conflict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email {user_data.email} já está em uso por outro usuário"
        )
    
    # Converter para o modelo User
    user = User.from_user_update(user_data, existing_user)
    
    # Atualizar o usuário
    user_dict = user.model_dump_for_db()
    # Manter o _id original
    if "_id" in existing_user:
        user_dict["_id"] = existing_user["_id"]
        
    users_collection.replace_one({"cnpj": user_cnpj}, user_dict)
    
    # Retornar o usuário atualizado
    updated_user = users_collection.find_one({"cnpj": user_cnpj})
    # Remover senha da resposta
    updated_user.pop("password", None)
    return parse_json(updated_user)

@router.delete("/{user_cnpj}", response_model=UserResponse)
async def delete_user(
    user_cnpj: str = Path(..., title="CNPJ do usuário"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    # Encontrar o usuário antes de excluí-lo
    user = users_collection.find_one({"cnpj": user_cnpj})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Excluir o usuário
    users_collection.delete_one({"cnpj": user_cnpj})
    
    # Remover senha da resposta
    user.pop("password", None)
    # Retornar o usuário excluído
    return parse_json(user)

@router.patch("/{user_cnpj}/activate", response_model=UserResponse)
async def activate_user(
    user_cnpj: str = Path(..., title="CNPJ do usuário"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    # Verificar se o usuário existe
    user = users_collection.find_one({"cnpj": user_cnpj})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Ativar o usuário
    users_collection.update_one(
        {"cnpj": user_cnpj},
        {"$set": {"active": True}}
    )
    
    # Retornar o usuário atualizado
    updated_user = users_collection.find_one({"cnpj": user_cnpj})
    # Remover senha da resposta
    updated_user.pop("password", None)
    return parse_json(updated_user)

@router.patch("/{user_cnpj}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_cnpj: str = Path(..., title="CNPJ do usuário"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    # Verificar se o usuário existe
    user = users_collection.find_one({"cnpj": user_cnpj})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Desativar o usuário
    users_collection.update_one(
        {"cnpj": user_cnpj},
        {"$set": {"active": False}}
    )
    
    # Retornar o usuário atualizado
    updated_user = users_collection.find_one({"cnpj": user_cnpj})
    # Remover senha da resposta
    updated_user.pop("password", None)
    return parse_json(updated_user) 