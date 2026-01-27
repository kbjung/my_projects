"""
order_sync.py

주문 동기화 및 중복 방지 모듈
SPEC.md 2.3절
"""

import time
from typing import Optional, Dict

from kis_orders import KISOrders
from logger_config import get_logger

logger = get_logger("orders")


class OrderSynchronizer:
    """
    주문 동기화 및 중복 방지
    
    SPEC.md 2.3:
    - 주문 → 미체결 조회 → 체결 확인 → 잔고 확인
    - 주문번호 추적으로 중복 방지
    """
    
    def __init__(self, kis_orders: KISOrders):
        self.orders = kis_orders
        self._processed_orders = set()  # 처리 완료 주문번호
    
    def execute_buy_with_sync(
        self,
        symbol: str,
        quantity: int,
        price: Optional[float] = None,
        max_retries: int = 3,
        wait_seconds: int = 2
    ) -> Optional[Dict]:
        """
        매수 주문 + 동기화
        
        Args:
            symbol: 종목 코드
            quantity: 수량
            price: 지정가 (None이면 시장가)
            max_retries: 최대 재시도 횟수
            wait_seconds: 대기 시간 (초)
        
        Returns:
            체결 정보 (실패 시 None)
        """
        order_type = "limit" if price else "market"
        
        # 주문 발주
        order_no = self.orders.buy(symbol, quantity, price, order_type)
        
        if not order_no:
            logger.error("매수 주문 실패")
            return None
        
        # 중복 체크
        if order_no in self._processed_orders:
            logger.warning(f"중복 주문 감지: {order_no}")
            return None
        
        # 체결 확인 (재시도)
        for attempt in range(max_retries):
            time.sleep(wait_seconds)
            
            order_status = self.orders.get_order_status(order_no)
            
            if order_status and order_status["status"] == "filled":
                logger.info(
                    f"매수 체결 확인: 주문번호={order_no}, "
                    f"수량={order_status['filled_qty']}, "
                    f"가격={order_status['filled_price']}"
                )
                
                # 잔고 확인
                position = self.orders.get_position(symbol)
                if position:
                    logger.info(f"잔고 확인 완료: {position}")
                
                self._processed_orders.add(order_no)
                
                return {
                    "order_no": order_no,
                    "symbol": symbol,
                    "quantity": order_status["filled_qty"],
                    "price": order_status["filled_price"],
                    "position": position
                }
            
            logger.debug(f"체결 대기 중... ({attempt+1}/{max_retries})")
        
        logger.error(f"체결 확인 실패: 주문번호={order_no}")
        return None
    
    def execute_sell_with_sync(
        self,
        symbol: str,
        quantity: int,
        price: Optional[float] = None,
        max_retries: int = 3,
        wait_seconds: int = 2
    ) -> Optional[Dict]:
        """
        매도 주문 + 동기화
        
        Args:
            symbol: 종목 코드
            quantity: 수량
            price: 지정가 (None이면 시장가)
            max_retries: 최대 재시도 횟수
            wait_seconds: 대기 시간 (초)
        
        Returns:
            체결 정보 (실패 시 None)
        """
        order_type = "limit" if price else "market"
        
        # 주문 발주
        order_no = self.orders.sell(symbol, quantity, price, order_type)
        
        if not order_no:
            logger.error("매도 주문 실패")
            return None
        
        # 중복 체크
        if order_no in self._processed_orders:
            logger.warning(f"중복 주문 감지: {order_no}")
            return None
        
        # 체결 확인 (재시도)
        for attempt in range(max_retries):
            time.sleep(wait_seconds)
            
            order_status = self.orders.get_order_status(order_no)
            
            if order_status and order_status["status"] == "filled":
                logger.info(
                    f"매도 체결 확인: 주문번호={order_no}, "
                    f"수량={order_status['filled_qty']}, "
                    f"가격={order_status['filled_price']}"
                )
                
                # 잔고 확인
                balance = self.orders.get_balance()
                if balance:
                    logger.info(f"잔고 확인 완료: 현금={balance['cash']}")
                
                self._processed_orders.add(order_no)
                
                return {
                    "order_no": order_no,
                    "symbol": symbol,
                    "quantity": order_status["filled_qty"],
                    "price": order_status["filled_price"],
                    "balance": balance
                }
            
            logger.debug(f"체결 대기 중... ({attempt+1}/{max_retries})")
        
        logger.error(f"체결 확인 실패: 주문번호={order_no}")
        return None
