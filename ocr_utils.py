# ocr_utils.py

import re
import os
import logging
from PIL import Image, UnidentifiedImageError
import pytesseract
from config import RUIDO_LINES, logger

def limpa_linhas_ocr(ocr_text: str):
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
    for l in lines:
        low = l.lower()
        if re.search(r'\b(mais de|under|over|total|empate|ambas|handicap|defesas|pontos)\b', low):
            continue
        m = re.search(r'(.+?)\s*(?:vs\.?|x|×|@|[-–—])\s*(.+)', l, flags=re.IGNORECASE)
        if m:
            left = m.group(1).strip()
            right = m.group(2).strip()
            left2 = re.sub(r'^\d{1,2}[:h]\d{2}\s*', '', left).strip()
            right2 = re.sub(r'^\d{1,2}[:h]\d{2}\s*', '', right).strip()
            left2 = re.sub(r'^(OOS\s+|fe\)\s*)', '', left2, flags=re.IGNORECASE).strip()
            right2 = re.sub(r'^(OOS\s+|fe\)\s*)', '', right2, flags=re.IGNORECASE).strip()
            if re.search(r'[A-Za-zÀ-ÿ]', left2) and re.search(r'[A-Za-zÀ-ÿ]', right2):
                return left2, right2
    return None, None

def extrai_todas_opcoes_mercado(lines, start_index=0):
    resultados = []
    for i in range(start_index, len(lines)):
        l = lines[i].strip()
        odd_val = None
        m_odd = re.search(r'([\d]+[.,][\d]+)x\b', l, flags=re.IGNORECASE)
        if m_odd:
            try:
                odd_val = float(m_odd.group(1).replace(',', '.'))
            except:
                odd_val = None
        low = l.lower()
        achou = False
        if re.match(r'.+?[-–—]\s*(Mais de|Under|Over)\s*[\d]+[.,]?[\d]*', l, flags=re.IGNORECASE):
            achou = True
        elif re.search(r'\b(Mais de|Under|Over)\s*[\d]+[.,]?[\d]*', l, flags=re.IGNORECASE):
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
        ocr_text = pytesseract.image_to_string(img, lang='por')
        return ocr_text
    except UnidentifiedImageError as e:
        logger.debug("OCR falhou ao abrir/imagem inválida:", exc_info=e)
    except pytesseract.pytesseract.TesseractError as e:
        logger.debug("OCR TesseractError:", exc_info=e)
    except Exception as e:
        logger.debug("OCR falhou genérico:", exc_info=e)
    return ""
