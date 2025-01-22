# Use uma imagem Python específica para garantir mais controle sobre a versão
FROM python:3.9-slim

# Defina o diretório de trabalho
WORKDIR /app

# Copie o arquivo de requisitos para instalar as dependências
COPY requirements.txt .

# Atualize o pip e instale as dependências
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copie o código fonte para dentro do container
COPY server.py .

# Expõe a porta onde a aplicação estará rodando
EXPOSE 5000

# Defina o comando para rodar a aplicação
CMD ["python", "server.py"]
