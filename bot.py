# bot.py

import asyncio
import logging
from telegram_bot import main

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error("Erro ao executar bot.py", exc_info=e)
# bot.py

import asyncio
import logging
from telegram_bot import main

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error("Erro ao executar bot.py", exc_info=e)
