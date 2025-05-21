FROM python:3.10-slim

# Instala dependências
RUN apt-get update && \
    apt-get install -y gcc g++ unixodbc unixodbc-dev curl && \
    apt-get clean

# Instala driver ODBC do SQL Server (se necessário)
# RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
#     curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
#     apt-get update && \
#     ACCEPT_EULA=Y apt-get install -y msodbcsql17

WORKDIR /app
COPY . /app
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
