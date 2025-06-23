# Use uma imagem base de Dev Container com Python
FROM mcr.microsoft.com/devcontainers/python:3.9

# Instala Tesseract OCR e dependências de sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       tesseract-ocr \
       libtesseract-dev \
       libleptonica-dev \
       pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Define diretório de trabalho
WORKDIR /workspace

# Copia o requirements e instala dependências Python
COPY requirements.txt /workspace/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /workspace/requirements.txt

# Copia todo o código do repositório
COPY . /workspace

# Ajuste opcional: se quiser configurar TESSERACT_CMD em config.py, dentro do container tesseract está no PATH.
