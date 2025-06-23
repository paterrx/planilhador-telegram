# dedup_utils.py

import os
import json
import hashlib
import logging

logger = logging.getLogger(__name__)
SEEN_FILE = "seen.json"

def load_seen():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            seen = set(data)
            logger.debug(f"seen.json carregado com {len(seen)} chaves.")
            return seen
        except Exception as e:
            logger.warning("Falha ao ler seen.json, iniciando vazio", exc_info=e)
    return set()

def save_seen(seen_set):
    try:
        with open(SEEN_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(seen_set), f)
        logger.debug("seen.json salvo.")
    except Exception as e:
        logger.warning("Falha ao salvar seen.json", exc_info=e)

def generate_bet_key(home: str, away: str, market_raw: str, odd_val) -> str:
    keystr = f"{home}|{away}|{market_raw or ''}|{odd_val or ''}"
    return hashlib.md5(keystr.encode('utf-8')).hexdigest()
