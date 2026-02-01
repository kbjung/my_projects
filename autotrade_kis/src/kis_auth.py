"""
kis_auth.py

한국투자증권 API 인증 및 토큰 관리 모듈
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict
from dotenv import load_dotenv

from logger_config import get_logger

logger = get_logger("auth")

# 환경 변수 로드
load_dotenv()


class KISAuth:
    """
    한국투자증권 API 인증 관리
    
    기능:
    - OAuth 토큰 발급 및 갱신
    - 토큰 만료 관리
    - Mock 모드 지원
    """
    
    def __init__(self, mock_mode: bool = None):
        """
        Args:
            mock_mode: Mock 모드 사용 여부 (None이면 환경변수에서 읽음)
        """
        self.app_key = os.getenv("KIS_APP_KEY", "")
        self.app_secret = os.getenv("KIS_APP_SECRET", "")
        self.base_url = os.getenv("KIS_BASE_URL", "https://openapi.koreainvestment.com:9443")
        
        if mock_mode is None:
            env_mock = os.getenv("KIS_MOCK_MODE")
            env_kis = os.getenv("KIS_ENV")

            if env_mock is not None:
                self.mock_mode = env_mock.strip().lower() == "true"
            elif env_kis is not None:
                self.mock_mode = env_kis.strip().lower() == "paper"
            else:
                self.mock_mode = True
        else:
            self.mock_mode = mock_mode
        
        # URL 설정
        if self.mock_mode:
            # Mock(VTS) 서버
            self.base_url = "https://openapivts.koreainvestment.com:29443"
            logger.info(f"Mock 모드: VTS 서버 사용 ({self.base_url})")
        else:
            # 실전 서버
            self.base_url = os.getenv("KIS_BASE_URL", "https://openapi.koreainvestment.com:9443")
            logger.info(f"실전 모드: 실거래 서버 사용 ({self.base_url})")
        
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
    
    def get_token(self) -> str:
        """
        액세스 토큰 반환 (필요시 자동 갱신)
        
        Returns:
            액세스 토큰
        """
        # (기존의 fake token 로직 제거하고 실제 발급 로직 수행)
        
        # 토큰이 없거나 만료되었으면 새로 발급
        if not self.access_token or self._is_token_expired():
            self._issue_token()
        
        return self.access_token

    def refresh_token(self) -> str:
        """토큰 강제 갱신"""
        self._issue_token()
        return self.access_token
    
    def _is_token_expired(self) -> bool:
        """토큰 만료 여부 확인"""
        if not self.token_expires_at:
            return True
        
        # 만료 5분 전부터 갱신
        return datetime.now() >= self.token_expires_at - timedelta(minutes=5)
    
    def _issue_token(self) -> None:
        """토큰 발급"""
        url = f"{self.base_url}/oauth2/tokenP"
        
        headers = {
            "content-type": "application/json"
        }
        
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, json=body, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data["access_token"]
            
            # 토큰 유효기간 (보통 24시간)
            expires_in = data.get("expires_in", 86400)  # 기본 24시간
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            logger.info(f"토큰 발급 성공 (만료: {self.token_expires_at})")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"토큰 발급 실패: {e}")
            raise
        except KeyError as e:
            logger.error(f"토큰 응답 파싱 실패: {e}")
            raise
    
    def get_headers(self, tr_id: str = "") -> Dict[str, str]:
        """
        API 요청용 헤더 생성
        
        Args:
            tr_id: 거래 ID (API별로 다름)
        
        Returns:
            헤더 딕셔너리
        """
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.get_token()}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }
        
        if tr_id:
            headers["tr_id"] = tr_id
        
        return headers
    
    def test_connection(self) -> bool:
        """
        API 연결 테스트
        
        Returns:
            연결 성공 여부
        """
        if self.mock_mode:
            logger.info("Mock 모드: 연결 테스트 성공")
            return True
        
        try:
            token = self.get_token()
            if token:
                logger.info("API 연결 테스트 성공")
                return True
            else:
                logger.error("API 연결 테스트 실패: 토큰 없음")
                return False
        except Exception as e:
            logger.error(f"API 연결 테스트 실패: {e}")
            return False


# 싱글톤 인스턴스
_auth_instance: Optional[KISAuth] = None


def get_auth(mock_mode: bool = None) -> KISAuth:
    """
    인증 인스턴스 반환 (싱글톤)
    
    Args:
        mock_mode: Mock 모드 사용 여부
    
    Returns:
        KISAuth 인스턴스
    """
    global _auth_instance
    
    if _auth_instance is None:
        _auth_instance = KISAuth(mock_mode=mock_mode)
    
    return _auth_instance
