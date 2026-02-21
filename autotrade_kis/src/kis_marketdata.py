"""
kis_marketdata.py

한국투자증권 API 시장 데이터 조회 모듈
"""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Literal, List, Dict

from kis_auth import get_auth
from logger_config import get_logger

logger = get_logger("marketdata")


class KISMarketData:
    """
    시장 데이터 조회 클래스
    
    기능:
    - 현재가 조회
    - 캔들 데이터 조회 (M5, H1, D1, W1)
    - 데이터 캐싱
    - CSV 내보내기
    - Mock 데이터 생성
    """
    
    def __init__(self, mock_mode: bool = None):
        """
        Args:
            mock_mode: Mock 모드 사용 여부
        """
        self.auth = get_auth(mock_mode=mock_mode)
        self.mock_mode = self.auth.mock_mode
        self.base_url = self.auth.base_url
        
        # 캐시 (데이터, 저장 시각)
        self._cache: Dict[str, Dict[str, object]] = {}

        # 타임프레임별 캐시 TTL (초)
        self._cache_ttl_seconds = {
            "M5": 30,
            "H1": 120,
            "D1": 900,
            "W1": 1800
        }
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        현재가 조회
        
        Args:
            symbol: 종목 코드 (예: "005930")
        
        Returns:
            현재가 (실패 시 None)
        """
        if self.mock_mode:
            # Mock 데이터: 임의의 가격
            mock_price = 50000 + (hash(symbol) % 10000)
            logger.info(f"Mock 현재가 조회: {symbol} = {mock_price}")
            return float(mock_price)
        
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            
            headers = self.auth.get_headers(tr_id="FHKST01010100")
            
            params = {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": symbol
            }
            
            response = self._request("GET", url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("rt_cd") == "0":
                price = float(data["output"]["stck_prpr"])
                logger.info(f"현재가 조회 성공: {symbol} = {price}")
                return price
            else:
                logger.error(f"현재가 조회 실패: {data.get('msg1', 'Unknown error')}")
                return None
        
        except Exception as e:
            logger.error(f"현재가 조회 오류: {e}")
            return None
    
    def get_candles(
        self,
        symbol: str,
        timeframe: Literal["M5", "H1", "D1", "W1"],
        count: int = 100
    ) -> Optional[pd.DataFrame]:
        """
        캔들 데이터 조회
        
        Args:
            symbol: 종목 코드
            timeframe: 타임프레임 (M5=5분, H1=60분, D1=일봉, W1=주봉)
            count: 조회할 캔들 개수
        
        Returns:
            DataFrame (컬럼: datetime, open, high, low, close, volume)
        """
        cache_key = f"{symbol}_{timeframe}_{count}"
        
        # 캐시 확인 (TTL 이내)
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            cached_at = cached.get("cached_at")
            ttl = self._cache_ttl_seconds.get(timeframe, 60)
            if cached_at and (datetime.now() - cached_at).total_seconds() <= ttl:
                logger.debug(f"캐시에서 캔들 데이터 반환: {cache_key}")
                return cached.get("data")
        
        if self.mock_mode:
            df = self._generate_mock_candles(symbol, timeframe, count)
            self._cache[cache_key] = {"data": df, "cached_at": datetime.now()}
            return df
        
        try:
            # 실제 API 호출 (타임프레임별 엔드포인트 다름)
            if timeframe in ["M5", "H1"]:
                df = self._get_intraday_candles(symbol, timeframe, count)
            elif timeframe == "D1":
                df = self._get_daily_candles(symbol, count)
            elif timeframe == "W1":
                df = self._get_weekly_candles(symbol, count)
            else:
                logger.error(f"지원하지 않는 타임프레임: {timeframe}")
                return None
            
            self._cache[cache_key] = {"data": df, "cached_at": datetime.now()}
            return df
        
        except Exception as e:
            logger.error(f"캔들 데이터 조회 오류: {e}")
            return None
    
    def _get_intraday_candles(
        self,
        symbol: str,
        timeframe: Literal["M5", "H1"],
        count: int
    ) -> pd.DataFrame:
        """분봉/시간봉 조회 (실제 API)"""
        # 타임프레임 코드 매핑
        tf_code = "5" if timeframe == "M5" else "60"
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"
        
        headers = self.auth.get_headers(tr_id="FHKST03010200")
        
        params = {
            "FID_ETC_CLS_CODE": "",
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol,
            "FID_INPUT_HOUR_1": tf_code,
            "FID_PW_DATA_INCU_YN": "Y"
        }
        
        response = self._request("GET", url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("rt_cd") != "0":
            raise ValueError(f"API 오류: {data.get('msg1', 'Unknown error')}")
        
        # 데이터 파싱
        output = data.get("output2", [])
        
        df = pd.DataFrame(output)
        df = df.rename(columns={
            "stck_bsop_date": "date",
            "stck_cntg_hour": "time",
            "stck_oprc": "open",
            "stck_hgpr": "high",
            "stck_lwpr": "low",
            "stck_prpr": "close",
            "cntg_vol": "volume"
        })
        
        # 타입 변환
        df["datetime"] = pd.to_datetime(df["date"] + df["time"], format="%Y%m%d%H%M%S")
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(int)
        
        df = df[["datetime", "open", "high", "low", "close", "volume"]]
        df = df.sort_values("datetime").reset_index(drop=True)
        
        # 요청한 개수만큼만 반환
        df = df.tail(count)
        
        logger.info(f"{timeframe} 캔들 조회 성공: {symbol}, {len(df)}개")
        return df
    
    def _get_daily_candles(self, symbol: str, count: int) -> pd.DataFrame:
        """일봉 조회 (실제 API)"""
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        
        headers = self.auth.get_headers(tr_id="FHKST03010100")
        
        # 종료일 (오늘)
        end_date = datetime.now().strftime("%Y%m%d")
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol,
            "FID_INPUT_DATE_1": "",  # 시작일 (비워두면 자동)
            "FID_INPUT_DATE_2": end_date,
            "FID_PERIOD_DIV_CODE": "D",  # D=일봉
            "FID_ORG_ADJ_PRC": "0"  # 0=수정주가
        }
        
        response = self._request("GET", url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("rt_cd") != "0":
            raise ValueError(f"API 오류: {data.get('msg1', 'Unknown error')}")
        
        output = data.get("output2", [])
        
        df = pd.DataFrame(output)
        df = df.rename(columns={
            "stck_bsop_date": "date",
            "stck_oprc": "open",
            "stck_hgpr": "high",
            "stck_lwpr": "low",
            "stck_clpr": "close",
            "acml_vol": "volume"
        })
        
        df["datetime"] = pd.to_datetime(df["date"], format="%Y%m%d")
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(int)
        
        df = df[["datetime", "open", "high", "low", "close", "volume"]]
        df = df.sort_values("datetime").reset_index(drop=True)
        df = df.tail(count)
        
        logger.info(f"D1 캔들 조회 성공: {symbol}, {len(df)}개")
        return df
    
    def _get_weekly_candles(self, symbol: str, count: int) -> pd.DataFrame:
        """주봉 조회 (실제 API)"""
        # 주봉은 일봉 API에서 FID_PERIOD_DIV_CODE="W"로 조회
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        
        headers = self.auth.get_headers(tr_id="FHKST03010100")
        
        end_date = datetime.now().strftime("%Y%m%d")
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol,
            "FID_INPUT_DATE_1": "",
            "FID_INPUT_DATE_2": end_date,
            "FID_PERIOD_DIV_CODE": "W",  # W=주봉
            "FID_ORG_ADJ_PRC": "0"
        }
        
        response = self._request("GET", url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("rt_cd") != "0":
            raise ValueError(f"API 오류: {data.get('msg1', 'Unknown error')}")
        
        output = data.get("output2", [])
        
        df = pd.DataFrame(output)
        df = df.rename(columns={
            "stck_bsop_date": "date",
            "stck_oprc": "open",
            "stck_hgpr": "high",
            "stck_lwpr": "low",
            "stck_clpr": "close",
            "acml_vol": "volume"
        })
        
        df["datetime"] = pd.to_datetime(df["date"], format="%Y%m%d")
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(int)
        
        df = df[["datetime", "open", "high", "low", "close", "volume"]]
        df = df.sort_values("datetime").reset_index(drop=True)
        df = df.tail(count)
        
        logger.info(f"W1 캔들 조회 성공: {symbol}, {len(df)}개")
        return df
    
    def _generate_mock_candles(
        self,
        symbol: str,
        timeframe: str,
        count: int
    ) -> pd.DataFrame:
        """Mock 캔들 데이터 생성"""
        import numpy as np
        
        # 타임프레임별 시간 간격
        intervals = {
            "M5": timedelta(minutes=5),
            "H1": timedelta(hours=1),
            "D1": timedelta(days=1),
            "W1": timedelta(weeks=1)
        }
        
        interval = intervals.get(timeframe, timedelta(days=1))
        
        # 시작 시간
        end_time = datetime.now()
        start_time = end_time - (interval * count)
        
        # 시간 배열 생성
        times = pd.date_range(start=start_time, end=end_time, freq=interval)[:count]
        
        # 가격 데이터 생성 (랜덤 워크)
        base_price = 50000 + (hash(symbol) % 10000)
        np.random.seed(hash(symbol) % 10000)
        
        returns = np.random.randn(count) * 0.02  # 2% 변동성
        prices = base_price * (1 + returns).cumprod()
        
        # OHLC 생성
        data = []
        for i, (time, close) in enumerate(zip(times, prices)):
            volatility = close * 0.01
            high = close + abs(np.random.randn() * volatility)
            low = close - abs(np.random.randn() * volatility)
            open_price = prices[i-1] if i > 0 else close
            
            data.append({
                "datetime": time,
                "open": open_price,
                "high": max(high, close, open_price),
                "low": min(low, close, open_price),
                "close": close,
                "volume": int(np.random.randint(100000, 1000000))
            })
        
        df = pd.DataFrame(data)
        logger.info(f"Mock {timeframe} 캔들 생성: {symbol}, {len(df)}개")
        return df
    
    def save_to_csv(self, df: pd.DataFrame, filename: str, data_dir: str = "data") -> None:
        """
        캔들 데이터를 CSV로 저장
        
        Args:
            df: 캔들 DataFrame
            filename: 파일명
            data_dir: 저장 디렉토리
        """
        data_path = Path(data_dir)
        data_path.mkdir(parents=True, exist_ok=True)
        
        filepath = data_path / filename
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        logger.info(f"CSV 저장 완료: {filepath}")

    def _request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
        timeout: int = 10,
        max_retries: int = 3
    ) -> requests.Response:
        """요청 수행 (네트워크 오류 시 재시도, 토큰 만료 시 1회 재시도)"""
        import time as time_module
        
        last_exception = None
        for attempt in range(max_retries):
            try:
                response = requests.request(method, url, headers=headers, params=params, json=json, timeout=timeout)

                if response.status_code >= 400 and self._is_token_expired_response(response):
                    logger.warning("[EVENT] 토큰 만료 감지: 재발급 후 재시도")
                    self.auth.refresh_token()
                    headers = self.auth.get_headers(tr_id=headers.get("tr_id", ""))
                    response = requests.request(method, url, headers=headers, params=params, json=json, timeout=timeout)

                return response
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                last_exception = e
                wait_time = 2 ** attempt  # 1초, 2초, 4초
                logger.warning(f"[RETRY] 네트워크 오류 ({attempt+1}/{max_retries}): {type(e).__name__}. {wait_time}초 후 재시도...")
                time_module.sleep(wait_time)
        
        # 최대 재시도 초과 시 예외 발생
        raise last_exception

    def _is_token_expired_response(self, response: requests.Response) -> bool:
        """토큰 만료 응답 여부"""
        try:
            data = response.json()
        except Exception:
            return False

        msg_cd = data.get("msg_cd")
        msg1 = data.get("msg1", "")
        return msg_cd == "EGW00123" or "token" in msg1
