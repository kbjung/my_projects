"""
indicators.py

기술적 지표 계산 모듈 (WEEKLY 전략용 H1 타임프레임)
SPEC.md 4.3절 정의 준수
"""

import pandas as pd
import numpy as np
from typing import Tuple, Literal

from strategy_config import CONFIG
from logger_config import get_logger

logger = get_logger("indicators")


def calculate_bollinger_bands(
    df: pd.DataFrame,
    mode: Literal["1W", "2_3W"]
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    볼린저 밴드 계산 (SMA 기반)
    
    SPEC.md 4.3.1:
    - mid[t] = SMA(close, N)[t]
    - sd[t] = STD(close, N)[t]
    - upper[t] = mid[t] + K * sd[t]
    - lower[t] = mid[t] - K * sd[t]
    
    Args:
        df: 캔들 DataFrame (컬럼: close)
        mode: 주간 모드 (1W 또는 2_3W)
    
    Returns:
        (upper, mid, lower) Series
    """
    if mode == "1W":
        period = CONFIG.BB_PERIOD_1W
        std_multiplier = CONFIG.BB_STD_1W
    else:  # 2_3W
        period = CONFIG.BB_PERIOD_2_3W
        std_multiplier = CONFIG.BB_STD_2_3W
    
    # SMA (중심선)
    mid = df['close'].rolling(window=period).mean()
    
    # 표준편차
    std = df['close'].rolling(window=period).std()
    
    # 상단/하단 밴드
    upper = mid + (std_multiplier * std)
    lower = mid - (std_multiplier * std)
    
    logger.debug(f"BB 계산 완료: mode={mode}, period={period}, K={std_multiplier}")
    
    return upper, mid, lower


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """
    지수 이동평균 (EMA) 계산
    
    Args:
        series: 가격 Series
        period: 기간
    
    Returns:
        EMA Series
    """
    return series.ewm(span=period, adjust=False).mean()


def calculate_macd(
    df: pd.DataFrame,
    mode: Literal["1W", "2_3W"]
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    MACD 계산 (EMA 기반)
    
    SPEC.md 4.3.2:
    - ema_fast[t] = EMA(close, fast)[t]
    - ema_slow[t] = EMA(close, slow)[t]
    - macd[t] = ema_fast[t] - ema_slow[t]
    - signal[t] = EMA(macd, macd_signal_period)[t]
    - hist[t] = macd[t] - signal[t]
    
    Args:
        df: 캔들 DataFrame
        mode: 주간 모드
    
    Returns:
        (macd, signal, hist) Series
    """
    if mode == "1W":
        fast = CONFIG.MACD_FAST_1W
        slow = CONFIG.MACD_SLOW_1W
        signal_period = CONFIG.MACD_SIGNAL_1W
    else:  # 2_3W
        fast = CONFIG.MACD_FAST_2_3W
        slow = CONFIG.MACD_SLOW_2_3W
        signal_period = CONFIG.MACD_SIGNAL_2_3W
    
    # EMA 계산
    ema_fast = calculate_ema(df['close'], fast)
    ema_slow = calculate_ema(df['close'], slow)
    
    # MACD 라인
    macd = ema_fast - ema_slow
    
    # 시그널 라인
    signal = calculate_ema(macd, signal_period)
    
    # 히스토그램
    hist = macd - signal
    
    logger.debug(f"MACD 계산 완료: mode={mode}, fast={fast}, slow={slow}, signal={signal_period}")
    
    return macd, signal, hist


def calculate_volume_ma(
    df: pd.DataFrame,
    mode: Literal["1W", "2_3W"]
) -> pd.Series:
    """
    거래량 이동평균 계산
    
    SPEC.md 4.3.3:
    - vol_ma[t] = SMA(vol, V)[t]
    
    Args:
        df: 캔들 DataFrame (컬럼: volume)
        mode: 주간 모드
    
    Returns:
        거래량 MA Series
    """
    if mode == "1W":
        period = CONFIG.VOL_MA_PERIOD_1W
    else:  # 2_3W
        period = CONFIG.VOL_MA_PERIOD_2_3W
    
    vol_ma = df['volume'].rolling(window=period).mean()
    
    logger.debug(f"거래량 MA 계산 완료: mode={mode}, period={period}")
    
    return vol_ma


def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """
    단순 이동평균 (SMA) 계산
    
    Args:
        series: 가격 Series
        period: 기간
    
    Returns:
        SMA Series
    """
    return series.rolling(window=period).mean()


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Average True Range (ATR) 계산
    
    Args:
        df: 캔들 DataFrame (컬럼: high, low, close)
        period: 기간
    
    Returns:
        ATR Series
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # True Range 계산
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # ATR = TR의 이동평균
    atr = tr.rolling(window=period).mean()
    
    return atr


def add_all_indicators(
    df: pd.DataFrame,
    mode: Literal["1W", "2_3W"]
) -> pd.DataFrame:
    """
    모든 지표를 DataFrame에 추가
    
    Args:
        df: 캔들 DataFrame
        mode: 주간 모드
    
    Returns:
        지표가 추가된 DataFrame
    """
    df = df.copy()
    
    # 볼린저 밴드
    df['bb_upper'], df['bb_mid'], df['bb_lower'] = calculate_bollinger_bands(df, mode)
    
    # MACD
    df['macd'], df['macd_signal'], df['macd_hist'] = calculate_macd(df, mode)
    
    # 거래량 MA
    df['vol_ma'] = calculate_volume_ma(df, mode)
    
    # 추가 지표 (모드 전환용)
    df['sma_5'] = calculate_sma(df['close'], 5)
    df['sma_20'] = calculate_sma(df['close'], 20)
    df['atr'] = calculate_atr(df)
    
    logger.info(f"모든 지표 계산 완료: mode={mode}, rows={len(df)}")
    
    return df
