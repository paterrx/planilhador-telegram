# analysis_utils.py

import logging

logger = logging.getLogger(__name__)

class HistoricalAnalyzer:
    """
    Lê a planilha existente para aprender mapeamentos raw_time -> canonical_time
    e mercado_raw -> market_summary, conforme correções manuais feitas na planilha.
    Depois, permite sugerir canonical e summary para novas entradas.
    """
    def __init__(self, sheet):
        """
        sheet: objeto gspread Worksheet já inicializado, com cabeçalho na primeira linha.
        """
        self.sheet = sheet
        # Dicionários de aprendizado:
        # raw_time_casa -> time_casa corrigido
        self.map_time_casa = {}
        # raw_time_fora -> time_fora corrigido
        self.map_time_fora = {}
        # mercado_raw -> market_summary corrigido
        self.map_summary = {}
        # Opcional: poderíamos mapear competição, bookmaker, etc, mas foco em nomes e resumo.
        self._load_existing()

    def _load_existing(self):
        """
        Lê todas as linhas atuais da planilha, armazena mapeamentos onde raw!=canon
        ou mercado_raw mapeado para summary diferente.
        """
        try:
            # Obtém todos os valores; primeira linha é header
            all_values = self.sheet.get_all_values()
        except Exception as e:
            logger.error("HistoricalAnalyzer: falha ao ler todas as linhas da planilha", exc_info=e)
            return

        if len(all_values) <= 1:
            # Sem dados
            return

        header = all_values[0]
        # Mapeia índices conforme HEADER esperado
        # Confirme posição:
        # header: ["bet_key", "duplicate", "data_hora", "group_id", "group_name", "raw_message_identified",
        #          "raw_time_casa", "raw_time_fora", "time_casa", "time_fora",
        #          "mercado_raw", "market_summary", ... , "sport"]
        # Índices 0-based:
        try:
            idx_raw_home = header.index("raw_time_casa")
            idx_raw_away = header.index("raw_time_fora")
            idx_can_home = header.index("time_casa")
            idx_can_away = header.index("time_fora")
            idx_raw_mkt = header.index("mercado_raw")
            idx_sum = header.index("market_summary")
        except ValueError as e:
            logger.error("HistoricalAnalyzer: cabeçalho não contém colunas esperadas", exc_info=e)
            return

        # Percorre linhas de dados
        for row in all_values[1:]:
            # Assegura tamanho suficiente
            if len(row) <= max(idx_raw_home, idx_can_home, idx_raw_mkt, idx_sum):
                continue
            raw_home = row[idx_raw_home].strip()
            raw_away = row[idx_raw_away].strip()
            can_home = row[idx_can_home].strip()
            can_away = row[idx_can_away].strip()
            raw_mkt = row[idx_raw_mkt].strip()
            sum_mkt = row[idx_sum].strip()

            # Se houver correção manual: raw_home não vazio e can_home diferente de raw_home
            if raw_home and can_home and raw_home != can_home:
                # memorize, mas se já houver valor, você pode optar por não sobrescrever
                if raw_home not in self.map_time_casa:
                    self.map_time_casa[raw_home] = can_home
            if raw_away and can_away and raw_away != can_away:
                if raw_away not in self.map_time_fora:
                    self.map_time_fora[raw_away] = can_away
            # Mercado summary
            if raw_mkt and sum_mkt and raw_mkt != sum_mkt:
                if raw_mkt not in self.map_summary:
                    self.map_summary[raw_mkt] = sum_mkt

        logger.info(f"HistoricalAnalyzer: mapeamentos carregados: "
                    f"time_casa({len(self.map_time_casa)}), "
                    f"time_fora({len(self.map_time_fora)}), "
                    f"summary({len(self.map_summary)})")

    def suggest_canonical(self, raw_name: str) -> str | None:
        """
        Se tivermos mapeamento para raw_name, retorna o canonical aprendido.
        """
        if not raw_name:
            return None
        # Busca exata. Poderíamos também implementar busca por proximidade, mas cuidado.
        return self.map_time_casa.get(raw_name) or self.map_time_fora.get(raw_name)

    def suggest_summary(self, mercado_raw: str) -> str | None:
        """
        Se tivermos mapeamento para mercado_raw, retorna summary aprendido.
        """
        if not mercado_raw:
            return None
        return self.map_summary.get(mercado_raw)

    def update(self, raw_home: str, raw_away: str, raw_mkt: str, summary: str):
        """
        Após inserir nova linha, podemos também atualizar o histórico em runtime,
        caso queira que correções manuais feitas imediatamente reflitam:
        - Se raw!=canonical, mas neste ponto canonical foi sugerido automaticamente, 
          não alteramos. Correções manuais precisam ser disparadas se o usuário editar a planilha.
        - Se quiser re-ler toda a planilha sempre, pode chamar _load_existing(), mas isso é custoso.
        Aqui, não fazemos nada automático.
        """
        # Se preferir, re-ler planilha a cada certo número de linhas inseridas, ou permitir comando manual de recarregar histórico.
        pass
