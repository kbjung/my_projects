"""
main.py

메인 봇 오케스트레이터
"""

import sys
import time
import signal
from pathlib import Path
from datetime import datetime, time as dt_time
import pandas as pd

# src 디렉토리를 경로에 추가
# src 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent / "src"))

from state_manager import StateManager
from kis_auth import get_auth
from kis_marketdata import KISMarketData
from kis_orders import KISOrders
from order_sync import OrderSynchronizer
from position_manager import PositionManager
from risk_controller import RiskController
from strategy_daily import DailyStrategy
from strategy_weekly import WeeklyStrategy
from weekly_mode_switcher import WeeklyModeSwitcher
from trade_recorder import TradeRecorder
from logger_config import main_logger as logger
from utils import pad_left, pad_right, pad_center
from strategy_config import CONFIG


class TradingBot:
    """
    자동매매 봇 메인 클래스
    """
    
    def __init__(self, mock_mode: bool = True):
        """
        Args:
            mock_mode: Mock 모드 사용 여부
        """
        self.mock_mode = mock_mode
        self.running = False
        
        # 컴포넌트 초기화
        logger.info("봇 초기화 시작...")
        
        self.state = StateManager(state_file="tests/output/state.json")
        self.auth = get_auth(mock_mode=mock_mode)
        self.marketdata = KISMarketData(mock_mode=mock_mode)
        self.orders = KISOrders(mock_mode=mock_mode)
        self.order_sync = OrderSynchronizer(self.orders)
        
        self.position_mgr = PositionManager(self.state)
        self.risk_ctrl = RiskController(self.state)
        self.recorder = TradeRecorder()  # 거래 기록기
        
        self.daily_strategy = DailyStrategy()
        self.weekly_strategy = WeeklyStrategy(mode=self.state.get_weekly_mode())
        self.mode_switcher = WeeklyModeSwitcher()
        
        # 테스트 종목 (실제로는 설정에서 로드)
        self.symbol = "005930"  # 삼성전자
        
        self.daily_report_done_date = None
        
        logger.info("봇 초기화 완료")
        
    def _get_symbol_name(self, code: str) -> str:
        """종목명 조회 (MVP: 주요 종목 하드코딩)"""
        if code == "005930":
            return "삼성전자"
        return code

    def _format_currency_kr(self, amount: float) -> str:
        """금액 포맷팅 (예: 100,000,000원(1억 원))"""
        if amount is None:
            return "0원"
            
        base_str = f"{int(amount):,}원"
        
        if amount >= 100_000_000:
            ok_unit = amount / 100_000_000
            return f"{base_str}({ok_unit:.1f}억 원)"
        elif amount >= 10_000:
            man_unit = amount / 10_000
            return f"{base_str}({man_unit:.0f}만 원)"
        
        return base_str

    def start(self):
        """봇 시작"""
        print("=" * 60)
        print(f"🚀 자동매매 봇 시작 (모드: {'Mock' if self.mock_mode else '실전'})")
        print("=" * 60)
        
        self.running = True
        
        # 시그널 핸들러 등록
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # 시작 시 계좌 요약 출력
        self._print_startup_summary()
        
        # 메인 루프
        try:
            self._main_loop()
        except Exception as e:
            logger.error(f"봇 실행 오류: {e}", exc_info=True)
        finally:
            self.stop()

    def _main_loop(self):
        """메인 루프"""
        loop_interval = 60  # 60초마다 실행
        
        while self.running:
            try:
                current_time = datetime.now()
                
                # 장 시간 체크 (09:00 ~ 15:30)
                if not self._is_market_hours(current_time):
                    # 장 마감 후 리포트 생성 (15:35 이후 한 번만)
                    if current_time.time() >= dt_time(15, 35) and self.daily_report_done_date != current_time.date():
                        self._generate_daily_report(current_time)
                    
                    # 루프 로깅 최소화
                    # logger.debug("장 시간 외: 대기 중...")
                    time.sleep(loop_interval)
                    continue
                
                # 루프 로깅 최소화 (DEBUG 레벨로 변경)
                logger.debug(f"루프 실행: {current_time.strftime('%H:%M:%S')}")
                
                # 일일 초기화 체크
                self._check_daily_reset(current_time)
                
                # 1. 시장 데이터 업데이트
                self._update_market_data()
                
                # 2. 포지션 확인 및 청산 체크
                position_state = self.state.get_position_state()
                
                if position_state != "NONE":
                    self._check_exit_conditions(current_time)
                else:
                    # 3. 진입 조건 체크
                    self._check_entry_conditions(current_time)
                
                # 대기
                time.sleep(loop_interval)
            
            except Exception as e:
                logger.error(f"루프 오류: {e}", exc_info=True)
                time.sleep(loop_interval)
    
    def _print_startup_summary(self):
        """시작 시 계좌 및 대상 종목 정보 출력"""
        # 로그 접두사 없이 깔끔하게 출력하기 위해 print 사용
        print("\n" + "=" * 60)
        print(" [계좌 잔고 및 보유 종목]")
        print("-" * 60)
        
        balance = self.orders.get_balance()
        if balance:
            cash_fmt = self._format_currency_kr(balance['cash'])
            asset_fmt = self._format_currency_kr(balance['total_asset'])
            
            print(f" - 예수금   : {cash_fmt}")
            print(f" - 총평가금 : {asset_fmt}")
            
            if balance['positions']:
                print("\n [현재 보유 종목]")
                
                # 헤더 설정
                # 종목명(16) | 수량(8) | 평단가(12) | 현재가(12) | 평가손익(14) | 수익률(10)
                h_name = pad_right("종목명", 16)
                h_qty = pad_left("수량", 8)
                h_avg = pad_left("평단가", 12)
                h_cur = pad_left("현재가", 12)
                h_pnl = pad_left("평가손익", 14)
                h_pct = pad_left("수익률", 10)
                
                header = f"{h_name} | {h_qty} | {h_avg} | {h_cur} | {h_pnl} | {h_pct}"
                print("-" * 80)
                print(header)
                print("-" * 80)
                
                for p in balance['positions']:
                    s_name = self._get_symbol_name(p['symbol'])
                    name_str = f"{s_name}({p['symbol']})"
                    
                    if p['avg_price'] > 0:
                        pnl_pct = (p['current_price'] - p['avg_price']) / p['avg_price'] * 100
                    else:
                        pnl_pct = 0.0
                    
                    c_name = pad_right(name_str, 16)
                    c_qty = pad_left(f"{p['quantity']:,}주", 8)
                    c_avg = pad_left(f"{p['avg_price']:,.0f}원", 12)
                    c_cur = pad_left(f"{p['current_price']:,.0f}원", 12)
                    c_pnl = pad_left(self._format_currency_kr(p['profit_loss']), 14)
                    c_pct = pad_left(f"{pnl_pct:,.2f}%", 10)
                    
                    line = f"{c_name} | {c_qty} | {c_avg} | {c_cur} | {c_pnl} | {c_pct}"
                    print(line)
                print("-" * 80)
            else:
                print(" - 현재 보유 종목 없음")
        else:
            logger.warning("계좌 정보 조회 실패")
            
        print("\n [거래 대상 설정]")
        s_name = self._get_symbol_name(self.symbol)
        print(f" - 대상 종목: {s_name}({self.symbol})")
        print("=" * 60 + "\n")

    def _generate_daily_report(self, current_time: datetime):
        """장 마감 일일 리포트 생성"""
        # 로그 접두사 없이 깔끔하게 출력하기 위해 print 사용
        print("\n" + "=" * 60)
        print(f" 📢 일일 거래 리포트 ({current_time.strftime('%Y-%m-%d')})")
        print("=" * 60)
        
        # 1. 당일 체결 내역
        trades = self.orders.get_today_trades()
        print(f" [1] 금일 체결 내역 (총 {len(trades)}건)")
        
        if trades:
            total_buy = 0
            total_sell = 0
            
            # 헤더
            # 시간(10) | 구분(6) | 종목(16) | 수량(8) | 체결가(12) | 총액(14)
            h_time = pad_right("시간", 10)
            h_side = pad_center("구분", 6)
            h_name = pad_right("종목", 16)
            h_qty = pad_left("수량", 8)
            h_price = pad_left("체결가", 12)
            h_amt = pad_left("총액", 14)
            
            header = f"{h_time} | {h_side} | {h_name} | {h_qty} | {h_price} | {h_amt}"
            print("-" * 80)
            print(header)
            print("-" * 80)
            
            for t in trades:
                s_name = self._get_symbol_name(t['symbol'])
                side_str = "매수" if t['side'] == 'buy' else "매도"
                
                c_time = pad_right(t['time'][:8], 10)
                c_side = pad_center(side_str, 6)
                c_name = pad_right(f"{s_name}({t['symbol']})", 16)
                c_qty = pad_left(f"{t['qty']:,}주", 8)
                c_price = pad_left(f"{t['price']:,.0f}원", 12)
                c_amt = pad_left(f"{t['total_price']:,.0f}원", 14)
                
                line = f"{c_time} | {c_side} | {c_name} | {c_qty} | {c_price} | {c_amt}"
                print(line)
                
                if t['side'] == 'buy':
                    total_buy += t['total_price']
                else:
                    total_sell += t['total_price']
            
            print("-" * 80)
            print(f"   => 총 매수액: {total_buy:,.0f}원 | 총 매도액: {total_sell:,.0f}원")
        else:
            print(" - 체결 내역 없음")
            
        # API 호출 간격 조절
        time.sleep(0.5)
        
        # 2. 계좌 잔고
        print("\n [2] 최종 계좌 잔고")
        balance = self.orders.get_balance()
        if balance:
            cash_fmt = self._format_currency_kr(balance['cash'])
            asset_fmt = self._format_currency_kr(balance['total_asset'])
            print("-" * 60)
            print(f" - 예수금   : {cash_fmt}")
            print(f" - 총평가금 : {asset_fmt}")
            
            if balance['positions']:
                print("\n [보유 포지션]")
                
                # 헤더
                h_name = pad_right("종목명", 16)
                h_qty = pad_left("수량", 8)
                h_avg = pad_left("평단가", 12)
                h_cur = pad_left("현재가", 12)
                h_pnl = pad_left("평가손익", 14)
                h_pct = pad_left("수익률", 10)
                
                header = f"{h_name} | {h_qty} | {h_avg} | {h_cur} | {h_pnl} | {h_pct}"
                print("-" * 80)
                print(header)
                print("-" * 80)
                
                for p in balance['positions']:
                    s_name = self._get_symbol_name(p['symbol'])
                    name_str = f"{s_name}({p['symbol']})"
                    
                    if p['avg_price'] > 0:
                        pnl_pct = (p['current_price'] - p['avg_price']) / p['avg_price'] * 100
                    else:
                        pnl_pct = 0.0
                    
                    c_name = pad_right(name_str, 16)
                    c_qty = pad_left(f"{p['quantity']:,}주", 8)
                    c_avg = pad_left(f"{p['avg_price']:,.0f}원", 12)
                    c_cur = pad_left(f"{p['current_price']:,.0f}원", 12)
                    c_pnl = pad_left(self._format_currency_kr(p['profit_loss']), 14)
                    c_pct = pad_left(f"{pnl_pct:,.2f}%", 10)
                    
                    line = f"{c_name} | {c_qty} | {c_avg} | {c_cur} | {c_pnl} | {c_pct}"
                    print(line)
                print("-" * 80)
        
        print("=" * 60 + "\n")
        
        self.daily_report_done_date = current_time.date()
    
    def _is_market_hours(self, current_time: datetime) -> bool:
        """장 시간 여부 확인"""
        current_time_only = current_time.time()
        market_open = dt_time(9, 0)
        market_close = dt_time(15, 30)
        
        # 주말 제외
        if current_time.weekday() >= 5:
            return False
        
        return market_open <= current_time_only <= market_close
    
    def _update_market_data(self):
        """시장 데이터 업데이트"""
        logger.debug("시장 데이터 업데이트 중...")
        
        # 현재가 조회 (필수)
        current_price = self.marketdata.get_current_price(self.symbol)
        if current_price:
            logger.debug(f"현재가: {self.symbol} = {current_price}")
        
        # 오프닝 레인지 계산 (DAILY 전략용)
        # 조건: 장 시작 후, 아직 계산 안됨, 포지션 없음
        if not self.daily_strategy.opening_high:
            current_time = datetime.now()
            market_open_time = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
            
            # 장 시작 10분 후부터 계산 시도 (데이터 확보 위해)
            m5_candles = self.marketdata.get_candles(self.symbol, "M5", count=20) # 넉넉히
            if m5_candles is not None and not m5_candles.empty:
                self.daily_strategy.calculate_opening_high(m5_candles, market_open_time)

        # 주간 모드 전환 체크 (하루 1회 또는 주기적)
        # 여기서는 매 업데이트마다 체크하되, 실제로는 D1 갱신 시점에만 해도 됨
        self._check_weekly_mode_switch()

    def _check_weekly_mode_switch(self):
        """주간 모드 전환 체크"""
        # 데이터 준비: 지수 D1 (여기서는 종목 D1으로 대체 가정, 실제론 KOSPI200 등 필요)
        # MVP에서는 단순히 종목 D1 사용
        d1_candles = self.marketdata.get_candles(self.symbol, "D1", count=100)
        
        # TODO: 실제 구현 시 daily_stop_history 관리 필요 (파일 또는 DB)
        daily_stop_history = [] 
        
        if d1_candles is not None:
             mode, score, conditions = self.mode_switcher.select_mode(
                 index_candles_d1=d1_candles,
                 daily_stop_history=daily_stop_history
             )
             
             current_mode = self.state.get_weekly_mode()
             if mode != current_mode:
                 logger.info(f"주간 모드 변경 감지: {current_mode} -> {mode}")
                 self.state.set_weekly_mode(mode)
                 self.weekly_strategy.mode = mode # 전략 객체에도 반영

    def _check_exit_conditions(self, current_time: datetime):
        """청산 조건 확인"""
        position_state = self.state.get_position_state()
        position_info = self.state.get_position_info()
        
        entry_price = position_info["entry_price"]
        symbol = position_info["symbol"]
        
        # 현재가 조회
        current_price = self.marketdata.get_current_price(symbol)
        if not current_price:
            logger.warning("현재가 조회 실패: 청산 체크 스킵")
            return
        
        # 보유일 (WEEKLY용) - DAILY는 0
        days_held = self.state.get_weekly_days_held() if position_state == "WEEKLY" else 0
        
        # 청산 조건 확인 (RiskController 위임)
        should_exit, reason = self.risk_ctrl.check_exit_conditions(
            position_state, entry_price, current_price, current_time, days_held
        )
        
        if should_exit:
            logger.info(f"청산 조건 충족: {reason}")
            self._execute_exit(symbol, current_price, reason)
            
    def _check_entry_conditions(self, current_time: datetime):
        """진입 조건 확인"""
        # 진입 가능 여부 1차 확인 (RiskController)
        can_enter, reason = self.risk_ctrl.validate_entry()
        if not can_enter:
            return
        
        # DAILY 전략 진입 시도
        self._check_daily_entry(current_time)
        
        # WEEKLY 전략 진입 시도 (DAILY가 아니면)
        # 주의: DAILY/WEEKLY 우선순위 정책 필요. 여기서는 둘 다 체크하되, 선진입 우선
        if self.state.get_position_state() == "NONE":
            self._check_weekly_entry(current_time)

    def _check_weekly_entry(self, current_time: datetime):
        """WEEKLY 전략 진입 로직"""
        # 1) 기존 H1 신호가 유효하면 M5 진입 타이밍만 확인
        if self.weekly_strategy.weekly_signal_h1 and self.weekly_strategy.signal_candle_time:
            if self._check_weekly_m5_entry(current_time):
                current_price = self.marketdata.get_current_price(self.symbol)
                if not current_price:
                    return

                mode = self.state.get_weekly_mode()
                logger.info(f"WEEKLY 진입 조건 충족: 모드={mode}, 가격={current_price}")
                self._execute_entry("WEEKLY", self.symbol, current_price, current_time)
            return

        # 2) H1 완성봉 기준 신호 평가
        h1_candles = self.marketdata.get_candles(self.symbol, "H1", count=120)
        if h1_candles is None or h1_candles.empty:
            return

        complete_h1 = self.weekly_strategy.select_complete_h1_candles(h1_candles, current_time)
        if complete_h1 is None or len(complete_h1) < 3:
            return

        is_signal = self.weekly_strategy.evaluate_h1_signal(complete_h1, is_complete_candle=True)
        if not is_signal:
            return

        # 3) M5 진입 타이밍 확인 (윈도우 + 돌파)
        if not self._check_weekly_m5_entry(current_time):
            return

        current_price = self.marketdata.get_current_price(self.symbol)
        if not current_price:
            return

        mode = self.state.get_weekly_mode()
        logger.info(f"WEEKLY 진입 조건 충족: 모드={mode}, 가격={current_price}")
        self._execute_entry("WEEKLY", self.symbol, current_price, current_time)

    def _check_weekly_m5_entry(self, current_time: datetime) -> bool:
        """WEEKLY M5 진입 타이밍 검증"""
        lookback = CONFIG.ENTRY_5M_BREAKOUT_LOOKBACK
        count = max(lookback + 1, 10)
        m5_candles = self.marketdata.get_candles(self.symbol, "M5", count=count)
        if m5_candles is None or m5_candles.empty:
            return False

        return self.weekly_strategy.check_m5_entry_timing(m5_candles, current_time)

    def _check_daily_entry(self, current_time: datetime):
        """DAILY 전략 진입 로직"""
        # 1. 이미 금일 진입했는지 확인
        if self.state.get_daily_entry_taken():
            return
        
        # 2. 오프닝 레인지 기준가 설정 여부 확인
        if not self.daily_strategy.opening_high:
            # 아직 계산 안됨 (장 초반이거나 데이터 부족)
            return

        # 3. 오프닝 레인지 종료 시간 이후인지 확인
        if current_time <= self.daily_strategy.opening_range_end_time:
            return 

        # 4. 현재가 조회
        current_price = self.marketdata.get_current_price(self.symbol)
        if not current_price:
            return
            
        # 5. 돌파 신호 확인
        signal = self.daily_strategy.check_breakout_signal(current_price)
        
        if signal:
            logger.info(f"DAILY 진입 신호 발생: {current_price} > {self.daily_strategy.opening_high}")
            
            # 매수 주문 실행
            self._execute_entry("DAILY", self.symbol, current_price, current_time)

    def _execute_entry(self, position_type: str, symbol: str, price: float, current_time: datetime):
        """진입 주문 실행"""
        s_name = self._get_symbol_name(symbol)
        
        # 수량 계산 (자본금 기준, 슬리피지 고려 안함)
        capital = self.state._state["capital_fixed_krw"]
        quantity = int(capital / price)
        
        if quantity <= 0:
            logger.error(f"주문 수량 부족: 자본={capital}, 가격={price}")
            return

        logger.info(f"⚡ 신규 진입 시도: {s_name}({symbol}) | 전략={position_type} | 수량={quantity}")
        
        # 매수 주문 + 동기화
        result = self.order_sync.execute_buy_with_sync(symbol, quantity)
        
        if result:
            actual_price = result["price"]
            self.position_mgr.enter_position(position_type, symbol, actual_price, current_time)
            
            # CSV 기록
            self.recorder.record_entry(symbol, position_type, actual_price, quantity, current_time)
            
            logger.info(f"✅ 진입 체결 완료: {s_name}({symbol}) @ {actual_price:,.0f}원")
        else:
            logger.error("❌ 진입 주문 실패")
    
    def _execute_exit(self, symbol: str, exit_price: float, reason: str):
        """청산 실행"""
        s_name = self._get_symbol_name(symbol)
        logger.info(f"👋 청산 시도: {s_name}({symbol}) @ {exit_price} | 사유={reason}")
        
        # 포지션 정보 조회 (청산 전 필요)
        position = self.orders.get_position(symbol)
        if not position:
            logger.error("포지션 정보 없음")
            return
        
        quantity = position["quantity"]
        
        # 진입가 조회 (수익률 기록용) - StateManager에서 가져오는 것이 정확 (get_position은 평단가일 수 있음)
        state_pos = self.state.get_position_info()
        entry_price = state_pos["entry_price"] if state_pos["entry_price"] else position["average_price"]
        position_type = self.state.get_position_state()
        
        # 매도 주문 + 동기화
        result = self.order_sync.execute_sell_with_sync(symbol, quantity)
        
        if result:
            # 상태 업데이트
            actual_exit_price = result["price"]
            self.position_mgr.exit_position(actual_exit_price, reason)
            
            # CSV 기록 (청산 시점)
            self.recorder.record_exit(
                symbol, position_type, actual_exit_price, quantity, 
                datetime.now(), reason, entry_price
            )
            
            # 손절 시 플래그 설정
            if reason == "SL":
                self.risk_ctrl.on_stop_loss()
            
            logger.info(f"✅ 청산 체결 완료: {s_name}({symbol}) @ {actual_exit_price:,.0f}원 (사유: {reason})")
        else:
            logger.error("❌ 청산 실패")
    
    def _signal_handler(self, signum, frame):
        """시그널 핸들러 (Ctrl+C 등)"""
        logger.info(f"\n시그널 수신: {signum}, 봇 종료 중...")
        self.running = False

    def _check_daily_reset(self, current_time: datetime):
        """일일 리셋 (09:00)"""
        reset_time = dt_time(9, 0)
        if current_time.time() < reset_time:
            return

        today = current_time.date().isoformat()
        last_reset = self.state.get_last_reset_date()

        if last_reset == today:
            return

        # WEEKLY 보유 중이면 영업일 증가
        if self.state.get_position_state() == "WEEKLY":
            self.position_mgr.increment_holding_days()

        # 일일 플래그 및 전략 상태 리셋
        self.state.reset_daily_flags()
        self.state.set_last_reset_date(current_time.date())
        self.daily_strategy.reset()
        self.weekly_strategy.reset()

        logger.info(f"일일 리셋 완료: {today} @ {reset_time}")
    
    def stop(self):
        """봇 종료"""
        logger.info("봇 종료 중...")
        self.running = False
        logger.info("봇 종료 완료")


def main():
    """메인 함수"""
    # Mock 모드로 시작 (실전 전환 시 False로 변경)
    bot = TradingBot(mock_mode=True)
    bot.start()


if __name__ == "__main__":
    main()
