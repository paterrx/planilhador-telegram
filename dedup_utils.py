# dedup_utils.py

import json
import os
import hashlib
import logging

logger = logging.getLogger(__name__)
SEEN_FILE = "seen.json"

def load_seen():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    seen = set(data)
                else:
                    seen = set(data)
            logger.debug(f"seen.json carregado com {len(seen)} chaves.")
            return seen
        except Exception as e:
            logger.error("Erro ao carregar seen.json", exc_info=e)
            return set()
    else:
        return set()

def save_seen(seen_set):
    try:
        with open(SEEN_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(seen_set), f, ensure_ascii=False, indent=2)
        logger.debug("seen.json salvo.")
    except Exception as e:
        logger.error("Erro ao salvar seen.json", exc_info=e)

def generate_bet_key(home: str, away: str, mercado: str, odd) -> str:
    """
    Gera chave única baseada em campos da aposta, para deduplicação.
    odd pode ser float ou None; se None, converte para string vazia.
    """
    odd_str = str(odd) if odd is not None else ""
    s = f"{home}|{away}|{mercado}|{odd_str}"
    return hashlib.sha256(s.encode('utf-8')).hexdigest()
