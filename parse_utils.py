# parse_utils.py

import re
import logging
from typing import Optional, Tuple, List
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
            if re.search(pat, l):
                ignora = True
                break
        if not ignora:
            novas.append(l)
    s2 = "\n".join(novas)
    # junta múltiplos espaços
    s2 = re.sub(r'\s+', ' ', s2)
    return s2.strip()

def extract_stake_list(text: str) -> List[float]:
    """
    Extrai todas ocorrências de stake na legenda, ex.: "1.50%", "0.50u", etc.
    Retorna lista de floats em porcentagem/unidades.
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
    Retorna apenas o primeiro stake, para casos simples.
    """
    lst = extract_stake_list(text)
    if lst:
        return lst[0]
    return None

def extract_odd_list(text: str) -> List[float]:
    """
    Extrai todas ocorrências de odd na legenda/texto. Usa PATTERN_ODD, que captura "Odd 2.5", "🏷2.5", etc.
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
    Retorna apenas a primeira odd da legenda.
    """
    lst = extract_odd_list(text)
    if lst:
        return lst[0]
    return None

def extract_limit(text: str) -> Optional[float]:
    """
    Extrai valor de limite, ex.: 'Limite da aposta: R$50,00' → 50.0
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
    Retorna (bet_type, selection).
    Exemplos:
      - "Over 2.5 gols" → ("over", "2.5")
      - "Under 1.5" → ("under", "1.5")
      - "Time A ganha" ou "Ganha Time A" → ("win", "Time A")
      - Outros tipos, adaptáveis
    """
    if not mercado_raw:
        return None, None
    s = mercado_raw.lower()
    # Over / Mais de
    if "over" in s or "mais de" in s:
        nums = re.findall(r'(\d+[.,]?\d*)', s)
        if nums:
            return "over", nums[0].replace(',', '.')
    # Under / Menos de
    if "under" in s or "menos de" in s:
        nums = re.findall(r'(\d+[.,]?\d*)', s)
        if nums:
            return "under", nums[0].replace(',', '.')
    # Win: "Time A ganha" ou "ganha Time A"
    m1 = re.search(r'(.+?)\s+(ganha|vence)', s, flags=re.IGNORECASE)
    if m1:
        sel = m1.group(1).strip()
        return "win", sel
    m2 = re.search(r'(ganha|vence)\s+(.+)', s, flags=re.IGNORECASE)
    if m2:
        sel = m2.group(2).strip()
        return "win", sel
    # Empate ou outras regras podem ser implementadas conforme necessidade
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
    Retorna a palavra do esporte (title case) ou None.
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
    Resumo de mercado: reaproveita mapping_utils ou heurística simples.
    """
    from mapping_utils import summarize_market as sm
    return sm(mercado_raw or "")
