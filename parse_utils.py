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
            if re.search(pat, l, flags=re.IGNORECASE):
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
    Extrai todas ocorrências de stake na legenda, ex.: ["1.50%", "0.50%", ...] ou em "1,25u" ou R$ quando interpretável.
    Retorna percentuais como float (ex.: 1.5).
    """
    if not text:
        return []
    stakes = []
    # 1) Padrão % ou u
    matches = PATTERN_STAKE.findall(text)
    for m in matches:
        num = m.replace(',', '.')
        try:
            val = float(num)
            stakes.append(val)
        except:
            continue
    # 2) Se não encontrou nenhum e há padrão 'R$X,YY', interpretar como percentuais/unidades se não houver contexto de valor real
    if not stakes:
        # mas cuidado: se R$ refere-se ao valor real em dinheiro, para converter em % precisamos BANK_TOTAL e scale,
        # mas aqui apenas capturamos o valor R$ para posterior conversão no telegram_bot, se desejar.
        # Portanto, retornamos a lista com o valor real em R$ marcando como especial (negativo ou sinal)? 
        # Aqui apenas retornamos o valor diretamente e o telegram_bot decide tratar.
        matches_r = re.findall(r'R\$[\s]*([\d\.,]+)', text)
        for m in matches_r:
            num = m.replace('.', '').replace(',', '.')
            try:
                val = float(num)
                stakes.append(val)  # no telegram_bot, pode-se detectar que é valor em reais e converter para %/u conforme unit_value
            except:
                continue
    return stakes

def extract_stake(text: str) -> Optional[float]:
    """
    Retorna apenas o primeiro stake (percentual/unidades) ou valor em R$ se não houver %/u, para casos simples.
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
    odds = []
    matches = PATTERN_ODD.findall(text)
    for m in matches:
        num = m.replace(',', '.')
        try:
            val = float(num)
            odds.append(val)
        except:
            continue
    # Em alguns casos, a odd aparece como número solto próximo a '@' ou 'a', ex: "@2,07" ou "1,87" sem prefixo 'Odd'; 
    # podemos tentar extrair padrões '@2,07'
    if not odds:
        matches2 = re.findall(r'[@]\s*([\d]+[.,][\d]+)', text)
        for m in matches2:
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
    Retorna (bet_type, selection). Exemplos:
      - "Over 2.5 gols" → ("over", "2.5")
      - "Under 1.5" → ("under", "1.5")
      - "Time X ou Empate" → ("double_chance", "Time X/Empate") ou similar
      - "Time A ganha" → ("win", "Time A")
      - Adaptar conforme necessidades específicas.
    """
    if not mercado_raw:
        return None, None
    s = mercado_raw.strip()
    s_lower = s.lower()
    # Double chance: "Time X ou Empate" ou "X ou Empate"
    m = re.search(r'(.+?)\s+ou\s+empate', s, flags=re.IGNORECASE)
    if m:
        team = m.group(1).strip()
        # Retornar seleção em formato: "team/empate"
        return "double_chance", f"{team}/Empate"
    # Over / Mais de
    if "over" in s_lower or "mais de" in s_lower:
        nums = re.findall(r'(\d+[.,]?\d*)', s_lower)
        if nums:
            return "over", nums[0].replace(',', '.')
    # Under / Menos de
    if "under" in s_lower or "menos de" in s_lower:
        nums = re.findall(r'(\d+[.,]?\d*)', s_lower)
        if nums:
            return "under", nums[0].replace(',', '.')
    # Resultado simples: "Time A ganha" ou "A vence" etc.
    m_win = re.search(r'(.+?)\s+(ganha|vence|winner)', s_lower)
    if m_win:
        team = m_win.group(1).strip().title()
        return "win", team
    # Empate exato (raro de usar isolado)
    if "empate" == s_lower.strip():
        return "draw", None
    # Outros padrões podem ser implementados conforme formatos recebidos.
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
            # Retornar com primeira letra maiúscula
            # Ex.: 'tênis' → 'Tênis'
            return kw.title()
    return None

def summarize_market(mercado_raw: str) -> str:
    """
    Resumo de mercado: reaproveita mapping_utils ou heurística simples.
    """
    from mapping_utils import summarize_market as sm
    return sm(mercado_raw or "")
