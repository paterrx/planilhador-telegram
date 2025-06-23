# config.py

from dotenv import load_dotenv
load_dotenv()

import os
import logging

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
    # Exemplo: ajuste conforme seus grupos
    2625305937: 150,   # Arrudex
    2468014496: 100,   # Psicopatas
    2445658326: 100,   # TP Especiais
    2336623429: 100,   # Casebre
    2313268503: 100,   # Pei
    2516014749: 100,   # Feel Tips
    2546110827: 150,   # LuCa Props
    2455542600: 100,   # Peixe Esperto
    # Adicione ou ajuste conforme seus grupos monitorados
}
DEFAULT_SCALE = int(os.getenv("DEFAULT_SCALE", "100"))
MONITORADOS = list(UNIT_SCALES.keys())
logger.info(f"Grupos monitorados: {MONITORADOS}")

# ─── Google Sheets ─────────────────────────────────────────
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "service_account.json")
# Nome da aba que o bot criará ou usará
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
# Lista de competições para detectar
COMPETITIONS = [
    "NBA", "Premier League", "Copa do Mundo", "Champions", "UEFA",
    "La Liga", "Serie A", "Bundesliga", "MLS", "Copa Libertadores",
]

# Linhas de ruído para OCR
import re
RUIDO_LINES = [
    r'^Aposta simples', r'^Imperdíveis', r'^Valor da aposta', r'^OOS\b',
    r'^fe\)', r'^Q \d+:\d+', r'^Hora de decidir', r'^📌', r'^🏠', r'^🆚',
]

# Mapeamento de bookmaker por palavra-chave
BOOKMAKER_MAP = {
    "bet365": "Bet365",
    "betano": "Betano",
    "superbet": "Superbet",
    "apostaganha": "ApostaGanha",
    "betboom": "BetBoom",
    "betfair": "Betfair",
    "novibet": "Novibet",
    "reidopitaco": "ReiDoPitaco",
    "f12bet": "F12Bet",
    "casadeapostas": "CasaDeApostas",
    "hiperbet": "Hiperbet",
    "pixdasorte": "PixDaSorte",
    "betdojogo": "BetDoJogo",
    "betsul": "BetSul",
    "galerabet": "GaleraBet",
    "papigames": "PapiGames",
    "sportybet": "SportyBet",
    "betsson": "Betsson",
    "spinbet": "SpinBet",
    "kto": "KTO",
    "stake": "Stake",
    "betmgm": "BetMGM",
    "sportingbet": "SportingBet",
    "betesporte": "BetEsporte",
    "lancedasorte": "LanceDaSorte",
    "betfast": "BetFast",
    "faz1bet": "Faz1Bet",
    "betnacional": "BetNacional",
    "mrjack": "MrJack",
    "bravobet": "BravoBet",
    "segurobet": "SeguroBet",
    "vaidebet": "VaiDeBet",
    "betpix365": "BetPix365",
    "bolsadeapostas": "BolsaDeApostas",
    "betbra": "BetBra",
    "fulltbet": "FullTBet",
    "brbet": "BRBet",
    "apostou": "Apostou",
    "brasildasorte": "BrasildaSorte",
    "betao": "Betao",
    "vbet": "VBet",
    "xpbet": "XPBet",
    "supremabet": "SupremaBet",
    "blaze": "Blaze",
    "betvip": "BetVIP",
    "jonbet": "JonBet",
    "jogodeouro": "JogoDeOuro",
    "estrelabet": "EstrelaBet",
    "7kbet": "7KBet",
    "cassino": "Cassino",
    "betdasorte": "BetDaSorte",
    "pixbet": "PixBet",
    "multibet": "MultiBet",
    "mcgames": "MCGames",
    "apostatudo": "ApostaTudo",
    "esportiva": "Esportiva",
    "bateubet": "BateuBet",
    "betfusion": "BetFusion",
    "verabet": "VeraBet",
    "mmabet": "MMABet",
    "bullsbet": "BullsBet",
    "pagol": "PagoL",
    "4play": "4Play",
    "goldebet": "GoldeBet",
    "br4bet": "BR4Bet",
    "lotogreen": "LotoGreen"
}

# Regex para stake, odd, limit
PATTERN_STAKE = re.compile(r'([\d]+(?:[.,]\d+)?)\s*(?:%|u)', re.IGNORECASE)
PATTERN_LIMIT = re.compile(r'Limite.*?R\$\s*([\d\.,]+)', re.IGNORECASE)
PATTERN_ODD   = re.compile(r'(?:Odd|🏷|odd justa)\s*([\d\.,]+)', re.IGNORECASE)
