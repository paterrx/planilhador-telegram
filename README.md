# Planilhador Telegram de Apostas

## Visão geral
Este bot monitora grupos de Telegram de dicas de apostas, extrai informações (times, tipo de aposta, odd, stake%, etc.) de mensagens de texto ou imagens via OCR, e grava tudo em uma Google Sheet.

## Estrutura
- `bot.py`: entrypoint
- `telegram_bot.py`: orquestra Telethon e handlers
- `config.py`: configurações centrais
- `ocr_utils.py`: funções de OCR e extração de texto de imagens
- `parse_utils.py`: parsing de texto em campos estruturados
- `mapping_utils.py`: mapeamento canônico com fuzzy matching
- `dedup_utils.py`: controle de duplicados (seen.json)
- `sheets_utils.py`: integração Google Sheets
- `teams_cache.py`: (opcional) lista de jogos para fuzzy matching
- `requirements.txt`: dependências
- `service_account.json`: credenciais Google (não versionar)
- `seen.json`, `mapping.json`: arquivos gerados durante execução
- `downloads/`: pasta temporária para mídias baixadas

## Pré-requisitos
1. Python 3.9+ e virtualenv:
   ```bash
   python -m venv venv
   source venv/bin/activate    # Linux/macOS
   .\venv\Scripts\activate.bat # Windows
