import os
from pymongo import MongoClient

# Configurações do MongoDB (valores padrão para desenvolvimento)
MONGODB_URL = "mongodb+srv://firebird748:5YDZGZIkWnXRpU8Q@challengefiap.zspngt1.mongodb.net/?retryWrites=true&w=majority&appName=CHALLENGEFIAP"
DB_NAME = "empresa_api"

# Verificar se existem variáveis de ambiente definidas
if os.environ.get("MONGODB_URL"):
    MONGODB_URL = os.environ.get("MONGODB_URL")
if os.environ.get("DB_NAME"):
    DB_NAME = os.environ.get("DB_NAME")

# Criar uma conexão com o MongoDB
try:
    client = MongoClient(MONGODB_URL)
    # Verifica a conexão
    client.admin.command('ping')
    print("✅ Conectado ao MongoDB com sucesso!")
except Exception as e:
    print(f"❌ Erro ao conectar ao MongoDB: {e}")

db = client[DB_NAME]

# Coleções
users_collection = db.users 