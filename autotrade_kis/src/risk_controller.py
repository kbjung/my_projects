"""
risk_controller.py

리스크 규칙 강제 모듈
"""

from typing import Tuple
from datetime import datetime

from state_manager import StateManager
from strategy_config import CONFIG
from logger_config import get_logger

logger = get_logger("risk")


class RiskController:
    """
    리스크 규칙 강제
    
    SPEC.md 2절 (절대 규칙):
    - A-1: 손절 후 당일 정지
    - A-2: 1포지션 정책
    - A-3: 물타기 금지
    """
    
    def __init__(self, state_manager: StateManager):
        self.state = state_manager
    
    def validate_entry(self) -> Tuple[bool, str]:
        """
        진입 전 검증
        
        Returns:
            (허용 여부, 사유)
        """
        # A-2: 1포지션 정책
        position_state = self.state.get_position_state()
        if position_state != "NONE":
            return False, f"1포지션 정책 위반: 현재 {position_state} 포지션 보유 중"
        
        # A-1: 손절 후 당일 정지
        if self.state.get_daily_stop_triggered():
            return False, "당일 손절 발생으로 신규 진입 차단 (daily_stop_triggered=True)"
        
        # 자본 확인
        equity = self.state.get_equity()
        if equity < CONFIG.CAPITAL_FIXED_KRW * 0.5:  # 50% 이하 시 경고
            logger.warning(f"자본 부족 경고: equity={equity} < 최소 요구={CONFIG.CAPITAL_FIXED_KRW*0.5}")
        
        return True, "진입 허용"
    
    def check_exit_conditions(
        self,
        position_type: str,
        entry_price: float,
        current_price: float,
        current_time: datetime,
        days_held: int = 0
    ) -> Tuple[bool, str]:
        """
        청산 조건 확인
        
        Args:
            position_type: DAILY 또는 WEEKLY
            entry_price: 진입가
            current_price: 현재가
            current_time: 현재 시각
            days_held: 보유 영업일 (WEEKLY용)
        
        Returns:
            (청산 여부, 사유)
        """
        if position_type == "DAILY":
            return self._check_daily_exit(entry_price, current_price, current_time)
        elif position_type == "WEEKLY":
            return self._check_weekly_exit(entry_price, current_price, days_held)
        else:
            return False, "알 수 없는 포지션 타입"
    
    def _check_daily_exit(
        self,
        entry_price: float,
        current_price: float,
        current_time: datetime
    ) -> Tuple[bool, str]:
        """DAILY 청산 조건 (TP/SL/EOD)"""
        # TP
        tp_pct = CONFIG.DAILY_TP_PCT
        tp_price = entry_price * (1 + tp_pct)
        if current_price >= tp_price:
            return True, "TP"
        
        # SL
        sl_pct = CONFIG.DAILY_SL_PCT
        sl_price = entry_price * (1 + sl_pct)
        if current_price <= sl_price:
            return True, "SL"
        
        # EOD (15:20 기준)
        if current_time.time() >= datetime.strptime("15:20", "%H:%M").time():
            return True, "EOD"
        
        return False, ""
    
    def _check_weekly_exit(
        self,
        entry_price: float,
        current_price: float,
        days_held: int
    ) -> Tuple[bool, str]:
        """WEEKLY 청산 조건 (TP/SL/TIME)"""
        mode = self.state.get_weekly_mode()
        
        # TP
        if mode == "1W":
            tp_pct = CONFIG.WEEKLY_TP_PCT_1W
            max_days = CONFIG.WEEKLY_TIME_STOP_DAYS_1W
        else:
            tp_pct = CONFIG.WEEKLY_TP_PCT_2_3W
            max_days = CONFIG.WEEKLY_TIME_STOP_DAYS_2_3W
        
        tp_price = entry_price * (1 + tp_pct)
        if current_price >= tp_price:
            return True, "TP"
        
        # SL
        if mode == "1W":
            sl_pct = CONFIG.WEEKLY_SL_PCT_1W
        else:
            sl_pct = CONFIG.WEEKLY_SL_PCT_2_3W
        
        sl_price = entry_price * (1 + sl_pct)
        if current_price <= sl_price:
            return True, "SL"
        
        # TIME STOP
        if days_held >= max_days:
            return True, "TIME"
        
        return False, ""
    
    def on_stop_loss(self) -> None:
        """
        손절 발생 시 처리
        
        A-1: daily_stop_triggered = True
        """
        self.state.set_daily_stop_triggered(True)
        logger.warning("손절 발생: daily_stop_triggered=True, 당일 신규 진입 차단")
