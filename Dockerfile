FROM python:3.10-slim

# Instala dependências do sistema
RUN apt-get update && \
    apt-get install -y gcc g++ unixodbc unixodbc-dev && \
    apt-get clean

# Copia os arquivos da aplicação
WORKDIR /app
COPY . /app

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Comando para iniciar sua aplicação (ajuste conforme necessário)
CMD ["python", "app.py"]
