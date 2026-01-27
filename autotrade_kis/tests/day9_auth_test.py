"""
day9_auth_test.py

Day 9 - 실전 모의투자(VTS) 인증 및 잔고 조회 테스트
- 실제 API 서버와 통신하여 인증 토큰 발급 확인
- 계좌 잔고 조회하여 5억 원(초기 자금) 확인
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# src 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kis_auth import get_auth
from kis_orders import KISOrders
from logger_config import main_logger as logger

def run_day9_test():
    load_dotenv()
    
    logger.info("=" * 60)
    logger.info("Day 9: 실전 모의투자 연동 테스트")
    logger.info("=" * 60)
    
    # 1. 환경변수 확인
    mock_mode = os.getenv("KIS_MOCK_MODE", "false").lower() == "true"
    logger.info(f"설정된 Mock 모드: {mock_mode}")
    
    account_no = os.getenv("KIS_ACCOUNT_NO", os.getenv("KIS_ACCOUNT", ""))
    logger.info(f"설정된 계좌번호: {account_no}")
    
    if not mock_mode:
        logger.warning("주의: 현재 실전(Live) 모드 설정일 수 있습니다. (KIS_MOCK_MODE=True 권장)")

    # 2. 컴포넌트 초기화
    logger.info("\n[1/3] 컴포넌트 초기화 및 토큰 발급...")
    try:
        auth = get_auth()
        token = auth.get_token()
        logger.info(f"토큰 발급 성공: {token[:10]}... (길이: {len(token)})")
        logger.info(f"접속 서버: {auth.base_url}")
    except Exception as e:
        logger.error(f"토큰 발급 실패: {e}")
        return

    # 3. 잔고 조회 테스트
    logger.info("\n[2/3] 계좌 잔고 조회...")
    orders = KISOrders()
    balance = orders.get_balance()
    
    if balance:
        logger.info(f"✓ 잔고 조회 성공")
        logger.info(f" - 예수금: {balance['cash']:,.0f}원")
        logger.info(f" - 총평가: {balance['total_asset']:,.0f}원")
        
        # 4. 포지션 정보
        logger.info("\n[3/3] 보유 종목 확인...")
        logger.info(f" - 종목 수: {len(balance['positions'])}")
        for pos in balance['positions']:
            logger.info(f"   * {pos['symbol']}: {pos['quantity']}주 ({pos['profit_loss']:,.0f}원)")
            
    else:
        logger.error("✗ 잔고 조회 실패 (로그 확인 필요)")

    logger.info("\n" + "=" * 60)
    logger.info("Day 9 테스트 종료")
    logger.info("=" * 60)

if __name__ == "__main__":
    run_day9_test()
