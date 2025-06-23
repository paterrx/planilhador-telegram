# mapping_utils.py

import os
import json
from rapidfuzz import process, fuzz
import logging

logger = logging.getLogger(__name__)
MAPPING_FILE = "mapping.json"

def load_mapping():
    if os.path.exists(MAPPING_FILE):
        try:
            with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
            logger.debug(f"mapping.json carregado com {len(mapping)} entradas.")
            return mapping
        except Exception as e:
            logger.warning("Falha ao ler mapping.json; iniciando vazio", exc_info=e)
    return {}

def save_mapping(mapping):
    try:
        with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        logger.debug("mapping.json salvo.")
    except Exception as e:
        logger.warning("Falha ao salvar mapping.json", exc_info=e)

mapping_cache = load_mapping()

def get_canonical(raw_name: str, threshold: int = 85) -> str:
    if not raw_name:
        return raw_name
    mapping = mapping_cache
    if raw_name in mapping:
        return mapping[raw_name]
    canonical_list = list(set(mapping.values()))
    if canonical_list:
        best_match, score, _ = process.extractOne(
            raw_name, canonical_list,
            scorer=fuzz.token_sort_ratio
        )
        if score >= threshold:
            mapping[raw_name] = best_match
            save_mapping(mapping)
            logger.debug(f"Mapeado '{raw_name}' -> '{best_match}' (score {score})")
            return best_match
    mapping[raw_name] = raw_name
    save_mapping(mapping)
    logger.debug(f"Novo raw em mapping: '{raw_name}' -> '{raw_name}'")
    return raw_name
