"""
strategy_weekly.py

WEEKLY 볼린저 + MACD + 거래량 전략 (SPEC.md 4절)
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Tuple, Literal

from strategy_config import CONFIG
from indicators import add_all_indicators
from logger_config import get_logger

logger = get_logger("strategy")


class WeeklyStrategy:
    """
    WEEKLY 전략 (볼린저 밴드 + MACD + 거래량)
    
    SPEC.md 4절 구현:
    - H1 신호 평가 (weekly_signal_h1)
    - M5 진입 타이밍
    - TP/SL/시간손절
    """
    
    def __init__(self, mode: Literal["1W", "2_3W"] = "1W"):
        self.mode = mode
        self.signal_candle_time: Optional[datetime] = None
        self.weekly_signal_h1: bool = False

    def select_complete_h1_candles(self, candles_h1: pd.DataFrame, now: datetime) -> pd.DataFrame:
        """
        H1 완성봉만 선택

        - 타임스탬프 해석:
          * 시작 시각이면 ts + 60min <= now 인 봉만 사용
          * 종료 시각이면 ts <= now 인 봉만 사용
        - 방어적으로 데이터 이상 시 마지막 1개 추가 제외
        """
        if candles_h1 is None or candles_h1.empty:
            return candles_h1

        df = candles_h1.copy()

        if "datetime" not in df.columns:
            logger.warning("H1 캔들에 datetime 컬럼 없음: 마지막 1개 제외")
            return df.iloc[:-1].reset_index(drop=True) if len(df) > 1 else df

        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        df = df.dropna(subset=["datetime"]).sort_values("datetime").reset_index(drop=True)

        if df.empty:
            return df

        tf = timedelta(minutes=CONFIG.TF_SIGNAL_MIN)
        ts = df["datetime"]

        ts_is_start = CONFIG.H1_TIMESTAMP_IS_START
        if ts_is_start is None:
            ts_is_start = self._infer_timestamp_is_start(ts, now, tf)

        if ts_is_start:
            complete_mask = (ts + tf) <= now
        else:
            complete_mask = ts <= now

        df_complete = df[complete_mask].reset_index(drop=True)

        if df_complete.empty and len(df) > 1:
            logger.warning("H1 완성봉 판단 실패: 마지막 1개 제외")
            return df.iloc[:-1].reset_index(drop=True)

        if self._needs_fallback_drop(df_complete, now):
            logger.warning("H1 타임스탬프 이상 감지: 마지막 1개 추가 제외")
            return df_complete.iloc[:-1].reset_index(drop=True) if len(df_complete) > 1 else df_complete

        return df_complete

    def _infer_timestamp_is_start(self, ts: pd.Series, now: datetime, tf: timedelta) -> bool:
        """타임스탬프가 시작 시각인지 보수적으로 추정"""
        if ts.empty:
            return True

        last_ts = ts.iloc[-1]

        if last_ts is pd.NaT:
            return True

        if last_ts > now:
            return True

        # 마지막 봉이 아직 완성되지 않았을 가능성이 높으면 시작 시각으로 간주
        if last_ts + tf > now:
            return True

        return False

    def _needs_fallback_drop(self, df: pd.DataFrame, now: datetime) -> bool:
        """데이터 이상 징후가 있으면 마지막 봉을 추가 제외"""
        if df is None or df.empty or len(df) < 2:
            return False

        ts = df["datetime"]

        if not ts.is_monotonic_increasing:
            return True

        if ts.duplicated().any():
            return True

        if ts.iloc[-1] > now:
            return True

        return False
    
    def evaluate_h1_signal(self, candles_h1: pd.DataFrame, is_complete_candle: bool = True) -> bool:
        """
        H1 신호 평가 (weekly_signal_h1)
        
        SPEC.md 4.4:
        - weekly_signal_h1 = bb_reentry_h1 AND macd_recover_h1 AND vol_confirm_h1
        - 반드시 H1 완성봉에서만 평가
        
        Args:
            candles_h1: H1 캔들 DataFrame (지표 포함)
            is_complete_candle: 완성봉 여부
        
        Returns:
            weekly_signal_h1
        """
        # C-0: 미완성봉으로는 신호 생성 불가
        if not is_complete_candle:
            logger.debug("H1 미완성봉: 신호 평가 스킵")
            return False
        
        # 지표 계산
        df = add_all_indicators(candles_h1, self.mode)
        
        if len(df) < 3:
            logger.warning("H1 캔들 부족: 신호 평가 불가")
            return False
        
        # 최신 완성봉 (t)
        t = -1
        
        # 3가지 조건 평가
        bb_reentry = self._check_bb_reentry_h1(df, t)
        macd_recover = self._check_macd_recover_h1(df, t)
        vol_confirm = self._check_vol_confirm_h1(df, t)
        
        # 신호 논거(Rationale) 상세 로깅
        logger.info(
            f"WEEKLY 신호 논거: [BB 재진입={bb_reentry}], [MACD 회복={macd_recover}], [거래량 확인={vol_confirm}]"
        )
        
        # AND 조건
        signal = bb_reentry and macd_recover and vol_confirm
        
        # 추가 보수 필터 (선택)
        if signal and CONFIG.REQUIRE_SIGNAL_CANDLE_UP:
            candle_up = df.iloc[t]['close'] > df.iloc[t-1]['close']
            if not candle_up:
                logger.info("신호봉 상승 필터: close[t] <= close[t-1], 신호 무효")
                signal = False
        
        if signal:
            self.weekly_signal_h1 = True
            self.signal_candle_time = df.iloc[t]['datetime']
            logger.info(
                f"WEEKLY H1 신호 발생: {self.signal_candle_time} | "
                f"bb_reentry={bb_reentry}, macd_recover={macd_recover}, vol_confirm={vol_confirm}"
            )
        else:
            logger.debug(
                f"WEEKLY H1 신호 없음: bb_reentry={bb_reentry}, "
                f"macd_recover={macd_recover}, vol_confirm={vol_confirm}"
            )
        
        return signal
    
    def _check_bb_reentry_h1(self, df: pd.DataFrame, t: int) -> bool:
        """
        볼린저 밴드 재진입 조건
        
        SPEC.md 4.4.1 (A안):
        - close[t-1] <= lower[t-1]
        - close[t] > lower[t]
        """
        variant = CONFIG.BB_REENTRY_VARIANT
        
        if variant == "A":
            # A안 (엄격)
            cond1 = df.iloc[t-1]['close'] <= df.iloc[t-1]['bb_lower']
            cond2 = df.iloc[t]['close'] > df.iloc[t]['bb_lower']
            result = cond1 and cond2
            
            logger.debug(
                f"bb_reentry_h1 (A안): close[t-1]={df.iloc[t-1]['close']:.2f} <= "
                f"lower[t-1]={df.iloc[t-1]['bb_lower']:.2f} = {cond1}, "
                f"close[t]={df.iloc[t]['close']:.2f} > lower[t]={df.iloc[t]['bb_lower']:.2f} = {cond2}"
            )
        
        elif variant == "B":
            # B안 (완화): 최근 3봉 중 1봉이라도 하단 터치
            touched = False
            for k in range(t-3, t):
                if df.iloc[k]['low'] <= df.iloc[k]['bb_lower']:
                    touched = True
                    break
            
            cond2 = df.iloc[t]['close'] > df.iloc[t]['bb_lower']
            result = touched and cond2
            
            logger.debug(f"bb_reentry_h1 (B안): touched={touched}, close[t] > lower[t] = {cond2}")
        
        else:
            logger.error(f"알 수 없는 BB 변형: {variant}")
            result = False
        
        return result
    
    def _check_macd_recover_h1(self, df: pd.DataFrame, t: int) -> bool:
        """
        MACD 회복 조건
        
        SPEC.md 4.4.2:
        - hist[t] < 0
        - hist[t] > hist[t-1] > hist[t-2] (연속 2봉 증가)
        - (macd[t] >= signal[t]) OR (macd[t] > macd[t-1])
        """
        hist_t = df.iloc[t]['macd_hist']
        hist_t1 = df.iloc[t-1]['macd_hist']
        hist_t2 = df.iloc[t-2]['macd_hist']
        
        macd_t = df.iloc[t]['macd']
        signal_t = df.iloc[t]['macd_signal']
        macd_t1 = df.iloc[t-1]['macd']
        
        # 필수 조건
        cond1 = hist_t < 0
        cond2 = hist_t > hist_t1 > hist_t2
        
        # 추가 조건 (OR)
        cond3 = (macd_t >= signal_t) or (macd_t > macd_t1)
        
        result = cond1 and cond2 and cond3
        
        logger.debug(
            f"macd_recover_h1: hist[t]={hist_t:.4f} < 0 = {cond1}, "
            f"hist 연속증가={cond2}, 추가조건={cond3}"
        )
        
        return result
    
    def _check_vol_confirm_h1(self, df: pd.DataFrame, t: int) -> bool:
        """
        거래량 확인 조건
        
        SPEC.md 4.4.3:
        - vol[t] >= vol_ma[t] * vol_factor
        - (선택) vol_spike_filter: vol[t] <= vol_ma[t] * vol_max_spike
        """
        vol_t = df.iloc[t]['volume']
        vol_ma_t = df.iloc[t]['vol_ma']
        
        if self.mode == "1W":
            vol_factor = CONFIG.VOL_FACTOR_1W
        else:
            vol_factor = CONFIG.VOL_FACTOR_2_3W
        
        # 기본 조건
        cond1 = vol_t >= vol_ma_t * vol_factor
        
        # 뉴스성 폭증 필터
        cond2 = True
        if CONFIG.VOL_SPIKE_FILTER_ENABLED:
            cond2 = vol_t <= vol_ma_t * CONFIG.VOL_MAX_SPIKE
        
        result = cond1 and cond2
        
        logger.debug(
            f"vol_confirm_h1: vol[t]={vol_t} >= vol_ma[t]*{vol_factor}={vol_ma_t*vol_factor:.0f} = {cond1}, "
            f"spike_filter={cond2}"
        )
        
        return result
    
    def check_m5_entry_timing(
        self,
        candles_m5: pd.DataFrame,
        current_time: datetime
    ) -> bool:
        """
        M5 진입 타이밍 확인
        
        SPEC.md 4.5:
        - H1 신호봉 마감 이후 entry_window_minutes 이내
        - close_5m(now) > max(high_5m[-1..-L])
        
        Args:
            candles_m5: M5 캔들 DataFrame
            current_time: 현재 시각
        
        Returns:
            진입 가능 여부
        """
        if not self.weekly_signal_h1 or not self.signal_candle_time:
            logger.debug("H1 신호 없음: M5 진입 불가")
            return False
        
        # 윈도우 체크
        window_minutes = CONFIG.ENTRY_WINDOW_MINUTES
        window_end = self.signal_candle_time + timedelta(minutes=window_minutes)
        
        if current_time > window_end:
            logger.info(f"진입 윈도우 만료: {current_time} > {window_end}")
            self.weekly_signal_h1 = False  # 신호 무효화
            return False
        
        # M5 돌파 조건
        lookback = CONFIG.ENTRY_5M_BREAKOUT_LOOKBACK
        
        if len(candles_m5) < lookback + 1:
            logger.warning("M5 캔들 부족")
            return False
        
        current_close = candles_m5.iloc[-1]['close']
        recent_highs = candles_m5.iloc[-(lookback+1):-1]['high']
        max_high = recent_highs.max()
        
        breakout = current_close > max_high
        
        if breakout:
            logger.info(
                f"WEEKLY M5 진입 조건 충족: close={current_close} > "
                f"max(high[-{lookback}])={max_high}"
            )
        
        return breakout
    
    def check_tp(self, entry_price: float, current_price: float) -> bool:
        """익절 조건"""
        if self.mode == "1W":
            tp_pct = CONFIG.WEEKLY_TP_PCT_1W
        else:
            tp_pct = CONFIG.WEEKLY_TP_PCT_2_3W
        
        tp_price = entry_price * (1 + tp_pct)
        
        if current_price >= tp_price:
            logger.info(f"WEEKLY TP 도달: {current_price} >= {tp_price:.2f}")
            return True
        
        return False
    
    def check_sl(self, entry_price: float, current_price: float) -> bool:
        """손절 조건"""
        if self.mode == "1W":
            sl_pct = CONFIG.WEEKLY_SL_PCT_1W
        else:
            sl_pct = CONFIG.WEEKLY_SL_PCT_2_3W
        
        sl_price = entry_price * (1 + sl_pct)
        
        if current_price <= sl_price:
            logger.warning(f"WEEKLY SL 도달: {current_price} <= {sl_price:.2f}")
            return True
        
        return False
    
    def check_time_stop(self, days_held: int) -> bool:
        """시간손절 조건 (영업일 기준)"""
        if self.mode == "1W":
            max_days = CONFIG.WEEKLY_TIME_STOP_DAYS_1W
        else:
            max_days = CONFIG.WEEKLY_TIME_STOP_DAYS_2_3W
        
        if days_held >= max_days:
            logger.info(f"WEEKLY 시간손절: {days_held}일 >= {max_days}일")
            return True
        
        return False
    
    def check_early_exit(self, candles_h1: pd.DataFrame) -> bool:
        """
        조기 청산 조건 (선택)
        
        SPEC.md 4.7:
        - hist[t] < hist[t-1]
        - close[t] < mid[t]
        - close[t] <= close[t-1]
        """
        if not CONFIG.ENABLE_EARLY_EXIT_WEEKLY:
            return False
        
        df = add_all_indicators(candles_h1, self.mode)
        
        if len(df) < 2:
            return False
        
        t = -1
        
        cond1 = df.iloc[t]['macd_hist'] < df.iloc[t-1]['macd_hist']
        cond2 = df.iloc[t]['close'] < df.iloc[t]['bb_mid']
        cond3 = df.iloc[t]['close'] <= df.iloc[t-1]['close']
        
        early_exit = cond1 and cond2 and cond3
        
        if early_exit:
            logger.info("WEEKLY 조기청산 조건 충족")
        
        return early_exit
    
    def reset(self) -> None:
        """신호 초기화"""
        self.weekly_signal_h1 = False
        self.signal_candle_time = None
        logger.info("WEEKLY 전략 상태 초기화")
