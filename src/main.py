from fastapi import FastAPI
from routes import router as user_router
from auth_routes import router as auth_router

app = FastAPI(
    title="API de Empresas",
    description="Uma API para gerenciamento de usuários empresariais com CNPJ",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {"message": "Bem-vindo à API de Empresas"}

# Incluir as rotas de autenticação
app.include_router(auth_router)

# Incluir as rotas de usuário
app.include_router(user_router) 