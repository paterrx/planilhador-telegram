# Use imagem base Dev Container Python 3.9
FROM mcr.microsoft.com/devcontainers/python:3.9

# Instala Tesseract OCR e dependências de SO
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

# Copia e instala dependências Python
COPY requirements.txt /workspace/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /workspace/requirements.txt

# Copia o código do repositório
COPY . /workspace

# No container, 'tesseract' estará no PATH, e python-dotenv lerá .env se existir.
