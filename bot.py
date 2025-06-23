# bot.py

import asyncio
import logging

# Reduz logs muito verbosos do Telethon
logging.getLogger("telethon").setLevel(logging.WARNING)
logging.getLogger("telethon.network").setLevel(logging.WARNING)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

from telegram_bot import main

if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    try:
        asyncio.run(main())
    except Exception:
        logger.error("Erro ao executar bot.py", exc_info=True)
