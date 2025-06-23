# parse_utils.py

import re
import urllib.parse
import logging
from config import PATTERN_STAKE, PATTERN_ODD, PATTERN_LIMIT, BOOKMAKER_MAP, COMPETITIONS

logger = logging.getLogger(__name__)

def clean_caption(text: str) -> str:
    lines = []
    for l in text.splitlines():
        s = l.strip()
        if not s:
            continue
        s = re.sub(r'^[^\wÀ-ÖØ-öø-ÿ]+', '', s)
        lines.append(s)
    return " ".join(lines)

def extract_stake(text: str):
    pcts = re.findall(PATTERN_STAKE, text)
    if not pcts:
        return None
    vals = []
    for x in pcts:
        try:
            vals.append(float(x.replace(',', '.')))
        except:
            pass
    if not vals:
        return None
    stake_pct = vals[0]
    logger.debug(f"extract_stake: encontrados {vals}, escolhido {stake_pct}")
    return stake_pct

def extract_odd(text: str):
    m = PATTERN_ODD.search(text)
    if m:
        try:
            odd = float(m.group(1).replace(',', '.'))
            logger.debug(f"extract_odd: odd encontrada via regex={odd}")
            return odd
        except:
            pass
    m2 = re.search(r'([\d]+[.,][\d]+)\s*(?=Limite)', text)
    if m2:
        try:
            odd = float(m2.group(1).replace(',', '.'))
            logger.debug(f"extract_odd: odd fallback antes de Limite={odd}")
            return odd
        except:
            pass
    return None

def extract_limit(text: str):
    m = PATTERN_LIMIT.search(text)
    if m:
        try:
            lim = float(m.group(1).replace(',', '.'))
            logger.debug(f"extract_limit: limite extraído={lim}")
            return lim
        except:
            pass
    return None

def normalize_bookmaker_from_url_or_text(text: str):
    urls = re.findall(r'https?://[^\s]+', text)
    if urls:
        try:
            parsed = urllib.parse.urlparse(urls[0])
            host = (parsed.hostname or "").lower().removeprefix("www.")
            for key, friendly in BOOKMAKER_MAP.items():
                if key in host:
                    logger.debug(f"normalize_bookmaker: extraído host {host}, mapeado a {friendly}")
                    return friendly
            logger.debug(f"normalize_bookmaker: host {host} não está em BOOKMAKER_MAP, retorna host")
            return host
        except Exception as e:
            logger.debug("normalize_bookmaker: falha ao parsear URL", exc_info=e)
    low = text.lower()
    for key, friendly in BOOKMAKER_MAP.items():
        if key in low:
            logger.debug(f"normalize_bookmaker: palavra-chave '{key}' detectada, retorna {friendly}")
            return friendly
    logger.debug("normalize_bookmaker: nenhuma URL ou palavra-chave detectada")
    return ""

def parse_market(mercado_raw: str):
    text = mercado_raw or ""
    text_low = text.lower()
    m_ou = re.search(r'\b(over|mais de|under|menos de)\s*([\d]+[.,]\d+)', text_low)
    if m_ou:
        palavra = m_ou.group(1)
        num = m_ou.group(2).replace(',', '.')
        if palavra.startswith('over') or palavra.startswith('mais'):
            sel = f"Over {num}"
        else:
            sel = f"Under {num}"
        return "OverUnder", sel

    if "dupla chance" in text_low or (" ou " in text_low and any(k in text_low for k in ['empate','draw','chance','vencer'])):
        return "DuplaChance", text.strip()

    if "ambas" in text_low and "marcam" in text_low:
        m = re.search(r'ambas.*marcam[:]*\s*(sim|não|nao)', text_low)
        if m:
            sel = "Ambas marcam: " + m.group(1).capitalize()
        else:
            sel = text.strip()
        return "AmbasMarcam", sel

    if "handicap" in text_low or re.search(r'[-–—]\s*[\d]+[.,]?[\d]*(\s*(pts|pontos))?', text_low):
        return "Handicap", text.strip()

    if "total" in text_low and ("pontos" in text_low or "gols" in text_low):
        return "Total", text.strip()

    if "marcar" in text_low and "vencer" in text_low:
        return "PlayerGoalWin", text.strip()

    return None, mercado_raw or ""

def detect_competition(text: str):
    for comp in COMPETITIONS:
        if comp.lower() in text.lower():
            return comp
    return ""

def summarize_market(raw: str) -> str:
    if not raw:
        return ""
    text = raw.strip()
    parts = re.split(r'[;,/]| e | vs | x ', text, flags=re.IGNORECASE)
    summaries = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        words = p.split()
        snippet = " ".join(words[:4])
        summaries.append(snippet)
    resumo = ", ".join(summaries[:3])
    return resumo
