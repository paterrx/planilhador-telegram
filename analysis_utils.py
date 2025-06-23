# analysis_utils.py

import logging
from typing import Optional, Dict, Tuple, List, Any
import threading

logger = logging.getLogger(__name__)

class HistoricalAnalyzer:
    """
    Mantém um histórico das entradas gravadas na planilha para sugerir
    canonicalizações e resumos baseados em exemplos anteriores.
    """

    def __init__(self, sheet):
        self.sheet = sheet
        # Estrutura interna para mapear raw_name -> canonical sugerido
        self._canonical_map: Dict[str, str] = {}
        # Para resumos de mercado: raw_market -> summary
        self._summary_map: Dict[str, str] = {}
        # Carrega existentes na planilha
        self._load_existing()
        # Se desejar thread-safe:
        self._lock = threading.Lock()

    def _load_existing(self) -> None:
        """
        Lê todas as linhas existentes na aba e popula os mapas.
        Presume que a planilha já tenha cabeçalho conforme HEADER em sheets_utils.
        """
        try:
            # pega todas as linhas: cada row é lista de strings
            all_values = self.sheet.get_all_values()
            # A primeira linha é o cabeçalho
            header = all_values[0] if all_values else []
            # Encontre índices de colunas que interessam:
            # raw_home está em coluna 'raw_time_casa' e raw_away em 'raw_time_fora',
            # market_summary em 'market_summary'.
            # Ajuste conforme HEADER real; supondo HEADER conforme sheets_utils:
            # ["bet_key", "duplicate", "data_hora", "group_id", "group_name",
            #  "raw_time_casa", "raw_time_fora", "time_casa", "time_fora",
            #  "mercado_raw", "market_summary", ...]
            try:
                idx_raw_home = header.index("raw_time_casa")
                idx_raw_away = header.index("raw_time_fora")
                idx_summary = header.index("market_summary")
            except ValueError:
                logger.warning("HistoricalAnalyzer: não encontrou colunas esperadas no cabeçalho")
                return

            # Itera das linhas já preenchidas (pular cabeçalho)
            for row in all_values[1:]:
                if len(row) <= max(idx_raw_home, idx_raw_away, idx_summary):
                    continue
                raw_home = row[idx_raw_home].strip()
                raw_away = row[idx_raw_away].strip()
                summary = row[idx_summary].strip()
                # Se canonical já estiver preenchido (colunas time_casa/time_fora), podemos mapear:
                # ex.: coluna time_casa em índice header.index("time_casa")
                try:
                    idx_canon_home = header.index("time_casa")
                    idx_canon_away = header.index("time_fora")
                    canon_home = row[idx_canon_home].strip() if len(row) > idx_canon_home else ""
                    canon_away = row[idx_canon_away].strip() if len(row) > idx_canon_away else ""
                except ValueError:
                    canon_home = ""
                    canon_away = ""
                # Só armazena se both raw e canon estiverem não vazios e diferentes
                if raw_home and canon_home:
                    with self._lock:
                        self._canonical_map[raw_home] = canon_home
                if raw_away and canon_away:
                    with self._lock:
                        self._canonical_map[raw_away] = canon_away
                # Para summary
                if summary:
                    with self._lock:
                        # Use raw mercado como chave? ou summary já manual?
                        # Aqui só guardamos se não existir
                        if summary not in self._summary_map.values():
                            # Mapear raw string -> summary: mas não temos raw mercado aqui.
                            # Se quiser, pode usar coluna 'mercado_raw' para índice:
                            try:
                                idx_raw_market = header.index("mercado_raw")
                                raw_market = row[idx_raw_market].strip() if len(row) > idx_raw_market else ""
                            except ValueError:
                                raw_market = ""
                            if raw_market:
                                self._summary_map[raw_market] = summary
        except Exception as e:
            logger.error("HistoricalAnalyzer: falha em _load_existing", exc_info=e)

    def suggest_canonical(self, raw_name: str) -> Optional[str]:
        """
        Se já tivermos visto raw_name parecido antes, sugere canonical previamente usado.
        Retorna None se não houver sugestão.
        """
        with self._lock:
            # Checagem exata; pode aprimorar com fuzzy matching
            return self._canonical_map.get(raw_name)

    def suggest_summary(self, mercado_raw: str) -> Optional[str]:
        """
        Se já tivermos um resumo para este mercado_raw, retorna-o, ou None.
        """
        with self._lock:
            return self._summary_map.get(mercado_raw)

    def update(self, raw_home: str, raw_away: str, mercado_raw: str, summary: str) -> None:
        """
        Atualiza histórico com nova entrada após gravar na planilha.
        """
        with self._lock:
            # Se ainda não existe, adiciona
            if raw_home and summary:
                # opcional: checar duplicatas
                if raw_home not in self._canonical_map:
                    # mas qual canonical usar? o código que chama deve usar get_canonical ou outra
                    # Aqui não definimos novo mapping automático; este método registra apenas summary e raw pair.
                    pass
            # Para summary:
            if mercado_raw and summary:
                if mercado_raw not in self._summary_map:
                    self._summary_map[mercado_raw] = summary
        # Não reescreve planilha, pois o usuário edita manualmente; apenas mantemos em memória
