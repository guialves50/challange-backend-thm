FROM python:3.11-slim

WORKDIR /app

# Copiar requirements primeiro para aproveitar o cache de camadas do Docker
COPY requirements.txt .

# Instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar arquivos da aplicação
COPY ./src ./src

# Definir variáveis de ambiente
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expor a porta que o servidor utiliza
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"] 