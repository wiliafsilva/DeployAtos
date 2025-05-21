# Usa imagem Python slim
FROM python:3.11-slim

# Instala pacotes de sistema e configura localização
RUN apt-get update && apt-get install -y locales && \
    locale-gen pt_BR.UTF-8 && \
    update-locale LANG=pt_BR.UTF-8

ENV LANG=pt_BR.UTF-8
ENV LANGUAGE=pt_BR:pt
ENV LC_ALL=pt_BR.UTF-8

# Define diretório da aplicação
WORKDIR /app

# Copia arquivos da aplicação
COPY . .

# Instala dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta padrão (ajuste conforme necessário)
EXPOSE 8000

# Comando de inicialização
CMD ["python", "main.py"]
