"""
state_manager.py

거래 상태 관리 모듈
SPEC.md에 정의된 모든 상태 변수를 관리하고 영속화
"""

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal, Dict, Any

from logger_config import get_logger

logger = get_logger("state")

# SPEC.md 정의 타입
PositionState = Literal["NONE", "DAILY", "WEEKLY"]
WeeklyMode = Literal["1W", "2_3W"]


class StateManager:
    """
    거래 상태 관리 클래스
    
    SPEC.md 1. 상태 변수(필수) 구현:
    - capital_fixed_krw, equity_krw
    - position_state, symbol_in_position
    - entry_price, entry_time, entry_date
    - daily_entry_taken, daily_stop_triggered
    - weekly_mode, weekly_position_open, weekly_days_held
    """
    
    def __init__(self, state_file: str = "state.json"):
        self.state_file = Path(state_file)
        self._lock = threading.Lock()
        self._state: Dict[str, Any] = self._load_or_initialize()
    
    def _load_or_initialize(self) -> Dict[str, Any]:
        """상태 파일 로드 또는 초기화"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                logger.info(f"상태 파일 로드 완료: {self.state_file}")
                return state
            except Exception as e:
                logger.error(f"상태 파일 로드 실패: {e}, 초기 상태로 시작")
        
        # 초기 상태 (SPEC.md 기준)
        initial_state = {
            # Capital
            "capital_fixed_krw": 500000,
            "equity_krw": 500000,
            
            # Position
            "position_state": "NONE",
            "symbol_in_position": None,
            "entry_price": None,
            "entry_time": None,
            "entry_date": None,
            
            # Daily strategy
            "daily_entry_taken": False,
            "daily_stop_triggered": False,
            
            # Weekly strategy
            "weekly_mode": "1W",
            "weekly_position_open": False,
            "weekly_days_held": 0,
            
            # Metadata
            "last_updated": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        self._save(initial_state)
        logger.info("초기 상태 생성 완료")
        return initial_state
    
    def _save(self, state: Dict[str, Any]) -> None:
        """상태를 파일에 저장"""
        try:
            state["last_updated"] = datetime.now().isoformat()
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"상태 저장 실패: {e}")
    
    # ========== Getters ==========
    
    def get_position_state(self) -> PositionState:
        """포지션 상태 조회"""
        with self._lock:
            return self._state["position_state"]
    
    def get_daily_entry_taken(self) -> bool:
        """DAILY 당일 진입 여부"""
        with self._lock:
            return self._state["daily_entry_taken"]
    
    def get_daily_stop_triggered(self) -> bool:
        """당일 손절 발생 여부"""
        with self._lock:
            return self._state["daily_stop_triggered"]
    
    def get_weekly_mode(self) -> WeeklyMode:
        """주간 모드 조회"""
        with self._lock:
            return self._state["weekly_mode"]
    
    def get_equity(self) -> float:
        """현재 평가금액"""
        with self._lock:
            return self._state["equity_krw"]
    
    def get_position_info(self) -> Dict[str, Any]:
        """포지션 정보 조회"""
        with self._lock:
            return {
                "position_state": self._state["position_state"],
                "symbol": self._state["symbol_in_position"],
                "entry_price": self._state["entry_price"],
                "entry_time": self._state["entry_time"],
                "entry_date": self._state["entry_date"],
            }
    
    def get_weekly_days_held(self) -> int:
        """주간 포지션 보유 영업일 수"""
        with self._lock:
            return self._state["weekly_days_held"]
    
    def get_all_state(self) -> Dict[str, Any]:
        """전체 상태 조회 (디버깅용)"""
        with self._lock:
            return self._state.copy()
    
    # ========== Setters ==========
    
    def set_position_state(self, state: PositionState) -> None:
        """포지션 상태 설정"""
        with self._lock:
            old_state = self._state["position_state"]
            self._state["position_state"] = state
            self._save(self._state)
            logger.info(f"포지션 상태 변경: {old_state} -> {state}")
    
    def set_daily_entry_taken(self, taken: bool) -> None:
        """DAILY 진입 플래그 설정"""
        with self._lock:
            self._state["daily_entry_taken"] = taken
            self._save(self._state)
            logger.info(f"daily_entry_taken = {taken}")
    
    def set_daily_stop_triggered(self, triggered: bool) -> None:
        """손절 발생 플래그 설정"""
        with self._lock:
            self._state["daily_stop_triggered"] = triggered
            self._save(self._state)
            logger.warning(f"daily_stop_triggered = {triggered}")
    
    def set_weekly_mode(self, mode: WeeklyMode) -> None:
        """주간 모드 설정"""
        with self._lock:
            old_mode = self._state["weekly_mode"]
            self._state["weekly_mode"] = mode
            self._save(self._state)
            logger.info(f"weekly_mode 변경: {old_mode} -> {mode}")
    
    def set_equity(self, equity: float) -> None:
        """평가금액 업데이트"""
        with self._lock:
            self._state["equity_krw"] = equity
            self._save(self._state)
    
    def increment_weekly_days_held(self) -> None:
        """주간 포지션 보유일 증가 (영업일 기준)"""
        with self._lock:
            self._state["weekly_days_held"] += 1
            self._save(self._state)
            logger.info(f"weekly_days_held = {self._state['weekly_days_held']}")
    
    # ========== Position Management ==========
    
    def open_position(
        self,
        position_type: Literal["DAILY", "WEEKLY"],
        symbol: str,
        entry_price: float,
        entry_time: datetime
    ) -> None:
        """
        포지션 진입
        
        Args:
            position_type: DAILY 또는 WEEKLY
            symbol: 종목 코드
            entry_price: 진입가
            entry_time: 진입 시각
        """
        with self._lock:
            self._state["position_state"] = position_type
            self._state["symbol_in_position"] = symbol
            self._state["entry_price"] = entry_price
            self._state["entry_time"] = entry_time.isoformat()
            self._state["entry_date"] = entry_time.date().isoformat()
            
            if position_type == "DAILY":
                self._state["daily_entry_taken"] = True
            elif position_type == "WEEKLY":
                self._state["weekly_position_open"] = True
                self._state["weekly_days_held"] = 0
            
            self._save(self._state)
            logger.info(
                f"포지션 진입: {position_type} | {symbol} | "
                f"진입가={entry_price} | 시각={entry_time}"
            )
    
    def close_position(self, exit_price: float, reason: str) -> None:
        """
        포지션 청산
        
        Args:
            exit_price: 청산가
            reason: 청산 사유 (TP/SL/EOD/TIME/EARLY_EXIT)
        """
        with self._lock:
            position_type = self._state["position_state"]
            symbol = self._state["symbol_in_position"]
            entry_price = self._state["entry_price"]
            
            if entry_price:
                pnl_pct = (exit_price - entry_price) / entry_price * 100
            else:
                pnl_pct = 0.0
            
            # 손절 여부 확인
            if reason == "SL":
                self._state["daily_stop_triggered"] = True
            
            # 상태 초기화
            self._state["position_state"] = "NONE"
            self._state["symbol_in_position"] = None
            self._state["entry_price"] = None
            self._state["entry_time"] = None
            self._state["entry_date"] = None
            
            if position_type == "WEEKLY":
                self._state["weekly_position_open"] = False
                self._state["weekly_days_held"] = 0
            
            self._save(self._state)
            logger.info(
                f"포지션 청산: {position_type} | {symbol} | "
                f"청산가={exit_price} | 수익률={pnl_pct:.2f}% | 사유={reason}"
            )
    
    # ========== Daily Reset ==========
    
    def reset_daily_flags(self) -> None:
        """일일 플래그 초기화 (장 시작 시 호출)"""
        with self._lock:
            self._state["daily_entry_taken"] = False
            self._state["daily_stop_triggered"] = False
            self._save(self._state)
            logger.info("일일 플래그 초기화 완료")
    
    # ========== Validation ==========
    
    def can_enter_new_position(self) -> tuple[bool, str]:
        """
        신규 진입 가능 여부 확인
        
        Returns:
            (가능 여부, 사유)
        """
        with self._lock:
            # A-2: 1포지션 정책
            if self._state["position_state"] != "NONE":
                return False, f"이미 포지션 보유 중: {self._state['position_state']}"
            
            # A-1: 손절 후 당일 정지
            if self._state["daily_stop_triggered"]:
                return False, "당일 손절 발생으로 신규 진입 차단"
            
            return True, "진입 가능"
