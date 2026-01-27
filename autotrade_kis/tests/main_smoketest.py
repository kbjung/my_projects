"""
main_smoketest.py

Day 1 스모크 테스트 (주문 금지)
README.md Day 1 체크리스트 구현
"""

import sys
from pathlib import Path

# src 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kis_auth import get_auth
from kis_marketdata import KISMarketData
from logger_config import main_logger as logger


def main():
    """
    스모크 테스트 메인 함수
    
    테스트 항목:
    1. 토큰 발급
    2. 현재가 조회
    3. M5 캔들 조회
    4. D1 캔들 조회
    """
    logger.info("=" * 60)
    logger.info("스모크 테스트 시작")
    logger.info("=" * 60)
    
    # 테스트 종목
    test_symbol = "005930"  # 삼성전자
    
    results = {
        "token": False,
        "current_price": False,
        "m5_candles": False,
        "d1_candles": False
    }
    
    try:
        # 1. 토큰 발급 테스트
        logger.info("\n[1/4] 토큰 발급 테스트...")
        auth = get_auth(mock_mode=True)  # Mock 모드로 테스트
        
        if auth.test_connection():
            logger.info("✓ 토큰 OK")
            results["token"] = True
        else:
            logger.error("✗ 토큰 실패")
        
        # 2. 현재가 조회 테스트
        logger.info("\n[2/4] 현재가 조회 테스트...")
        marketdata = KISMarketData(mock_mode=True)
        
        current_price = marketdata.get_current_price(test_symbol)
        if current_price:
            logger.info(f"✓ 현재가 OK: {test_symbol} = {current_price}")
            results["current_price"] = True
        else:
            logger.error("✗ 현재가 조회 실패")
        
        # 3. M5 캔들 조회 테스트
        logger.info("\n[3/4] M5 캔들 조회 테스트...")
        m5_candles = marketdata.get_candles(test_symbol, "M5", count=50)
        
        if m5_candles is not None and len(m5_candles) > 0:
            logger.info(f"✓ M5 캔들 OK: {len(m5_candles)}개 조회")
            
            # CSV 저장
            output_dir = Path(__file__).parent / "output"
            output_dir.mkdir(exist_ok=True)
            marketdata.save_to_csv(m5_candles, str(output_dir / f"{test_symbol}_M5.csv"))
            results["m5_candles"] = True
        else:
            logger.error("✗ M5 캔들 조회 실패")
        
        # 4. D1 캔들 조회 테스트
        logger.info("\n[4/4] D1 캔들 조회 테스트...")
        d1_candles = marketdata.get_candles(test_symbol, "D1", count=100)
        
        if d1_candles is not None and len(d1_candles) > 0:
            logger.info(f"✓ D1 캔들 OK: {len(d1_candles)}개 조회")
            
            # CSV 저장
            marketdata.save_to_csv(d1_candles, str(output_dir / f"{test_symbol}_D1.csv"))
            results["d1_candles"] = True
        else:
            logger.error("✗ D1 캔들 조회 실패")
    
    except Exception as e:
        logger.error(f"스모크 테스트 오류: {e}", exc_info=True)
    
    # 결과 요약
    logger.info("\n" + "=" * 60)
    logger.info("스모크 테스트 결과")
    logger.info("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ 성공" if passed else "✗ 실패"
        logger.info(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    logger.info(f"\n총 {passed}/{total} 테스트 통과")
    
    if passed == total:
        logger.info("✓ 모든 테스트 통과!")
        return 0
    else:
        logger.error("✗ 일부 테스트 실패")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
