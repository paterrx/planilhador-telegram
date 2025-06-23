# config.py

import os
import json
import logging

# Configure logging de forma global
# Você pode ajustar level para DEBUG quando quiser ver logs detalhados
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Telethon API ───────────────────────────────────────────
API_ID = int(os.getenv("TG_API_ID", "23767719"))
API_HASH = os.getenv("TG_API_HASH", "COLOQUE_SEU_API_HASH_AQUI")

# ─── Banca e escalas ────────────────────────────────────────
# Total da banca em reais
BANK_TOTAL = float(os.getenv("BANK_TOTAL", "4000.0"))

# UNIT_SCALES: mapeia group_id (int) → scale (int)
# Ajuste conforme os IDs que você monitora e a escala de cada grupo.
# Se preferir, mova esse mapeamento para um arquivo JSON e carregue aqui.
UNIT_SCALES = {
    2625305937: 150,   # Arrudex → scale 150
    2468014896: 100,   # Psicopatas → 100
    2445658326: 100,   # TP Especiais → 100
    2336623429: 100,   # Casebre → 100
    2313268503: 100,   # Pei → 100
    2516014749: 100,   # Feel Tips → 100
    2546110827: 150,   # LuCa Props → 150
    2455542600: 100,   # Peixe Esperto → 100
    # Adicione ou ajuste conforme seus grupos...
}
DEFAULT_SCALE = int(os.getenv("DEFAULT_SCALE", "100"))

# MONITORADOS: lista de IDs de grupos a monitorar
MONITORADOS = list(UNIT_SCALES.keys())
logger.info(f"Grupos monitorados: {MONITORADOS}")

# ─── Google Sheets ──────────────────────────────────────────
SPREADSHEET_ID = os.getenv(
    "SPREADSHEET_ID",
    "1zmv8q_XhIeRSXtM4SPu7uXyOU7bfKwt1_I2_oncafCc"
)
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "service_account.json")
# Aba nova que o bot criará se não existir
NEW_TAB = os.getenv("NEW_TAB_NAME", "APOSTAS_BOT")

# ─── OCR / Tesseract ────────────────────────────────────────
# Se precisar configurar o caminho do executável tesseract no Windows, 
# defina TESSERACT_CMD no .env ou edite aqui:
TESSERACT_CMD = os.getenv(
    "TESSERACT_CMD",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)
# Diretório tessdata, se necessário:
TESSDATA_PREFIX = os.getenv(
    "TESSDATA_PREFIX",
    r"C:\Program Files\Tesseract-OCR\tessdata"
)

# Atribui ao pytesseract em runtime:
try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    os.environ.setdefault('TESSDATA_PREFIX', TESSDATA_PREFIX)
    logger.debug(f"Tesseract configurado: cmd={TESSERACT_CMD}, tessdata_prefix={TESSDATA_PREFIX}")
except ImportError:
    logger.warning("pytesseract não está instalado; OCR falhará se usado.")

# ─── Heurísticas (listas de competições, ruídos, bookmakers) ──
# Caso queira expor COMPETITIONS via config ou JSON externo, pode fazer aqui.
COMPETITIONS = [
    "NBA", "Premier League", "Copa do Mundo", "Champions", "UEFA",
    "La Liga", "Serie A", "Bundesliga", "MLS", "Copa Libertadores",
    # adicione mais se quiser
]

# Lista de prefixos ou padrões de linhas a ignorar no OCR:
RUIDO_LINES = [
    r'^Aposta simples', r'^Imperdíveis', r'^Valor da aposta', r'^OOS\b',
    r'^fe\)', r'^Q \d+:\d+', r'^Hora de decidir', r'^📌', r'^🏠', r'^🆚',
    # adicione outros prefixos que identifique como ruído
]

# BOOKMAKER_MAP: reconhece substrings de hostname ou palavras-chave na legenda
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

# Regexes para stake/odd/limit em legenda:
import re
PATTERN_STAKE = re.compile(r'([\d]+(?:[.,]\d+)?)\s*(?:%|u)', re.IGNORECASE)
PATTERN_LIMIT = re.compile(r'Limite.*?R\$\s*([\d\.,]+)', re.IGNORECASE)
PATTERN_ODD   = re.compile(r'(?:Odd|🏷|odd justa)\s*([\d\.,]+)', re.IGNORECASE)
