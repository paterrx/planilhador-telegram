# Planilhador Telegram de Apostas

Este projeto monitora grupos de Telegram que enviam dicas/apostas, extrai informações (times, mercado, odd, stake%, etc.) de mensagens de texto ou imagens via OCR, e grava em uma Google Sheet.

## Estrutura do projeto

- `.devcontainer/`: configuração para GitHub Codespaces ou VSCode Dev Container
  - `devcontainer.json`
  - `Dockerfile`
- `bot.py`: entrypoint que chama `telegram_bot.main()`
- `telegram_bot.py`: orquestra Telethon e handlers de mensagem
- `config.py`: variáveis de configuração (lê env vars)
- `ocr_utils.py`: funções relacionadas a OCR e extração de linhas
- `parse_utils.py`: parsing de texto (stake, odd, limit, mercado, bookmaker, competition, summary)
- `mapping_utils.py`: mapeamento canônico de nomes com fuzzy matching
- `dedup_utils.py`: carregamento/salvamento de seen.json e geração de bet_key
- `sheets_utils.py`: inicialização e gravação em Google Sheets
- `teams_cache.py`: (opcional) funções para carregar lista de times/jogos para fuzzy matching
- `requirements.txt`: dependências do projeto
- `README.md`: instruções de configuração e uso
- Não versionar: `service_account.json`, `.env`, `session.session*`, `seen.json`, `mapping.json`, `downloads/`

## Pré-requisitos

1. **Python 3.9+**  
2. **Tesseract OCR** (opcional, para OCR): no Dev Container já instalado; localmente, instale e configure `TESSERACT_CMD` se necessário.  
3. **Credenciais Telegram**:
   - Obtenha `API_ID` e `API_HASH` em https://my.telegram.org.
   - Defina como variáveis de ambiente `TG_API_ID` e `TG_API_HASH` ou em `.env`.  
4. **Google Sheets API**:
   - Crie Service Account com permissão Editor na planilha.
   - Habilite Sheets API no projeto Google Cloud.
   - Baixe JSON e forneça ao bot via `service_account.json` ou Secret.  
   - Defina `SPREADSHEET_ID` (ID da planilha) em variáveis de ambiente.  
5. **Variáveis de ambiente**:
   - Crie `.env` (não commitado) com:
     ```
     TG_API_ID=...
     TG_API_HASH=...
     SPREADSHEET_ID=...
     SERVICE_ACCOUNT_FILE=service_account.json
     BANK_TOTAL=4000
     LOG_LEVEL=DEBUG
     TESSERACT_CMD=tesseract
     ```
6. **Dependências**:
   ```bash
   pip install -r requirements.txt
