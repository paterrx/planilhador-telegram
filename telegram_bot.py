# telegram_bot.py

import os
import asyncio
import logging
from telethon import TelegramClient, events
from datetime import datetime

import config
from config import API_ID, API_HASH, BANK_TOTAL, UNIT_SCALES, DEFAULT_SCALE, MONITORADOS
from ocr_utils import limpa_linhas_ocr, extrai_times_de_linhas, extrai_todas_opcoes_mercado, perform_ocr_on_media
from parse_utils import clean_caption, extract_stake, extract_odd, extract_limit, parse_market, detect_competition, summarize_market, normalize_bookmaker_from_url_or_text
from mapping_utils import get_canonical
from dedup_utils import load_seen, save_seen, generate_bet_key
from sheets_utils import init_sheet, append_row
from analysis_utils import HistoricalAnalyzer

logger = logging.getLogger(__name__)

async def main():
    # Solicita número
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

    # Carrega seen e inicializa Google Sheets
    seen = load_seen()
    try:
        sheet = init_sheet()
        # Carrega histórico para aprendizado
        historical = HistoricalAnalyzer(sheet)
    except Exception:
        logger.error("Erro ao inicializar Google Sheets. Saindo.")
        return

    @client.on(events.NewMessage(chats=MONITORADOS))
    async def handler(ev):
        try:
            raw = ev.raw_text or ""
            chat_id = ev.chat_id

            # 1) OCR se houver mídia
            ocr_text = ""
            if ev.message.media:
                ocr_text = await perform_ocr_on_media(ev.message)
            lines = []
            if ocr_text:
                lines = limpa_linhas_ocr(ocr_text)
                logger.debug(f"[OCR] Linhas limpas: {lines}")

            # 2) Limpa legenda
            clean = clean_caption(raw)
            logger.debug(f"[Caption] {clean}")

            # 3) Extrai bookmaker
            bookmaker = normalize_bookmaker_from_url_or_text(clean)

            # 4) Extrai stake_pct; se não houver, ignora
            stake_pct = extract_stake(clean)
            if stake_pct is None:
                logger.debug("Sem stake_pct na legenda; ignora mensagem.")
                return
            odd_caption = extract_odd(clean)
            limit = extract_limit(clean)
            logger.debug(f"Stake_pct={stake_pct}, odd_caption={odd_caption}, limit={limit}")

            # 5) Extrai apostas possíveis via OCR ou legenda
            bets_to_record = []
            # Via OCR
            if lines:
                home, away = extrai_times_de_linhas(lines)
                if home and away:
                    logger.debug(f"Times extraídos via OCR: {home} x {away}")
                    idx = None
                    for i,l in enumerate(lines):
                        if home in l and away in l:
                            idx = i
                            break
                    after = lines[idx+1:] if idx is not None else lines
                    ops = extrai_todas_opcoes_mercado(after, start_index=0)
                    if ops:
                        for mkt_raw, odd_img in ops:
                            bets_to_record.append({
                                'time_casa': home,
                                'time_fora': away,
                                'mercado': mkt_raw.strip(),
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
            # Fallback legenda
            if not bets_to_record:
                home2, away2 = extrai_times_de_linhas([clean])
                if home2 and away2:
                    logger.debug(f"Times extraídos da legenda: {home2} x {away2}")
                    ops2 = extrai_todas_opcoes_mercado([clean], start_index=0)
                    if ops2:
                        for mkt_raw, odd_img in ops2:
                            bets_to_record.append({
                                'time_casa': home2,
                                'time_fora': away2,
                                'mercado': mkt_raw.strip(),
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
                    logger.debug("Não extraiu times da legenda; ignora.")
                    return

            # 6) Para cada aposta, gera bet_key e envia à planilha
            for entry in bets_to_record:
                home = entry['time_casa']
                away = entry['time_fora']
                mercado_raw = entry.get('mercado')
                odd_img = entry.get('odd_img')

                # Determina odd final
                odd_val = odd_img or odd_caption

                # Dedup
                bkey = generate_bet_key(home, away, mercado_raw, odd_val)
                is_dup = bkey in seen
                if not is_dup:
                    seen.add(bkey)
                    save_seen(seen)
                    logger.debug(f"Novo bet_key salvo: {bkey}")
                logger.debug(f"bet_key={bkey}, duplicate={is_dup}")

                # Calcula unidades
                scale = UNIT_SCALES.get(chat_id, DEFAULT_SCALE)
                unit_value = round(BANK_TOTAL/scale, 2)
                rec_amount = unit_value * stake_pct
                if limit is not None and rec_amount > limit:
                    actual_amount = limit
                    actual_units = round(limit/unit_value, 4)
                else:
                    actual_amount = rec_amount
                    actual_units = stake_pct
                logger.debug(f"unit_value={unit_value}, rec_amount={rec_amount}, actual_units={actual_units}, actual_amount={actual_amount}")

                # Canonical names
                canon_home = get_canonical(home)
                canon_away = get_canonical(away)
                logger.debug(f"Canonical: {home}->{canon_home}, {away}->{canon_away}")

                # Parse mercado etc.
                bet_type, selection = parse_market(mercado_raw or "")
                competition = detect_competition(clean + " " + (mercado_raw or ""))
                market_summary = summarize_market(mercado_raw or "")
                logger.debug(f"parse_market -> bet_type={bet_type}, selection={selection}")
                logger.debug(f"competition={competition}, market_summary={market_summary}")

                # Nome do grupo
                try:
                    chat = await ev.get_chat()
                    group_name = getattr(chat, 'title', str(chat_id))
                except:
                    group_name = str(chat_id)

                ts = ev.message.date.isoformat()
                row = [
                    bkey,
                    is_dup,
                    ts,
                    chat_id,
                    group_name,
                    home,        # raw_time_casa
                    away,        # raw_time_fora
                    canon_home,  # time_casa
                    canon_away,  # time_fora
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
                    bookmaker or ''
                ]
                logger.debug(f"Row p/ Sheets: {row}")
                try:
                    await asyncio.to_thread(append_row, sheet, row)
                except Exception as e:
                    logger.error("Erro ao append_row", exc_info=e)

        except Exception as e:
            logger.error("Erro no handler de NewMessage", exc_info=e)

    try:
        await client.run_until_disconnected()
    except KeyboardInterrupt:
        logger.info("Bot encerrado pelo usuário")
