# analysis_utils.py
import logging
from rapidfuzz import process, fuzz

logger = logging.getLogger(__name__)

class HistoricalAnalyzer:
    def __init__(self, sheet, threshold=85):
        self.threshold = threshold
        self.raw_times = set()
        self.raw_to_summary = {}
        self.load_from_sheet(sheet)

    def load_from_sheet(self, sheet):
        try:
            records = sheet.get_all_records()
            for rec in records:
                raw_home = rec.get('raw_time_casa') or ''
                raw_away = rec.get('raw_time_fora') or ''
                mercado_raw = rec.get('mercado_raw') or ''
                summary = rec.get('market_summary') or ''
                if raw_home:
                    self.raw_times.add(raw_home)
                if raw_away:
                    self.raw_times.add(raw_away)
                if mercado_raw and summary:
                    # se houver múltiplas entradas com mesmo raw, permitimos sobrescrever ou manter primeiro
                    if mercado_raw not in self.raw_to_summary:
                        self.raw_to_summary[mercado_raw] = summary
            logger.debug(f"HistoricalAnalyzer: carregado {len(self.raw_times)} nomes e {len(self.raw_to_summary)} resumos de mercado")
        except Exception as e:
            logger.warning("HistoricalAnalyzer: falha ao carregar histórico da planilha", exc_info=e)

    def suggest_canonical(self, raw_name):
        if not raw_name or not self.raw_times:
            return None
        match, score, _ = process.extractOne(raw_name, list(self.raw_times), scorer=fuzz.token_sort_ratio)
        if score >= self.threshold:
            logger.debug(f"HistoricalAnalyzer: raw '{raw_name}' match histórico '{match}' (score {score})")
            return match
        return None

    def suggest_summary(self, mercado_raw):
        if not mercado_raw or not self.raw_to_summary:
            return None
        match, score, _ = process.extractOne(mercado_raw, list(self.raw_to_summary.keys()), scorer=fuzz.token_sort_ratio)
        if score >= self.threshold:
            summary = self.raw_to_summary.get(match)
            logger.debug(f"HistoricalAnalyzer: mercado_raw '{mercado_raw}' match '{match}' resumo '{summary}' (score {score})")
            return summary
        return None

    def update(self, raw_home, raw_away, mercado_raw, summary):
        # atualizar cache em runtime
        if raw_home:
            self.raw_times.add(raw_home)
        if raw_away:
            self.raw_times.add(raw_away)
        if mercado_raw and summary:
            if mercado_raw not in self.raw_to_summary:
                self.raw_to_summary[mercado_raw] = summary
