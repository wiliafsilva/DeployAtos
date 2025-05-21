FROM python:3.10-slim

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    gnupg \
    apt-transport-https \
    unixodbc \
    unixodbc-dev \
    libpq-dev \
    libsqlite3-dev \
    libssl-dev \
    libffi-dev \
    libsasl2-dev \
    libldap2-dev \
    libkrb5-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos da aplicação
COPY . /app

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta (ajuste conforme necessário)
EXPOSE 8080

# Comando para iniciar sua aplicação (ajuste se for diferente)
CMD ["python", "app.py"]
