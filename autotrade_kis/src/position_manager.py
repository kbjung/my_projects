"""
position_manager.py

포지션 생명주기 관리 모듈
"""

from datetime import datetime
from typing import Optional, Literal, Dict

from state_manager import StateManager
from strategy_config import CONFIG
from logger_config import get_logger

logger = get_logger("position")


class PositionManager:
    """
    포지션 생명주기 관리
    
    - 포지션 진입/청산 조정
    - 포지션 사이징
    - PnL 추적
    """
    
    def __init__(self, state_manager: StateManager):
        self.state = state_manager
    
    def calculate_position_size(self, price: float, capital: float = None) -> int:
        """
        포지션 사이즈 계산 (고정 자본)
        
        Args:
            price: 진입 예정 가격
            capital: 사용 자본 (None이면 고정 자본 사용)
        
        Returns:
            매수 수량
        """
        if capital is None:
            capital = CONFIG.CAPITAL_FIXED_KRW
        
        # 수량 = 자본 / 가격 (소수점 버림)
        quantity = int(capital / price)
        
        logger.info(f"포지션 사이즈 계산: 자본={capital}, 가격={price}, 수량={quantity}")
        
        return quantity
    
    def enter_position(
        self,
        position_type: Literal["DAILY", "WEEKLY"],
        symbol: str,
        entry_price: float,
        entry_time: datetime = None
    ) -> bool:
        """
        포지션 진입
        
        Args:
            position_type: DAILY 또는 WEEKLY
            symbol: 종목 코드
            entry_price: 진입가
            entry_time: 진입 시각
        
        Returns:
            진입 성공 여부
        """
        if entry_time is None:
            entry_time = datetime.now()
        
        # 진입 가능 여부 확인
        can_enter, reason = self.state.can_enter_new_position()
        if not can_enter:
            logger.warning(f"포지션 진입 불가: {reason}")
            return False
        
        # 상태 업데이트
        self.state.open_position(position_type, symbol, entry_price, entry_time)
        
        logger.info(
            f"포지션 진입 완료: {position_type} | {symbol} | "
            f"진입가={entry_price} | 시각={entry_time}"
        )
        
        return True
    
    def exit_position(self, exit_price: float, reason: str) -> bool:
        """
        포지션 청산
        
        Args:
            exit_price: 청산가
            reason: 청산 사유 (TP/SL/EOD/TIME/EARLY_EXIT)
        
        Returns:
            청산 성공 여부
        """
        position_state = self.state.get_position_state()
        
        if position_state == "NONE":
            logger.warning("청산할 포지션 없음")
            return False
        
        # 상태 업데이트
        self.state.close_position(exit_price, reason)
        
        logger.info(f"포지션 청산 완료: 청산가={exit_price}, 사유={reason}")
        
        return True
    
    def get_current_pnl_pct(self, current_price: float) -> Optional[float]:
        """
        현재 손익률 계산
        
        Args:
            current_price: 현재가
        
        Returns:
            손익률 (%) 또는 None
        """
        position_info = self.state.get_position_info()
        entry_price = position_info.get("entry_price")
        
        if not entry_price:
            return None
        
        pnl_pct = (current_price - entry_price) / entry_price * 100
        
        return pnl_pct
    
    def increment_holding_days(self) -> None:
        """보유 영업일 증가 (WEEKLY 전용)"""
        position_state = self.state.get_position_state()
        
        if position_state == "WEEKLY":
            self.state.increment_weekly_days_held()
            logger.info(f"보유일 증가: {self.state.get_weekly_days_held()}일")
