# ocr_utils.py

import re
import os
import logging
from PIL import Image, UnidentifiedImageError
import pytesseract
from config import RUIDO_LINES, logger
from parse_utils import detect_sport

def limpa_linhas_ocr(ocr_text: str):
    """
    Filtra linhas de OCR removendo vazias e linhas de ruído conforme RUIDO_LINES.
    """
    lines = [l.strip() for l in ocr_text.splitlines()]
    filtered = []
    for l in lines:
        if not l:
            continue
        ignora = False
        for p in RUIDO_LINES:
            if re.match(p, l, flags=re.IGNORECASE):
                ignora = True
                break
        if ignora:
            continue
        filtered.append(l)
    return filtered

def extrai_times_de_linhas(lines):
    """
    Tenta extrair pares (home, away) de uma lista de linhas de OCR.
    - Usa detect_sport para ajustar heurísticas (ex.: tênis vs futebol).
    - Para tênis, procura padrões de 'Jogador A vs Jogador B' ou deduz de linhas separadas.
    - Para outros esportes, procura 'Time A x Time B', 'Time A vs Time B', 'Time A - Time B'.
    Retorna tupla (home, away) ou (None, None) se falhar.
    """
    if not lines:
        return None, None

    # Junta texto para detectar esporte
    texto_junto = " ".join(lines)
    sport = detect_sport(texto_junto)  # ex.: 'Tênis', 'Futebol', etc.
    sport_l = sport.lower() if sport else None

    # Se for tênis, usar heurísticas específicas
    if sport_l and ("tênis" in sport_l or "tenis" in sport_l):
        # Primeiro, procurar em cada linha padrão 'A vs B', 'A x B', 'A - B'
        for l in lines:
            m = re.search(
                r'([A-Za-zÀ-ÿ][\wÀ-ÿ\.\s]{1,50}?)\s*(?:vs\.?|x|×|-\s*)\s*([A-Za-zÀ-ÿ][\wÀ-ÿ\.\s]{1,50})',
                l, flags=re.IGNORECASE
            )
            if m:
                left = m.group(1).strip()
                right = m.group(2).strip()
                def parece_nome(s: str) -> bool:
                    parts = s.split()
                    return len(parts) >= 2 and all(re.match(r'^[A-ZÀ-Ÿ]', p) for p in parts)
                if parece_nome(left) and parece_nome(right):
                    logger.debug(f"extrai_times_de_linhas (Tênis linha única): '{left}' x '{right}'")
                    return left, right
        # Se não achou em linha única, tentar usar as duas primeiras linhas
        if len(lines) >= 2:
            l0 = lines[0].strip()
            l1 = lines[1].strip()
            def parece_nome(s: str) -> bool:
                parts = s.split()
                return len(parts) >= 2 and all(re.match(r'^[A-ZÀ-Ÿ]', p) for p in parts)
            if parece_nome(l0) and parece_nome(l1):
                logger.debug(f"extrai_times_de_linhas (Tênis 2 linhas): '{l0}' x '{l1}'")
                return l0, l1
        return None, None

    # Heurística geral para outros esportes (futebol, basquete, etc.)
    for l in lines:
        low = l.lower()
        if re.search(r'\b(mais de|under|over|total|empate|ambas|handicap|defesas|pontos)\b', low):
            continue
        m = re.search(r'(.+?)\s*(?:x|vs\.?|v|×|-\s*)\s*(.+)', l, flags=re.IGNORECASE)
        if m:
            left = m.group(1).strip()
            right = m.group(2).strip()
            left2 = re.sub(r'^\d{1,2}[:h]\d{2}\s*', '', left).strip()
            right2 = re.sub(r'^\d{1,2}[:h]\d{2}\s*', '', right).strip()
            left2 = re.sub(r'^(OOS\s+|fe\)\s*)', '', left2, flags=re.IGNORECASE).strip()
            right2 = re.sub(r'^(OOS\s+|fe\)\s*)', '', right2, flags=re.IGNORECASE).strip()
            if re.search(r'[A-Za-zÀ-ÿ]', left2) and re.search(r'[A-Za-zÀ-ÿ]', right2):
                logger.debug(f"extrai_times_de_linhas (Geral): '{left2}' x '{right2}'")
                return left2, right2
    return None, None

def extrai_todas_opcoes_mercado(lines, start_index=0):
    """
    Tenta extrair de cada linha opções de mercado + odd extraída (se lograr):
    Retorna lista de tuplas (mercado_raw, odd_img) onde odd_img é float ou None.
    """
    resultados = []
    for i in range(start_index, len(lines)):
        l = lines[i].strip()
        odd_val = None
        # Tenta extrair odd padrão '2.35x'
        m_odd = re.search(r'([\d]+[.,][\d]+)\s*x\b', l, flags=re.IGNORECASE)
        if m_odd:
            try:
                odd_val = float(m_odd.group(1).replace(',', '.'))
            except:
                odd_val = None
        # heurística de reconhecimento de mercado:
        low = l.lower()
        achou = False
        if re.search(r'\b(Mais de|Under|Over)\s*[\d]+[.,]?[\d]*', l, flags=re.IGNORECASE):
            achou = True
        elif ' ou ' in low and any(k in low for k in ['empate','draw','chance','vencer']):
            achou = True
        elif re.match(r'.+?[-–—]\s*[\d]+[.,]?[\d]*(\s*(pts|pontos))?', l, flags=re.IGNORECASE):
            achou = True
        elif 'defesas do goleiro' in low and re.search(r'Mais de\s*[\d]+[.,]?[\d]*', l, flags=re.IGNORECASE):
            achou = True
        if achou:
            resultados.append((l, odd_val))
    return resultados

async def perform_ocr_on_media(message, download_folder='downloads'):
    """
    Faz download da mídia e tenta OCR via pytesseract.
    Retorna string de texto ou "" se falhar.
    Tenta em português; se falhar por falta de tessdata, tenta em 'eng'.
    """
    os.makedirs(download_folder, exist_ok=True)
    try:
        path = await message.download_media(file=download_folder)
    except Exception as e:
        logger.debug("download_media levantou exceção:", exc_info=e)
        return ""
    if not path or not os.path.exists(path):
        logger.debug(f"download_media retornou None ou não existe: {path}")
        return ""
    logger.debug(f"Mídia salva em {path}, tentando OCR…")
    try:
        img = Image.open(path)
    except UnidentifiedImageError as e:
        logger.debug("OCR falhou ao abrir/imagem inválida:", exc_info=e)
        return ""
    except Exception as e:
        logger.debug("Erro ao abrir imagem para OCR:", exc_info=e)
        return ""
    # First try Portuguese
    try:
        ocr_text = pytesseract.image_to_string(img, lang='por')
        if ocr_text:
            return ocr_text
    except pytesseract.pytesseract.TesseractError as e:
        logger.debug("OCR TesseractError (pt):", exc_info=e)
    except Exception as e:
        logger.debug("OCR falhou genérico (pt):", exc_info=e)
    # Fallback to English
    try:
        ocr_text = pytesseract.image_to_string(img, lang='eng')
        return ocr_text or ""
    except Exception as e:
        logger.debug("OCR falhou genérico (eng):", exc_info=e)
    return ""
