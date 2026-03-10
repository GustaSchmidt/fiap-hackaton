# Estágio 1: Build e Instalação de Dependências
FROM python:3.11-slim as builder

WORKDIR /app

# Evita que o Python gere arquivos .pyc e permite logs em tempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instala dependências do sistema necessárias para processamento de imagem (se usar OpenCV, por exemplo)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instala as dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Estágio 2: Imagem Final (Runtime)
FROM python:3.11-slim

WORKDIR /app

# Copia apenas as dependências instaladas do estágio anterior
COPY --from=builder /install /usr/local

COPY . .

# Expõe a porta que o Flask/FastAPI usará (ex: 5000)
EXPOSE 5000

# Comando para rodar a aplicação usando Gunicorn (padrão de produção)
# Se estiver usando Flask:
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]