import re
import unicodedata
import logging
from typing import Optional  # Import necessário para as anotações que retornam Optional[str]
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
    - Mapeamentos manuais (adicione conforme frequência)
    """
    s = raw_name.strip()
    # Remove caracteres não ASCII (ex.: emojis) de forma simples
    s = re.sub(r'[^\x00-\x7F]+', '', s)
    # Normaliza espaços
    s = ' '.join(s.split())
    # Mapping manual de abreviações comuns
    mapping = {
        "Man City": "Manchester City",
        "City": "Manchester City",
        "Real Madrid": "Real Madrid",
        # Adicione conforme necessário...
    }
    if s in mapping:
        return mapping[s]
    # Opcional: normalizar acentuação
    s_norm = normalize_text(s)
    # Pode aplicar title case ou outra normalização leve
    return s_norm

def normalize_bookmaker_from_url_or_text(text: str) -> Optional[str]:
    """
    Detecta bookmaker a partir de URL ou texto livre, usando BOOKMAKER_MAP.
    Retorna valor mapeado (ex.: "Bet365") ou None.
    """
    if not text:
        return None

    # Primeiro, extrai host de possíveis URLs
    # Regex simples: captura parte após https?:// até / ou espaço
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
    - Divide por delimitadores comuns (; , . - –)
    - Retorna a primeira parte não vazia, com até ~8 tokens
    """
    if not mercado_raw:
        return ""
    s = mercado_raw.replace('\n', ' ').strip()
    s = ' '.join(s.split())
    # Divide por delimitadores comuns
    parts = re.split(r'[;.,\-–]', s)
    for part in parts:
        part = part.strip()
        if part:
            tokens = part.split()
            # Retorna até os primeiros 8 tokens
            return ' '.join(tokens[:8])
    # fallback: primeiras tokens
    tokens = s.split()
    return ' '.join(tokens[:8])
