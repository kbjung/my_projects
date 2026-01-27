"""
weekly_mode_switcher.py

주간 모드 전환 로직 (1W ↔ 2_3W)
SPEC.md 5절
"""

import pandas as pd
from typing import Tuple, List, Dict
from datetime import datetime, timedelta

from strategy_config import CONFIG
from indicators import calculate_macd, calculate_sma, calculate_atr
from logger_config import get_logger

logger = get_logger("strategy")


class WeeklyModeSwitcher:
    """
    주간 모드 선택 (1W ↔ 2_3W)
    
    SPEC.md 5.2:
    4가지 조건 중 3개 이상 충족 시 2_3W 모드
    """
    
    def __init__(self):
        self.last_switch_score = 0
        self.last_conditions: List[str] = []
    
    def select_mode(
        self,
        index_candles_d1: pd.DataFrame,
        index_candles_w1: pd.DataFrame = None,
        daily_stop_history: List[Dict] = None
    ) -> Tuple[str, int, List[str]]:
        """
        주간 모드 선택
        
        Args:
            index_candles_d1: 지수 일봉 DataFrame
            index_candles_w1: 지수 주봉 DataFrame (선택)
            daily_stop_history: DAILY 손절 이력
        
        Returns:
            (mode, score, conditions_met)
        """
        conditions_met = []
        score = 0
        
        # 조건 1: 지수 MACD hist 바닥권 상승 전환
        if self._check_index_macd_reversal(index_candles_d1):
            conditions_met.append("지수 MACD 히스토그램 상승 전환")
            score += 1
        
        # 조건 2: 지수 가격 > MA20 AND MA5 > MA20
        if self._check_index_ma_trend(index_candles_d1):
            conditions_met.append("지수 MA 상승 추세 (가격>MA20, MA5>MA20)")
            score += 1
        
        # 조건 3: 변동성 완화 (ATR% 하락)
        if self._check_volatility_reduction(index_candles_d1):
            conditions_met.append("변동성 완화 (ATR% 하락)")
            score += 1
        
        # 조건 4: 최근 DAILY 손절률 >= 50%
        if self._check_daily_stop_rate(daily_stop_history):
            conditions_met.append(f"최근 DAILY 손절률 >= {CONFIG.DAILY_STOP_RATE_THRESHOLD*100}%")
            score += 1
        
        # 모드 결정
        threshold = CONFIG.WEEKLY_MODE_SWITCH_SCORE_THRESHOLD
        mode = "2_3W" if score >= threshold else "1W"
        
        self.last_switch_score = score
        self.last_conditions = conditions_met
        
        logger.info(
            f"주간 모드 선택: {mode} | 점수={score}/{threshold} | "
            f"충족 조건={conditions_met}"
        )
        
        return mode, score, conditions_met
    
    def _check_index_macd_reversal(self, df: pd.DataFrame) -> bool:
        """
        조건 1: 지수 MACD hist 바닥권 상승 전환
        
        - hist[t] < 0 (바닥권)
        - hist[t] > hist[t-1] (상승 전환)
        """
        if len(df) < 2:
            return False
        
        # MACD 계산 (1W 파라미터 사용)
        macd, signal, hist = calculate_macd(df, "1W")
        
        if hist.isna().iloc[-1] or hist.isna().iloc[-2]:
            return False
        
        hist_t = hist.iloc[-1]
        hist_t1 = hist.iloc[-2]
        
        cond1 = hist_t < 0
        cond2 = hist_t > hist_t1
        
        result = cond1 and cond2
        
        logger.debug(f"조건1 (MACD 반전): hist[t]={hist_t:.4f}<0={cond1}, 상승={cond2} -> {result}")
        
        return result
    
    def _check_index_ma_trend(self, df: pd.DataFrame) -> bool:
        """
        조건 2: 지수 가격 > MA20 AND MA5 > MA20
        """
        if len(df) < 20:
            return False
        
        ma5 = calculate_sma(df['close'], 5)
        ma20 = calculate_sma(df['close'], 20)
        
        if ma5.isna().iloc[-1] or ma20.isna().iloc[-1]:
            return False
        
        price = df['close'].iloc[-1]
        ma5_val = ma5.iloc[-1]
        ma20_val = ma20.iloc[-1]
        
        cond1 = price > ma20_val
        cond2 = ma5_val > ma20_val
        
        result = cond1 and cond2
        
        logger.debug(
            f"조건2 (MA 추세): price={price:.2f}>MA20={ma20_val:.2f}={cond1}, "
            f"MA5={ma5_val:.2f}>MA20={cond2} -> {result}"
        )
        
        return result
    
    def _check_volatility_reduction(self, df: pd.DataFrame) -> bool:
        """
        조건 3: 변동성 완화 (ATR% 하락)
        
        ATR% = ATR / close * 100
        최근 ATR%가 과거 평균 대비 감소
        """
        if len(df) < 30:
            return False
        
        atr = calculate_atr(df, period=14)
        
        if atr.isna().iloc[-1]:
            return False
        
        # ATR% 계산
        atr_pct = (atr / df['close']) * 100
        
        # 최근 5일 평균 vs 과거 20일 평균
        recent_atr_pct = atr_pct.iloc[-5:].mean()
        past_atr_pct = atr_pct.iloc[-25:-5].mean()
        
        result = recent_atr_pct < past_atr_pct
        
        logger.debug(
            f"조건3 (변동성): 최근ATR%={recent_atr_pct:.2f} < "
            f"과거ATR%={past_atr_pct:.2f} -> {result}"
        )
        
        return result
    
    def _check_daily_stop_rate(self, daily_stop_history: List[Dict] = None) -> bool:
        """
        조건 4: 최근 DAILY 손절률 >= 50%
        
        Args:
            daily_stop_history: [{"date": "2024-01-01", "result": "SL"/"TP"/"EOD"}, ...]
        """
        if not daily_stop_history:
            logger.debug("조건4 (손절률): 이력 없음 -> False")
            return False
        
        lookback_days = CONFIG.DAILY_STOP_RATE_LOOKBACK_DAYS
        threshold = CONFIG.DAILY_STOP_RATE_THRESHOLD
        
        # 최근 N일 이력 필터
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        recent_history = [
            h for h in daily_stop_history
            if datetime.fromisoformat(h["date"]) >= cutoff_date
        ]
        
        if not recent_history:
            logger.debug("조건4 (손절률): 최근 이력 없음 -> False")
            return False
        
        # 손절 비율 계산
        total = len(recent_history)
        stop_loss_count = sum(1 for h in recent_history if h["result"] == "SL")
        stop_rate = stop_loss_count / total
        
        result = stop_rate >= threshold
        
        logger.debug(
            f"조건4 (손절률): {stop_loss_count}/{total} = {stop_rate:.2%} >= "
            f"{threshold:.2%} -> {result}"
        )
        
        return result
