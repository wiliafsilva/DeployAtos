# Usa imagem Python
FROM python:3.11-slim

# Define diretório da aplicação
WORKDIR /app

# Copia arquivos
COPY . .

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta padrão
EXPOSE 8000

# Comando de inicialização (ajuste para seu app, ex: flask ou uvicorn)
CMD ["python", "main.py"]
