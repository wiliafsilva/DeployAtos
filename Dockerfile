FROM python:3.10-slim

# Instala dependências do sistema necessárias
RUN apt-get update && \
    apt-get install -y gcc g++ unixodbc unixodbc-dev && \
    apt-get clean

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . /app

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta que o Streamlit vai usar
EXPOSE 8080

# Comando para rodar o Streamlit na porta 8080, acessível de fora do container
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
