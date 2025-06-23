# parse_utils.py

import re
import logging
from typing import Optional, List, Tuple

from config import PATTERN_STAKE, PATTERN_LIMIT, PATTERN_ODD, RUIDO_LINES, COMPETITIONS, SPORTS_KEYWORDS

logger = logging.getLogger(__name__)

def clean_caption(raw: str) -> str:
    """
    Limpeza básica de legenda: remove linhas de ruído e múltiplos espaços.
    """
    if not raw:
        return ""
    s = raw.strip()
    linhas = s.splitlines()
    novas = []
    for l in linhas:
        ignora = False
        for pat in RUIDO_LINES:
            try:
                if re.search(pat, l, flags=re.IGNORECASE):
                    ignora = True
                    break
            except re.error:
                continue
        if not ignora:
            novas.append(l)
    s2 = "\n".join(novas)
    s2 = re.sub(r'\s+', ' ', s2)
    return s2.strip()

def extract_stake_list(text: str) -> List[float]:
    """
    Extrai todas ocorrências de stake na legenda, ex.: ["1.50%", "0.50%", ...]
    Retorna lista de floats.
    """
    if not text:
        return []
    matches = PATTERN_STAKE.findall(text)
    stakes: List[float] = []
    for m in matches:
        num = m.replace(',', '.')
        try:
            val = float(num)
            stakes.append(val)
        except:
            continue
    return stakes

def extract_stake(text: str) -> Optional[float]:
    """
    Retorna apenas o primeiro stake, ou None se não houver.
    """
    lst = extract_stake_list(text)
    if lst:
        return lst[0]
    return None

def extract_odd_list(text: str) -> List[float]:
    """
    Extrai todas ocorrências de odd na legenda/texto.
    """
    if not text:
        return []
    matches = PATTERN_ODD.findall(text)
    odds: List[float] = []
    for m in matches:
        num = m.replace(',', '.')
        try:
            val = float(num)
            odds.append(val)
        except:
            continue
    return odds

def extract_odd(text: str) -> Optional[float]:
    """
    Retorna apenas a primeira odd da legenda, ou None.
    """
    lst = extract_odd_list(text)
    if lst:
        return lst[0]
    return None

def extract_limit(text: str) -> Optional[float]:
    """
    Extrai valor de limite, ex.: 'Limite da aposta: R$50,00' → 50.0, ou None.
    """
    if not text:
        return None
    m = PATTERN_LIMIT.search(text)
    if m:
        num = m.group(1).replace('.', '').replace(',', '.')
        try:
            return float(num)
        except:
            return None
    return None

def parse_market(mercado_raw: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse simplificado de mercado_raw.
    Retorna (bet_type, selection), ex:
      - "Over 2.5 gols" → ("over", "2.5")
      - "Under 1.5" → ("under", "1.5")
      - Handicap: ("handicap", "-1.5") se encontrado
      - "Dupla Chance", "Ambas Marcam", etc.
    """
    if not mercado_raw:
        return None, None
    s = mercado_raw.lower()

    # Over / Mais de
    if "over" in s or "mais de" in s:
        nums = re.findall(r'(\d+[.,]?\d*)', s)
        if nums:
            sel = nums[0].replace(',', '.')
            return "over", sel

    # Under / Menos de
    if "under" in s or "menos de" in s:
        nums = re.findall(r'(\d+[.,]?\d*)', s)
        if nums:
            sel = nums[0].replace(',', '.')
            return "under", sel

    # Handicap com sinal explícito, ex: "-1.5", "+2"
    m2 = re.search(r'([+-]\s*\d+[.,]?\d*)', mercado_raw)
    if m2:
        val = m2.group(1).replace(' ', '').replace(',', '.')
        return "handicap", val

    # Dupla Chance
    if re.search(r'dupla chance', s):
        return "dupla chance", ""

    # Ambos Marcam
    if re.search(r'ambas.*marcam', s):
        return "ambas marcam", ""

    # Total de gols/pontos
    if re.search(r'total(?: de)? (gols|pontos)', s):
        return "total", ""

    # Vitória simples: ex: "Time A ganha"
    m3 = re.search(r'(.+?)\s+ganha', mercado_raw, flags=re.IGNORECASE)
    if m3:
        return "win", m3.group(1).strip()

    return None, None

def detect_competition(text: str) -> Optional[str]:
    """
    Detecta competição a partir de lista COMPETITIONS.
    """
    if not text:
        return None
    for comp in COMPETITIONS:
        if comp.lower() in text.lower():
            return comp
    return None

def detect_sport(text: str) -> Optional[str]:
    """
    Detecta esporte a partir de palavras-chave em SPORTS_KEYWORDS.
    Retorna a palavra em title case ou None.
    """
    if not text:
        return None
    tlower = text.lower()
    for kw in SPORTS_KEYWORDS:
        if kw.lower() in tlower:
            return kw.title()
    return None

def summarize_market(mercado_raw: str) -> str:
    """
    Resumo de mercado: reaproveita heurística de mapping_utils.
    """
    from mapping_utils import summarize_market as sm
    return sm(mercado_raw or "")
