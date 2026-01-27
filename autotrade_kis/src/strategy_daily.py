"""
strategy_daily.py

DAILY 변동성 돌파 전략 (SPEC.md 3절)
"""

import pandas as pd
from datetime import datetime, time
from typing import Optional, Dict

from strategy_config import CONFIG
from logger_config import get_logger

logger = get_logger("strategy")


class DailyStrategy:
    """
    DAILY 변동성 돌파 전략
    
    SPEC.md 3절 구현:
    - 오프닝 레인지 계산
    - 돌파 신호 감지
    - TP/SL/EOD 청산
    """
    
    def __init__(self):
        self.opening_high: Optional[float] = None
        self.opening_range_end_time: Optional[datetime] = None
    
    def calculate_opening_high(self, candles_m5: pd.DataFrame, market_open_time: datetime) -> float:
        """
        오프닝 레인지 고가 계산
        
        SPEC.md 3.2:
        - 장 시작 후 OPENING_RANGE_MINUTES 구간의 고가
        
        Args:
            candles_m5: M5 캔들 DataFrame
            market_open_time: 장 시작 시각
        
        Returns:
            opening_high
        """
        range_minutes = CONFIG.OPENING_RANGE_MINUTES
        range_end = market_open_time + pd.Timedelta(minutes=range_minutes)
        
        # 오프닝 레인지 구간 필터링
        opening_candles = candles_m5[
            (candles_m5['datetime'] >= market_open_time) &
            (candles_m5['datetime'] < range_end)
        ]
        
        if opening_candles.empty:
            logger.warning("오프닝 레인지 캔들 없음")
            return 0.0
        
        opening_high = opening_candles['high'].max()
        self.opening_high = opening_high
        self.opening_range_end_time = range_end
        
        logger.info(
            f"오프닝 레인지 계산: {market_open_time.strftime('%H:%M')} ~ "
            f"{range_end.strftime('%H:%M')} | opening_high={opening_high}"
        )
        
        return opening_high
    
    def check_breakout_signal(
        self,
        current_price: float,
        current_candle: pd.Series = None,
        volume_filter: bool = False
    ) -> bool:
        """
        돌파 신호 확인
        
        SPEC.md 3.3:
        - last_price > opening_high
        - (선택) 거래량 필터
        
        Args:
            current_price: 현재가
            current_candle: 현재 M5 캔들 (거래량 필터용)
            volume_filter: 거래량 필터 사용 여부
        
        Returns:
            돌파 신호 여부
        """
        if not self.opening_high:
            logger.warning("opening_high가 설정되지 않음")
            return False
        
        # 기본 돌파 조건
        breakout = current_price > self.opening_high
        
        if breakout:
            logger.info(f"DAILY 돌파 발생: 현재가({current_price}) > 기준가({self.opening_high})")
        else:
            logger.debug(f"DAILY 돌파 실패: 현재가({current_price}) <= 기준가({self.opening_high})")
            
        return breakout
    
    def check_tp(self, entry_price: float, current_price: float) -> bool:
        """
        익절(TP) 조건 확인
        
        Args:
            entry_price: 진입가
            current_price: 현재가
        
        Returns:
            TP 도달 여부
        """
        tp_pct = CONFIG.DAILY_TP_PCT
        tp_price = entry_price * (1 + tp_pct)
        
        if current_price >= tp_price:
            logger.info(f"DAILY TP 도달: 현재가={current_price} >= TP={tp_price:.2f}")
            return True
        
        return False
    
    def check_sl(self, entry_price: float, current_price: float) -> bool:
        """
        손절(SL) 조건 확인
        
        Args:
            entry_price: 진입가
            current_price: 현재가
        
        Returns:
            SL 도달 여부
        """
        sl_pct = CONFIG.DAILY_SL_PCT
        sl_price = entry_price * (1 + sl_pct)
        
        if current_price <= sl_price:
            logger.warning(f"DAILY SL 도달: 현재가={current_price} <= SL={sl_price:.2f}")
            return True
        
        return False
    
    def check_eod(self, current_time: datetime, market_close_time: time = time(15, 20)) -> bool:
        """
        장 종료 전 청산(EOD) 조건 확인
        
        SPEC.md 3.4:
        - 장 종료 전 포지션 강제 청산
        
        Args:
            current_time: 현재 시각
            market_close_time: 장 마감 시각 (기본 15:20)
        
        Returns:
            EOD 청산 여부
        """
        current_time_only = current_time.time()
        
        if current_time_only >= market_close_time:
            logger.info(f"DAILY EOD 청산: 현재시각={current_time_only} >= 마감={market_close_time}")
            return True
        
        return False
    
    def reset(self) -> None:
        """일일 상태 초기화"""
        self.opening_high = None
        self.opening_range_end_time = None
        logger.info("DAILY 전략 상태 초기화")
