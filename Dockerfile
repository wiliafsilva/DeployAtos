# Etapa de build
FROM python:3.10-slim AS build

# Diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos de requisitos
COPY requirements.txt .

# Instala as dependências
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
COPY . .

# Exponha a porta que sua aplicação utiliza
EXPOSE 8080

# Comando para iniciar a aplicação
CMD ["python", "main.py"]
