"""
day3_order_test.py

Day 3 — 주문 및 동기화 테스트 (Mock 모드)
- 주문 함수 연동 확인
- 주문 동기화 루틴 확인
- 상태 전이 확인
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# src 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kis_orders import KISOrders
from order_sync import OrderSynchronizer
from state_manager import StateManager
from logger_config import main_logger as logger

def run_day3_test():
    logger.info("=" * 60)
    logger.info("Day 3: 주문 및 동기화 테스트 시작 (Mock)")
    logger.info("=" * 60)
    
    # 컴포넌트 초기화
    # 주의: 테스트용 state 파일을 사용하여 실제 운영 파일에 영향 없도록 함
    # tests/test_state_day3.json 경로 사용
    state_file_path = Path(__file__).parent / "test_state_day3.json"
    state_manager = StateManager(state_file=str(state_file_path))
    
    # 초기 상태 리셋
    state_manager._save(state_manager._load_or_initialize())
    state_manager.close_position(0, "RESET") # 상태 강제 초기화
    
    kis_orders = KISOrders(mock_mode=True)
    order_sync = OrderSynchronizer(kis_orders)
    
    symbol = "005930"  # 삼성전자
    qty = 10
    
    try:
        # 1. 매수 주문 테스트 (동기화 포함)
        logger.info("\n[1/3] 매수 주문 및 동기화 테스트...")
        
        # 진입 가능 여부 확인
        can_enter, reason = state_manager.can_enter_new_position()
        if not can_enter:
            logger.error(f"진입 불가 사유: {reason}")
            return
            
        # 매수 실행
        buy_result = order_sync.execute_buy_with_sync(
            symbol=symbol,
            quantity=qty,
            price=None, # 시장가
            wait_seconds=1 # 테스트 속도를 위해 단축
        )
        
        if buy_result:
            logger.info(f"✓ 매수 성공: {buy_result}")
            
            # 상태 업데이트 (Main 로직 시뮬레이션)
            entry_price = buy_result["price"]
            state_manager.open_position(
                position_type="DAILY", 
                symbol=symbol, 
                entry_price=entry_price, 
                entry_time=datetime.now()
            )
            
            # 상태 검증
            current_state = state_manager.get_position_state()
            if current_state == "DAILY":
                logger.info("✓ 상태 전이 확인: NONE -> DAILY")
            else:
                logger.error(f"✗ 상태 전이 실패: {current_state}")
                
        else:
            logger.error("✗ 매수 실패")
            return

        # 2. 중복 주문 방지 및 포지션 보호 테스트
        logger.info("\n[2/3] 중복 진입 방지 테스트...")
        
        can_enter_again, reason_again = state_manager.can_enter_new_position()
        if not can_enter_again:
            logger.info(f"✓ 중복 진입 차단 확인: {reason_again}")
        else:
            logger.error("✗ 중복 진입 차단 실패 (진입 가능으로 나옴)")

        # 3. 매도 주문 테스트 (동기화 포함)
        logger.info("\n[3/3] 매도 주문 및 동기화 테스트...")
        
        # 매도 실행
        sell_result = order_sync.execute_sell_with_sync(
            symbol=symbol,
            quantity=qty,
            price=None, # 시장가
            wait_seconds=1
        )
        
        if sell_result:
            logger.info(f"✓ 매도 성공: {sell_result}")
            
            # 상태 업데이트 (Main 로직 시뮬레이션)
            exit_price = sell_result["price"]
            state_manager.close_position(exit_price=exit_price, reason="TP")
            
            # 상태 검증
            current_state = state_manager.get_position_state()
            if current_state == "NONE":
                logger.info("✓ 상태 전이 확인: DAILY -> NONE")
            else:
                logger.error(f"✗ 상태 전이 실패: {current_state}")
                
        else:
            logger.error("✗ 매도 실패")

    except Exception as e:
        logger.error(f"Day 3 테스트 중 오류 발생: {e}", exc_info=True)

    logger.info("\n" + "=" * 60)
    logger.info("Day 3 테스트 종료")
    logger.info("=" * 60)

if __name__ == "__main__":
    run_day3_test()
