# telegram_bot.py

import os
import asyncio
import logging
import base64
from datetime import timezone

# reduzir logs verbosos do telethon
logging.getLogger("telethon").setLevel(logging.WARNING)
logging.getLogger("telethon.network").setLevel(logging.WARNING)

from telethon import TelegramClient, events

import config
from config import API_ID, API_HASH, BANK_TOTAL, UNIT_SCALES, DEFAULT_SCALE, MONITORADOS
from ocr_utils import limpa_linhas_ocr, extrai_times_de_linhas, extrai_todas_opcoes_mercado, perform_ocr_on_media
from parse_utils import (
    clean_caption,
    extract_stake,
    extract_stake_list,
    extract_odd,
    extract_odd_list,
    extract_limit,
    parse_market,
    detect_competition,
    detect_sport,
    summarize_market as summarize_fallback
)
from mapping_utils import get_canonical, normalize_bookmaker_from_url_or_text
from dedup_utils import load_seen, save_seen, generate_bet_key
from sheets_utils import init_sheet, append_row
from analysis_utils import HistoricalAnalyzer

logger = logging.getLogger(__name__)

def ensure_service_account_file():
    """
    Decodifica SERVICE_ACCOUNT_JSON_B64 e escreve em disco no caminho SERVICE_ACCOUNT_FILE.
    Se SERVICE_ACCOUNT_JSON_B64 não existir, verifica se SERVICE_ACCOUNT_FILE já existe localmente.
    """
    sa_b64 = os.getenv("SERVICE_ACCOUNT_JSON_B64")
    sa_file = os.getenv("SERVICE_ACCOUNT_FILE", "service_account.json")
    if sa_b64:
        try:
            data = base64.b64decode(sa_b64)
        except Exception as e:
            logger.error("Falha ao decodificar SERVICE_ACCOUNT_JSON_B64", exc_info=e)
            raise
        try:
            with open(sa_file, "wb") as f:
                f.write(data)
            logger.info(f"Service Account JSON escrito em '{sa_file}' a partir de SERVICE_ACCOUNT_JSON_B64")
        except Exception as e:
            logger.error("Falha ao escrever arquivo de credenciais Service Account", exc_info=e)
            raise
    else:
        # Se não há Base64, espera que o arquivo já exista localmente
        if not os.path.exists(sa_file):
            logger.error(f"Service account file '{sa_file}' não encontrado e SERVICE_ACCOUNT_JSON_B64 não definido.")
            raise FileNotFoundError(f"Service account file '{sa_file}' não existe e nenhuma credencial em SERVICE_ACCOUNT_JSON_B64.")
        else:
            logger.info(f"Usando service account existente em '{sa_file}'")

async def main():
    # Garante credenciais antes de init_sheet
    ensure_service_account_file()

    phone = input("📱 Número (+55...): ").strip()
    client = TelegramClient('session', API_ID, API_HASH)
    await client.start(phone=phone)
    if not await client.is_user_authorized():
        pwd = input("🔑 Senha 2FA (ou Enter pular): ").strip()
        if pwd:
            await client.sign_in(password=pwd)

    me = await client.get_me()
    logger.info(f"Conectado como @{me.username} (ID {me.id})")
    logger.info(f"Monitorando grupos: {MONITORADOS}")

    seen = load_seen()
    try:
        sheet = init_sheet()
        historical = HistoricalAnalyzer(sheet)
    except Exception:
        logger.error("Erro ao inicializar Google Sheets. Saindo.")
        return

    @client.on(events.NewMessage(pattern=r'/reload_history'))
    async def reload_history(ev):
        try:
            historical.reload()
            await ev.reply("✅ Histórico recarregado a partir da planilha.")
        except Exception as e:
            logger.error("Erro ao recarregar histórico", exc_info=e)
            await ev.reply(f"❌ Falha ao recarregar histórico: {e}")

    @client.on(events.NewMessage(chats=MONITORADOS))
    async def handler(ev):
        try:
            raw = ev.raw_text or ""
            chat_id = ev.chat_id

            # 1) OCR se houver mídia
            ocr_text = ""
            if ev.message.media:
                try:
                    ocr_text = await perform_ocr_on_media(ev.message)
                except Exception as e:
                    logger.debug("perform_ocr_on_media falhou", exc_info=e)
            lines = []
            if ocr_text:
                lines = limpa_linhas_ocr(ocr_text)
                logger.debug(f"[OCR] Linhas limpas: {lines}")

            # 2) Limpa legenda/texto
            clean = clean_caption(raw)
            logger.debug(f"[Caption limpa] {clean}")

            # RAW_MENSAGEM_IDENTIFICADA: combina legenda limpa e OCR cru
            if ocr_text:
                raw_msg_identified = f"{clean} || OCR: {ocr_text}"
            else:
                raw_msg_identified = clean

            # 3) Extrai bookmaker
            bookmaker = normalize_bookmaker_from_url_or_text(clean)
            logger.debug(f"Bookmaker detectado: {bookmaker}")

            # 4) Extrai stake(s) e odd(s) da legenda
            stake_list = extract_stake_list(clean)
            if not stake_list:
                logger.debug("Sem stake_pct na legenda; ignora mensagem.")
                return
            odd_caption_list = extract_odd_list(clean)
            odd_single = extract_odd(clean)
            limit = extract_limit(clean)
            logger.debug(f"Stake_list={stake_list}, odd_caption_list={odd_caption_list}, limit={limit}")

            # 5) Extrai possíveis apostas via OCR ou legenda
            bets_to_record = []
            if lines:
                try:
                    home, away = extrai_times_de_linhas(lines)
                except Exception as e:
                    home = away = None
                    logger.debug("Erro em extrai_times_de_linhas via OCR", exc_info=e)
                if home and away:
                    logger.debug(f"Times extraídos via OCR: {home} x {away}")
                    idx0 = None
                    for i, l in enumerate(lines):
                        if home in l and away in l:
                            idx0 = i
                            break
                    after = lines[idx0+1:] if idx0 is not None else lines
                    try:
                        ops = extrai_todas_opcoes_mercado(after, start_index=0)
                    except Exception as e:
                        ops = None
                        logger.debug("Erro em extrai_todas_opcoes_mercado via OCR", exc_info=e)
                    if ops:
                        for mkt_raw, odd_img in ops:
                            bets_to_record.append({
                                'time_casa': home,
                                'time_fora': away,
                                'mercado': mkt_raw.strip() if mkt_raw else None,
                                'odd_img': odd_img
                            })
                        logger.debug(f"Encontradas {len(ops)} opções via OCR")
                    else:
                        bets_to_record.append({
                            'time_casa': home,
                            'time_fora': away,
                            'mercado': None,
                            'odd_img': None
                        })
                else:
                    logger.debug("OCR não extraiu times confiáveis.")
            if not bets_to_record:
                try:
                    home2, away2 = extrai_times_de_linhas([clean])
                except Exception as e:
                    home2 = away2 = None
                    logger.debug("Erro em extrai_times_de_linhas na legenda", exc_info=e)
                if home2 and away2:
                    logger.debug(f"Times extraídos da legenda: {home2} x {away2}")
                    try:
                        ops2 = extrai_todas_opcoes_mercado([clean], start_index=0)
                    except Exception as e:
                        ops2 = None
                        logger.debug("Erro em extrai_todas_opcoes_mercado na legenda", exc_info=e)
                    if ops2:
                        for mkt_raw, odd_img in ops2:
                            bets_to_record.append({
                                'time_casa': home2,
                                'time_fora': away2,
                                'mercado': mkt_raw.strip() if mkt_raw else None,
                                'odd_img': odd_img
                            })
                        logger.debug(f"Encontradas {len(ops2)} opções via legenda")
                    else:
                        bets_to_record.append({
                            'time_casa': home2,
                            'time_fora': away2,
                            'mercado': None,
                            'odd_img': None
                        })
                else:
                    logger.debug("Não extraiu times da legenda via OCR/regex.")
                    # 5.b) Fallback adicional: padrões como "Time ou Empate"
                    # Exemplo: "Palmeiras ou Empate" ou "Team ou Draw"
                    m = None
                    # tenta detectar "<Team> ou Empate"
                    pat = re.search(r'([A-Za-zÀ-ÿ0-9\s]+?)\s+ou\s+Empate', clean, flags=re.IGNORECASE)
                    if pat:
                        team_raw = pat.group(1).strip()
                        # Tenta canonicalizar via histórico ou mapping_utils
                        canon_team = historical.suggest_canonical(team_raw) or get_canonical(team_raw)
                        # Tenta sugerir adversário via histórico
                        opponent = historical.suggest_opponent(canon_team)
                        if opponent:
                            logger.debug(f"Fallback 'ou Empate': detectou time '{team_raw}', sugeriu adversário '{opponent}'")
                            bets_to_record.append({
                                'time_casa': canon_team,
                                'time_fora': opponent,
                                'mercado': clean,  # manter raw para análise de mercado
                                'odd_img': None
                            })
                    if not bets_to_record:
                        logger.debug("Ignorando mensagem: sem times confiáveis e sem fallback histórico.")
                        return

            # 6) Lógica de casamento múltiplos mercados <-> múltiplos stakes (escada)
            num_markets = len(bets_to_record)
            num_stakes = len(stake_list)
            num_odds_caption = len(odd_caption_list)
            logger.debug(f"num_markets={num_markets}, num_stakes={num_stakes}, num_odds_caption={num_odds_caption}")

            # 7) Detecta esporte
            sport = detect_sport(raw_msg_identified)
            logger.debug(f"Esporte detectado: {sport}")

            # 8) Processa cada sub-aposta
            for idx, entry in enumerate(bets_to_record):
                raw_home = entry['time_casa']
                raw_away = entry['time_fora']
                mercado_raw = entry.get('mercado')
                odd_img = entry.get('odd_img')

                # stake_pct por índice (escada)
                if num_stakes >= num_markets:
                    stake_pct = stake_list[idx]
                else:
                    stake_pct = stake_list[0]
                # odd final
                if odd_img is not None:
                    odd_val = odd_img
                else:
                    if num_odds_caption >= num_markets:
                        odd_val = odd_caption_list[idx]
                    else:
                        odd_val = odd_single
                logger.debug(f"[Índice {idx}] stake_pct={stake_pct}, odd_val={odd_val}")

                # Dedup
                bkey = generate_bet_key(raw_home, raw_away, mercado_raw, odd_val)
                is_dup = bkey in seen
                if not is_dup:
                    seen.add(bkey)
                    save_seen(seen)
                    logger.debug(f"Novo bet_key salvo: {bkey}")
                logger.debug(f"bet_key={bkey}, duplicate={is_dup}")

                # Unidades
                scale = UNIT_SCALES.get(chat_id, DEFAULT_SCALE)
                unit_value = round(BANK_TOTAL / scale, 2)
                rec_amount = unit_value * stake_pct
                if limit is not None and rec_amount > limit:
                    actual_amount = limit
                    actual_units = round(limit / unit_value, 4)
                else:
                    actual_amount = rec_amount
                    actual_units = stake_pct
                logger.debug(f"unit_value={unit_value}, rec_amount={rec_amount}, actual_units={actual_units}, actual_amount={actual_amount}")

                # Canonicalização com histórico
                suggest_home = historical.suggest_canonical(raw_home)
                suggest_away = historical.suggest_canonical(raw_away)
                canon_home = suggest_home if suggest_home else get_canonical(raw_home)
                canon_away = suggest_away if suggest_away else get_canonical(raw_away)
                logger.debug(f"Canonical: '{raw_home}' -> '{canon_home}', '{raw_away}' -> '{canon_away}'")

                # Parse mercado
                bet_type, selection = parse_market(mercado_raw or "")
                competition = detect_competition(clean + " " + (mercado_raw or "")) or ""
                summary_parse = "" if not mercado_raw else summarize_fallback(mercado_raw)
                summary_hist = historical.suggest_summary(mercado_raw or "")
                market_summary = summary_hist if summary_hist else (summary_parse or "")
                logger.debug(f"market_summary escolhido: {market_summary}")

                # Nome do grupo
                try:
                    chat = await ev.get_chat()
                    group_name = getattr(chat, 'title', str(chat_id))
                except:
                    group_name = str(chat_id)

                ts = ev.message.date.astimezone(timezone.utc).isoformat()

                row = [
                    bkey,
                    is_dup,
                    ts,
                    chat_id,
                    group_name,
                    raw_msg_identified,  # RAW_MENSAGEM_IDENTIFICADA
                    raw_home,
                    raw_away,
                    canon_home,
                    canon_away,
                    mercado_raw or '',
                    market_summary or '',
                    odd_val or '',
                    stake_pct,
                    actual_units,
                    scale,
                    unit_value,
                    round(actual_amount, 2),
                    '',
                    selection or '',
                    bet_type or '',
                    competition or '',
                    bookmaker or '',
                    sport or ''
                ]
                logger.debug(f"[Índice {idx}] Row p/ Sheets: {row}")
                try:
                    await asyncio.to_thread(append_row, sheet, row)
                except Exception as e:
                    logger.error("Erro ao append_row", exc_info=e)

                # Atualiza histórico apenas de mercado para futuras sugestões (nome aguarda recarga manual)
                historical.update(raw_home, raw_away, mercado_raw or "", market_summary or "")

        except Exception:
            logger.error("Erro no handler de NewMessage", exc_info=True)

    try:
        logger.info("▶️ Bot rodando. Monitorando mensagens dos grupos listados acima.")
        await client.run_until_disconnected()
    except KeyboardInterrupt:
        logger.info("Bot encerrado pelo usuário")
