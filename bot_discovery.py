# bot_discovery.py

import asyncio
from telethon import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty

# ─── SUAS CREDENCIAIS ───────────────────────────
API_ID   = 23767719
API_HASH = '238e12910fd0755bd76d58b09705fe9c'
# ─────────────────────────────────────────────────

async def main():
    client = TelegramClient('session', API_ID, API_HASH)
    await client.start()
    print("✅ Conectado! Buscando todos os dialogs...")

    # Pega até 200 chats (ajuste limit se precisar mais)
    result = await client(GetDialogsRequest(
        offset_date=None,
        offset_id=0,
        offset_peer=InputPeerEmpty(),
        limit=200,
        hash=0
    ))

    print("\n📋 Lista de chats:")
    for chat in result.chats:
        # Alguns chats não têm title (privados), então checamos
        nome = getattr(chat, 'title', None) or getattr(chat, 'username', None) or '—sem título—'
        print(f"   ID: {chat.id}   |   {nome}")

    await client.disconnect()
    print("\n✅ Pronto! Anote os IDs dos grupos que quer monitorar e coloque em MONITORADOS.")

if __name__ == '__main__':
    asyncio.run(main())
