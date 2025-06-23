# sheets_utils.py

import logging
import gspread
from google.oauth2.service_account import Credentials
from config import SERVICE_ACCOUNT_FILE, SPREADSHEET_ID, NEW_TAB

logger = logging.getLogger(__name__)

# sheets_utils.py

HEADER = [
    "bet_key", "duplicate", "data_hora", "group_id", "group_name",
    "raw_mensagem_identificada",
    "raw_time_casa", "raw_time_fora",
    "time_casa", "time_fora",
    "mercado_raw", "market_summary", "odd", "stake_pct",
    "actual_units", "scale", "unit_value", "amount_real", "placed",
    "selection", "bet_type", "competition", "bookmaker", "sport"
]



def init_sheet():
    # Carrega credenciais
    try:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    except Exception as e:
        logger.error("Falha ao carregar service_account.json", exc_info=e)
        raise
    try:
        gc = gspread.authorize(creds)
    except Exception as e:
        logger.error("Falha ao autorizar gspread", exc_info=e)
        raise

    try:
        ss = gc.open_by_key(SPREADSHEET_ID)
    except Exception as e:
        logger.error(f"Falha ao abrir planilha com ID {SPREADSHEET_ID}", exc_info=e)
        raise

    try:
        titles = [ws.title for ws in ss.worksheets()]
        logger.info(f"Aba(s) existentes: {titles}")
        if NEW_TAB in titles:
            sheet = ss.worksheet(NEW_TAB)
            logger.info(f"Usando aba existente '{NEW_TAB}'")
        else:
            sheet = ss.add_worksheet(title=NEW_TAB, rows=2000, cols=len(HEADER))
            logger.info(f"Aba '{NEW_TAB}' criada")
    except Exception as e:
        logger.error("Falha ao selecionar/criar aba", exc_info=e)
        raise

    # Inserir cabeçalho se necessário
    try:
        existing = sheet.row_values(1)
    except Exception:
        existing = []
    if existing != HEADER:
        try:
            # Insere no topo: deleta linhas extras antes, se necessário?
            # Aqui assumimos que se já existir algo diferente, inserimos cabeçalho na linha 1.
            sheet.insert_row(HEADER, index=1)
            logger.info("Cabeçalho inserido na planilha")
        except Exception as e:
            try:
                sheet.append_row(HEADER, value_input_option='USER_ENTERED')
                logger.info("Cabeçalho adicionado via append_row")
            except Exception as e2:
                logger.error("Falha ao inserir cabeçalho", exc_info=e2)
    else:
        logger.info("Cabeçalho já presente")
    return sheet

def append_row(sheet, row: list):
    try:
        sheet.append_row(row, value_input_option='USER_ENTERED')
        logger.info("Linha enviada ao Google Sheets")
    except Exception as e:
        logger.error("Falha ao append_row no Google Sheets", exc_info=e)
        raise
