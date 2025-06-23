# Dockerfile para devcontainer
FROM mcr.microsoft.com/devcontainers/python:3.9

# Instala Tesseract e línguas
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       tesseract-ocr \
       tesseract-ocr-por \
       tesseract-ocr-eng \
       libtesseract-dev \
       libleptonica-dev \
       pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Copia e instala dependências Python
COPY requirements.txt /workspace/requirements.txt
RUN python3 -m pip install --upgrade pip \
    && pip install -r /workspace/requirements.txt

# Copia todo o projeto
COPY . /workspace
