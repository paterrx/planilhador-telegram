# mapping_utils.py

import re
import unicodedata
import logging
from typing import Optional
from config import BOOKMAKER_MAP

logger = logging.getLogger(__name__)

def normalize_text(s: str) -> str:
    """
    Remove diacríticos e normaliza texto para comparações simples.
    """
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)])

def get_canonical(raw_name: str) -> str:
    """
    Converte raw_name em forma canônica:
    - Strip de espaços e quebras
    - Remove emojis/caracteres não ASCII de forma simples
    - Mapeamentos manuais (adicione conforme frequência)
    - Normaliza acentuação
    - Title-case leve (opcional)
    """
    if not raw_name:
        return raw_name
    s = raw_name.strip()
    # Remove caracteres não ASCII (ex.: emojis) de forma simples
    s = re.sub(r'[^\x00-\x7F]+', '', s)
    # Normaliza espaços
    s = ' '.join(s.split())
    # Mapeamentos manuais comuns
    mapping = {
        "Man City": "Manchester City",
        "City": "Manchester City",
        "Atl Madrid": "Atlético Madrid",
        "Atletico Madrid": "Atlético Madrid",
        "Atlético Madrid": "Atlético Madrid",
        "PSG": "Paris Saint Germain",
        "Paris SG": "Paris Saint Germain",
        # Adicione outros casos frequentes aqui
    }
    if s in mapping:
        return mapping[s]
    # Normaliza acentuação
    s_norm = normalize_text(s)
    # Title-case leve: cuidado com “da”, “de”, etc.; mas já ajuda no geral
    # Podemos fazer: cada palavra capitalize, exceto preposições curtas, mas aqui usamos title()
    s_title = s_norm.title()
    return s_title

def normalize_bookmaker_from_url_or_text(text: str) -> Optional[str]:
    """
    Detecta bookmaker a partir de URL ou texto livre, usando BOOKMAKER_MAP.
    Retorna valor mapeado (ex.: "Bet365") ou None.
    """
    if not text:
        return None
    # Primeiro, extrai host de possíveis URLs
    urls = re.findall(r'https?://([^/\s]+)', text)
    for host in urls:
        host_lower = host.lower().replace('www.', '')
        for key, name in BOOKMAKER_MAP.items():
            if key in host_lower:
                logger.debug(f"normalize_bookmaker: encontrou '{key}' em host '{host_lower}' → '{name}'")
                return name
    # Senão, procura palavra-chave no texto
    text_lower = text.lower()
    for key, name in BOOKMAKER_MAP.items():
        if key in text_lower:
            logger.debug(f"normalize_bookmaker: encontrou '{key}' em texto → '{name}'")
            return name
    return None

def summarize_market(mercado_raw: str) -> str:
    """
    Gera resumo curto a partir de mercado_raw:
    - Junta linhas numa string única
    - Divide por delimitadores comuns (; , . - – | /)
    - Retorna a primeira parte não vazia, com até ~8 tokens
    """
    if not mercado_raw:
        return ""
    s = mercado_raw.replace('\n', ' ').strip()
    s = ' '.join(s.split())
    # Divide por pontuação comum para isolar a parte principal
    parts = re.split(r'[;.,\-–\|/]', s)
    for part in parts:
        part = part.strip()
        if part:
            tokens = part.split()
            return ' '.join(tokens[:8])
    # Fallback: primeiras 8 tokens
    tokens = s.split()
    return ' '.join(tokens[:8])
