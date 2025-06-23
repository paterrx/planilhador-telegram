# config.py

from dotenv import load_dotenv
load_dotenv()

import os
import logging
import re

# Logging global
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Telegram API ───────────────────────────────────────────
try:
    API_ID = int(os.getenv("TG_API_ID", "0"))
except:
    API_ID = 0
API_HASH = os.getenv("TG_API_HASH", "")
if not API_ID or not API_HASH:
    logger.warning("TG_API_ID ou TG_API_HASH não definidos ou inválidos")

# ─── Banca e escalas ────────────────────────────────────────
try:
    BANK_TOTAL = float(os.getenv("BANK_TOTAL", "4000"))
except:
    BANK_TOTAL = 4000.0

# UNIT_SCALES: mapeia group_id (int) → escala (int)
UNIT_SCALES = {
    # Ajuste conforme seus grupos
    2625305937: 150,   # Arrudex
    2468014496: 100,   # Psicopatas
    2445658326: 100,   # TP Especiais
    2336623429: 100,   # Casebre
    2313268503: 100,   # Pei
    2516014749: 100,   # Feel Tips
    2546110827: 150,   # LuCa Props
    2455542600: 100,   # Peixe Esperto
}
DEFAULT_SCALE = int(os.getenv("DEFAULT_SCALE", "100"))
MONITORADOS = list(UNIT_SCALES.keys())
logger.info(f"Grupos monitorados: {MONITORADOS}")

# ─── Google Sheets ─────────────────────────────────────────
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "service_account.json")
NEW_TAB = os.getenv("NEW_TAB_NAME", "APOSTAS_BOT")

# ─── OCR / Tesseract ────────────────────────────────────────
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "tesseract")
TESSDATA_PREFIX = os.getenv("TESSDATA_PREFIX", "")
try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    if TESSDATA_PREFIX:
        os.environ.setdefault('TESSDATA_PREFIX', TESSDATA_PREFIX)
    logger.debug(f"Tesseract configurado: cmd={TESSERACT_CMD}, tessdata_prefix={TESSDATA_PREFIX}")
except ImportError:
    logger.warning("pytesseract não instalado; OCR falhará")

# ─── Heurísticas ───────────────────────────────────────────
COMPETITIONS = [
    "NBA", "Premier League", "Copa do Mundo", "Champions", "UEFA",
    "La Liga", "Serie A", "Bundesliga", "MLS", "Copa Libertadores",
    # Adicione outras competições frequentes
]

SPORTS_KEYWORDS = [
    "tênis", "tenis", "futebol", "basquete", "basketball",
    "vôlei", "volei", "voleibol", "handebol", "hóquei", "hockey",
    # Adicione outros esportes
]

# Linhas de ruído para OCR / caption
RUIDO_LINES = [
    r'^Aposta simples', r'^Imperdíveis', r'^Valor da aposta', r'^OOS\b',
    r'^fe\)', r'^Q \d+:\d+', r'^Hora de decidir', r'^📌', r'^🏠', r'^🆚',
    # Outros padrões
]

# Mapeamento de bookmaker por palavra-chave
BOOKMAKER_MAP = {
    "bet365": "Bet365",
    "betano": "Betano",
    "superbet": "Superbet",
    # ... (restante conforme antes)
    "lotogreen": "LotoGreen"
}

# Regex para stake, odd, limit
PATTERN_STAKE = re.compile(r'([\d]+(?:[.,]\d+)?)\s*(?:%|u)', re.IGNORECASE)
PATTERN_LIMIT = re.compile(r'Limite.*?R\$\s*([\d\.,]+)', re.IGNORECASE)
PATTERN_ODD   = re.compile(r'(?:Odd|🏷|odd justa)\s*([\d\.,]+)', re.IGNORECASE)
