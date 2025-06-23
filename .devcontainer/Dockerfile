# Dockerfile
FROM mcr.microsoft.com/devcontainers/python:3.9

# Instala Tesseract e idiomas (pt e eng)
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

COPY requirements.txt /workspace/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /workspace/requirements.txt

COPY . /workspace
