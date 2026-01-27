"""
strategy_config.py

전략의 모든 수치/정책을 한 곳에서 고정하기 위한 설정 파일.
STRATEGY.md(설명), SPEC.md(규격), ACCEPTANCE.md(통과조건)과 동기화되어야 한다.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TradingConfig:
    # Capital policy
    CAPITAL_FIXED_KRW: int = 500_000

    # Position policy
    ALLOW_MULTIPLE_POSITIONS: bool = False
    BLOCK_ALL_ENTRIES_AFTER_DAILY_STOP: bool = True  # 손절 1번이면 당일 신규진입 전면 차단

    # Daily strategy (Volatility Breakout)
    DAILY_TP_PCT: float = 0.008   # +0.8% (권장: 0.005~0.010)
    DAILY_SL_PCT: float = -0.004  # -0.4% (권장: -0.003~-0.005)
    OPENING_RANGE_MINUTES: int = 10  # 5~15분 중 고정값

    # Timeframes (minutes)
    TF_ENTRY_MIN: int = 5
    TF_SIGNAL_MIN: int = 60  # WEEKLY 신호봉: H1(60분봉) 고정

    # Weekly exits — 1W mode
    WEEKLY_TP_PCT_1W: float = 0.025
    WEEKLY_SL_PCT_1W: float = -0.009
    WEEKLY_TIME_STOP_DAYS_1W: int = 5

    # Weekly exits — 2_3W mode
    WEEKLY_TP_PCT_2_3W: float = 0.04
    WEEKLY_SL_PCT_2_3W: float = -0.013
    WEEKLY_TIME_STOP_DAYS_2_3W: int = 10

    # Weekly indicator params — 1W mode
    BB_PERIOD_1W: int = 20
    BB_STD_1W: float = 2.0
    MACD_FAST_1W: int = 12
    MACD_SLOW_1W: int = 26
    MACD_SIGNAL_1W: int = 9
    VOL_MA_PERIOD_1W: int = 10

    # Weekly indicator params — 2_3W mode (slower)
    BB_PERIOD_2_3W: int = 35
    BB_STD_2_3W: float = 2.2
    MACD_FAST_2_3W: int = 19
    MACD_SLOW_2_3W: int = 39
    MACD_SIGNAL_2_3W: int = 9
    VOL_MA_PERIOD_2_3W: int = 15

    # Weekly signal rules (H1 -> M5 entry)
    BB_REENTRY_VARIANT: str = "A"  # "A" or "B"
    MACD_HIST_UP_BARS: int = 2

    VOL_FACTOR_1W: float = 1.05
    VOL_FACTOR_2_3W: float = 1.10

    VOL_SPIKE_FILTER_ENABLED: bool = True
    VOL_MAX_SPIKE: float = 3.0

    ENTRY_WINDOW_MINUTES: int = 120
    ENTRY_5M_BREAKOUT_LOOKBACK: int = 3

    REQUIRE_SIGNAL_CANDLE_UP: bool = False  # close[t] > close[t-1] 필터(선택)

    # Weekly mode switch
    WEEKLY_MODE_SWITCH_SCORE_THRESHOLD: int = 3
    DAILY_STOP_RATE_LOOKBACK_DAYS: int = 10  # 최근 2주(영업일 근사)
    DAILY_STOP_RATE_THRESHOLD: float = 0.5   # 손절률 >= 50%

    # Execution constraints
    DAILY_MAX_ENTRIES_PER_DAY: int = 1

    # Optional feature
    ENABLE_EARLY_EXIT_WEEKLY: bool = False  # 처음엔 False 권장


CONFIG = TradingConfig()
