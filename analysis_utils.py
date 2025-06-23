# analysis_utils.py

import logging
import threading
from typing import Optional, Dict, List
from collections import Counter

logger = logging.getLogger(__name__)

class HistoricalAnalyzer:
    """
    Mantém mapeamentos de nomes canônicos e resumos de mercado a partir das entradas já existentes na planilha,
    e também mapeamento de adversários para sugerir oponente em casos como “Time ou Empate”.
    """

    def __init__(self, sheet):
        """
        sheet: objeto gspread Worksheet já inicializado, com cabeçalho conforme HEADER em sheets_utils.
        """
        self.sheet = sheet
        self._canonical_map: Dict[str, str] = {}     # raw_name -> canonical
        self._summary_map: Dict[str, str] = {}       # raw_market -> summary
        self._opponents_map: Dict[str, Counter] = {} # canonical_team -> Counter(opponent_name)
        self._lock = threading.Lock()
        self._load_existing()

    def _load_existing(self) -> None:
        """
        Carrega todas as linhas existentes da aba na memória para extrair mapeamentos:
        - raw_time_casa -> time_casa (canônico)
        - raw_time_fora -> time_fora (canônico)
        - mercado_raw -> market_summary
        - time_casa <-> time_fora em _opponents_map
        """
        try:
            all_values: List[List[str]] = self.sheet.get_all_values()
            if not all_values:
                return
            header = all_values[0]
            # Espera colunas conforme sheets_utils.HEADER
            # Encontrar índices pelas strings exatas:
            try:
                idx_raw_home = header.index("raw_time_casa")
                idx_raw_away = header.index("raw_time_fora")
                idx_canon_home = header.index("time_casa")
                idx_canon_away = header.index("time_fora")
                idx_raw_market = header.index("mercado_raw")
                idx_summary = header.index("market_summary")
            except ValueError:
                logger.warning(
                    "HistoricalAnalyzer: cabeçalho inesperado ou colunas ausentes. Não carregará histórico."
                )
                return

            for row in all_values[1:]:
                # Proteção: verificar comprimento suficiente
                if len(row) <= max(idx_raw_home, idx_raw_away, idx_canon_home, idx_canon_away, idx_raw_market, idx_summary):
                    continue
                raw_home = row[idx_raw_home].strip()
                raw_away = row[idx_raw_away].strip()
                canon_home = row[idx_canon_home].strip()
                canon_away = row[idx_canon_away].strip()
                raw_market = row[idx_raw_market].strip()
                summary = row[idx_summary].strip()

                # canonical mapping
                if raw_home and canon_home:
                    with self._lock:
                        if raw_home not in self._canonical_map:
                            self._canonical_map[raw_home] = canon_home
                if raw_away and canon_away:
                    with self._lock:
                        if raw_away not in self._canonical_map:
                            self._canonical_map[raw_away] = canon_away

                # summary mapping
                if raw_market and summary:
                    with self._lock:
                        if raw_market not in self._summary_map:
                            self._summary_map[raw_market] = summary

                # opponents mapping (baseado em canonical)
                if canon_home and canon_away:
                    with self._lock:
                        if canon_home not in self._opponents_map:
                            self._opponents_map[canon_home] = Counter()
                        if canon_away not in self._opponents_map:
                            self._opponents_map[canon_away] = Counter()
                        self._opponents_map[canon_home][canon_away] += 1
                        self._opponents_map[canon_away][canon_home] += 1

            logger.info(
                f"HistoricalAnalyzer: carregado {len(self._canonical_map)} mapeamentos canônicos, "
                f"{len(self._summary_map)} resumos e {len(self._opponents_map)} times em histórico."
            )
        except Exception as e:
            logger.error("HistoricalAnalyzer: falha ao carregar histórico existente", exc_info=e)

    def suggest_canonical(self, raw_name: str) -> Optional[str]:
        """
        Sugere nome canônico para raw_name se já conhecido no histórico; caso contrário, None.
        """
        if not raw_name:
            return None
        with self._lock:
            return self._canonical_map.get(raw_name)

    def suggest_summary(self, mercado_raw: str) -> Optional[str]:
        """
        Sugere resumo de mercado para mercado_raw se já conhecido no histórico; caso contrário, None.
        """
        if not mercado_raw:
            return None
        with self._lock:
            return self._summary_map.get(mercado_raw)

    def suggest_opponent(self, raw_name: str) -> Optional[str]:
        """
        Dada uma raw_name (ex.: 'Palmeiras'), tenta obter canonical ou normalizar, e buscar
        em histórico adversário frequente:
        - Se houver apenas um adversário no histórico ou um claro mais frequente, retorna-o.
        - Caso contrário, None.
        """
        if not raw_name:
            return None
        with self._lock:
            canonical = self._canonical_map.get(raw_name, raw_name)
            counter = self._opponents_map.get(canonical)
            if counter:
                most_common = counter.most_common(1)
                if most_common:
                    opponent, count = most_common[0]
                    return opponent
        return None

    def update(self, raw_home: str, raw_away: str, mercado_raw: str, summary: str) -> None:
        """
        Atualiza o histórico em memória com nova entrada após planilhar:
        Apenas mapeamentos de mercado_summary; nomes e opponents aguardam reload manual (/reload_history).
        """
        if mercado_raw and summary:
            with self._lock:
                if raw_market := mercado_raw.strip():
                    if raw_market not in self._summary_map:
                        self._summary_map[raw_market] = summary

    def reload(self) -> None:
        """
        Recarrega todo o histórico a partir da planilha; pode ser chamado via comando.
        """
        with self._lock:
            self._canonical_map.clear()
            self._summary_map.clear()
            self._opponents_map.clear()
        self._load_existing()
