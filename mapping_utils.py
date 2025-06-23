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
    - Remove emojis/caracteres não ASCII
    - Mapeamentos manuais
    """
    s = raw_name.strip()
    s = re.sub(r'[^\x00-\x7F]+', '', s)  # remove não ASCII
    s = ' '.join(s.split())
    mapping = {
        "Man City": "Manchester City",
        "City": "Manchester City",
        "Real Madrid": "Real Madrid",
        # Adicione conforme necessário...
    }
    if s in mapping:
        return mapping[s]
    s_norm = normalize_text(s)
    return s_norm

def normalize_bookmaker_from_url_or_text(text: str) -> Optional[str]:
    """
    Detecta bookmaker a partir de URL ou texto livre, usando BOOKMAKER_MAP.
    """
    if not text:
        return None
    # Extrai host de URLs
    urls = re.findall(r'https?://([^/\s]+)', text)
    for host in urls:
        host_lower = host.lower().replace('www.', '')
        for key, name in BOOKMAKER_MAP.items():
            if key in host_lower:
                logger.debug(f"normalize_bookmaker: encontrou '{key}' em host '{host_lower}' → '{name}'")
                return name
    # Procura palavra-chave no texto
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
    - Divide por delimitadores comuns (; , . - –)
    - Retorna a primeira parte não vazia, até ~8 tokens
    """
    if not mercado_raw:
        return ""
    s = mercado_raw.replace('\n', ' ').strip()
    s = ' '.join(s.split())
    parts = re.split(r'[;.,\-–]', s)
    for part in parts:
        part = part.strip()
        if part:
            tokens = part.split()
            return ' '.join(tokens[:8])
    tokens = s.split()
    return ' '.join(tokens[:8])
