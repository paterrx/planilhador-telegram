# Use a imagem oficial de Dev Container Python
FROM mcr.microsoft.com/devcontainers/python:3.9

# Precisamos rodar apt-get como root
USER root

# Instalar Tesseract OCR e o idioma português
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
         tesseract-ocr \
         tesseract-ocr-por \
         # Dependências adicionais se necessário:
         libtesseract-dev \
         libleptonica-dev \
         pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Volta para usuário vscode
USER vscode

WORKDIR /workspace

# Copia apenas requirements para aproveitar cache de layers
COPY requirements.txt /workspace/requirements.txt

# Instala dependências Python imediatamente (poderia ser no postCreateCommand, mas este RUN garante já em build)
RUN python3 -m pip install --upgrade pip \
    && pip install -r /workspace/requirements.txt

# Copia o restante do código para dentro do container
COPY . /workspace

# (Opcional) Se precisar expor portas, defina aqui, etc.
