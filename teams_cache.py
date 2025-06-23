# teams_cache.py

import json
import os
import logging
from datetime import date

logger = logging.getLogger(__name__)
CACHE_FILE = "teams_cache.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Falha ao ler teams_cache.json", exc_info=e)
    return {}

def save_cache(data):
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug("teams_cache.json salvo.")
    except Exception as e:
        logger.warning("Falha ao salvar teams_cache.json", exc_info=e)

def get_games_for_today():
    """
    Retorna lista de tuplas (home, away) para jogos do dia. 
    Implemente chamada a API esportiva ou mantenha manualmente.
    """
    data = load_cache()
    today = date.today().isoformat()
    if data.get("date") == today:
        return data.get("games", [])
    # Aqui você poderia chamar API e popular:
    # Exemplo:
    # response = requests.get("URL_DA_API", params={...})
    # jogos = parse_response(response)
    # new_data = {"date": today, "games": jogos}
    # save_cache(new_data)
    # return jogos
    return []
