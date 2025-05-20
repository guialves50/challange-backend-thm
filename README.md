# API de Empresas com FastAPI, MongoDB e Autenticação JWT

Este projeto implementa uma API RESTful para gerenciamento de empresas usando CNPJ, com FastAPI, Uvicorn, MongoDB e autenticação JWT.

## Requisitos

- Python 3.7+
- pip (gerenciador de pacotes Python)
- MongoDB (local ou remoto)

## Instalação

1. Clone este repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```
3. Certifique-se de que o MongoDB está em execução (por padrão em mongodb://localhost:27017)

## Executando a API

Execute o seguinte comando no diretório do projeto:

```bash
cd src
python server.py
```

A API estará disponível em http://localhost:8000

## Configuração do MongoDB

Por padrão, a API se conecta ao MongoDB na URL `mongodb://localhost:27017`. Para personalizar a conexão, defina as seguintes variáveis de ambiente:

- `MONGODB_URL`: URL de conexão do MongoDB (ex: mongodb://usuario:senha@servidor:porta)
- `DB_NAME`: Nome do banco de dados (padrão: empresa_api)
- `SECRET_KEY`: Chave secreta para geração de tokens JWT

## Autenticação

A API utiliza autenticação JWT (JSON Web Token). Para acessar endpoints protegidos, é necessário:

1. Registrar um usuário com o endpoint `/register`
2. Obter um token de acesso com o endpoint `/token`
3. Incluir o token nos cabeçalhos HTTP com o formato `Authorization: Bearer <token>`

O token de acesso tem validade de 30 minutos. Após esse período, é necessário solicitar um novo token.

## Documentação

A documentação automática está disponível em:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

## Estrutura do Projeto

```
src/
  ├── main.py         # Configuração principal da API
  ├── models.py       # Definição dos modelos de dados
  ├── auth_models.py  # Modelos para autenticação
  ├── routes.py       # Rotas e handlers para usuários
  ├── auth_routes.py  # Rotas e handlers para autenticação
  ├── security.py     # Configuração de segurança e JWT
  ├── database.py     # Configuração do MongoDB
  └── server.py       # Script para iniciar o servidor
requirements.txt      # Dependências do projeto
```

## Endpoints de Autenticação

- `POST /register` - Registrar um novo usuário
  - Corpo: `{ "cnpj": "XX.XXX.XXX/XXXX-XX", "email": "email@exemplo.com", "password": "senha" }`
- `POST /token` - Obter token de acesso (LoginForm - username/password)
  - Retorno: `{ "access_token": "token-jwt", "token_type": "bearer" }`
- `GET /users/me` - Obter informações do usuário autenticado

## Endpoints de Usuários (Protegidos)

- `GET /users` - Listar todos os usuários (com suporte a paginação)
  - Parâmetros: `skip` (padrão: 0), `limit` (padrão: 10)
- `GET /users/search` - Pesquisar usuários por CNPJ, email e status
  - Parâmetros: `cnpj` (opcional), `email` (opcional), `active` (opcional)
- `GET /users/{cnpj}` - Obter um usuário específico pelo CNPJ
- `POST /users` - Criar um novo usuário
- `PUT /users/{cnpj}` - Atualizar um usuário
- `DELETE /users/{cnpj}` - Deletar um usuário
- `PATCH /users/{cnpj}/activate` - Ativar um usuário
- `PATCH /users/{cnpj}/deactivate` - Desativar um usuário

## Modelo de Usuário

```json
{
  "_id": "5f8d0eee5e5c5d6e5e5c5d6e",
  "cnpj": "12.345.678/0001-90",
  "email": "empresa@exemplo.com",
  "password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePa.QXtZsw.w.k1fq...", // Hash bcrypt, nunca retornado nas respostas
  "active": true
}
```

## Validações Implementadas

- Validação completa de CNPJ (formato, dígitos verificadores)
- Validação de email (formato válido)
- Validação de senha (comprimento mínimo, letras maiúsculas, números e caracteres especiais)
- Verificação de duplicidade de CNPJ e email
- Hash seguro de senha com bcrypt

## Recursos Implementados

- Autenticação JWT
- Proteção de endpoints
- Persistência de dados com MongoDB
- Validação de dados com Pydantic
- Organização modular do código
- Documentação automática com Swagger UI e ReDoc
- Mensagens de erro padronizadas
- Paginação de resultados
- Filtragem por parâmetros de consulta
- Validação de rotas
- Códigos de status HTTP apropriados
- Endpoints para ativação/desativação de usuários 