# parse_utils.py

import re
import logging
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

def extract_stake_list(text: str) -> list[float]:
    """
    Extrai todas ocorrências de stake na legenda, ex.: ["1.50%", "0.50%", ...]
    """
    if not text:
        return []
    matches = PATTERN_STAKE.findall(text)
    stakes = []
    for m in matches:
        num = m.replace(',', '.')
        try:
            val = float(num)
            stakes.append(val)
        except:
            continue
    return stakes

def extract_stake(text: str) -> float | None:
    """
    Retorna apenas o primeiro stake, para casos simples.
    """
    lst = extract_stake_list(text)
    if lst:
        return lst[0]
    return None

def extract_odd_list(text: str) -> list[float]:
    """
    Extrai todas ocorrências de odd na legenda/texto.
    """
    if not text:
        return []
    matches = PATTERN_ODD.findall(text)
    odds = []
    for m in matches:
        num = m.replace(',', '.')
        try:
            val = float(num)
            odds.append(val)
        except:
            continue
    return odds

def extract_odd(text: str) -> float | None:
    """
    Retorna apenas a primeira odd da legenda.
    """
    lst = extract_odd_list(text)
    if lst:
        return lst[0]
    return None

def extract_limit(text: str) -> float | None:
    """
    Extrai valor de limite, ex.: 'Limite da aposta: R$50,00' → 50.0
    """
    if not text:
        return None
    m = PATTERN_LIMIT.search(text)
    if m:
        # remover pontos de milhar e normalizar vírgula decimal
        num = m.group(1).replace('.', '').replace(',', '.')
        try:
            return float(num)
        except:
            return None
    return None

def parse_market(mercado_raw: str) -> tuple[str | None, str | None]:
    """
    Parse simplificado de mercado_raw.
    Adapte de acordo com seus casos específicos.
    Retorna (bet_type, selection).
    Exemplo: 
      - "Over 2.5 gols" → ("over", "2.5")
      - "Under 1.5" → ("under", "1.5")
      - Outras regras que você tenha.
    """
    if not mercado_raw:
        return None, None
    s = mercado_raw.lower()
    # Exemplos simples:
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
    # Ganha / Resultado exato: adapte se quiser
    # Exemplo: “Time A ganha” → ("win", "Time A")
    # ...
    return None, None

def detect_competition(text: str) -> str | None:
    """
    Detecta competição a partir de lista COMPETITIONS.
    """
    if not text:
        return None
    for comp in COMPETITIONS:
        if comp.lower() in text.lower():
            return comp
    return None

def detect_sport(text: str) -> str | None:
    """
    Detecta esporte a partir de palavras-chave em SPORTS_KEYWORDS.
    Retorna a palavra do esporte (title case) ou None.
    """
    if not text:
        return None
    tlower = text.lower()
    for kw in SPORTS_KEYWORDS:
        if kw.lower() in tlower:
            # Retornar com primeira letra maiúscula
            return kw.title()
    return None

def summarize_market(mercado_raw: str) -> str:
    """
    Resumo de mercado: reaproveita mapping_utils ou heurística simples.
    """
    from mapping_utils import summarize_market as sm
    return sm(mercado_raw or "")
