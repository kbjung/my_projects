"""
logger_config.py

중앙 집중식 로깅 설정 모듈
- 컴포넌트별 로그 파일 분리
- 자동 로그 로테이션
- 민감 데이터 필터링 (API 키, 토큰)
- 구조화된 로그 형식
"""

import logging
import logging.handlers
import os
import re
from pathlib import Path
from typing import Optional


class SensitiveDataFilter(logging.Filter):
    """민감한 데이터를 로그에서 필터링하는 필터"""
    
    SENSITIVE_PATTERNS = [
        (re.compile(r'(appkey|app_key|AppKey)["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)', re.IGNORECASE), r'\1=***FILTERED***'),
        (re.compile(r'(appsecret|app_secret|AppSecret)["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)', re.IGNORECASE), r'\1=***FILTERED***'),
        (re.compile(r'(token|access_token|AccessToken)["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)', re.IGNORECASE), r'\1=***FILTERED***'),
        (re.compile(r'(authorization:\s*bearer\s+)([^\s]+)', re.IGNORECASE), r'\1***FILTERED***'),
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """로그 레코드에서 민감한 데이터를 마스킹"""
        if hasattr(record, 'msg'):
            msg = str(record.msg)
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                msg = pattern.sub(replacement, msg)
            record.msg = msg
        
        if hasattr(record, 'args') and record.args:
            filtered_args = []
            for arg in record.args:
                arg_str = str(arg)
                for pattern, replacement in self.SENSITIVE_PATTERNS:
                    arg_str = pattern.sub(replacement, arg_str)
                filtered_args.append(arg_str)
            record.args = tuple(filtered_args)
        
        return True


class ConsoleEventFilter(logging.Filter):
    """콘솔에는 이벤트/경고/에러만 출력"""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno >= logging.WARNING:
            return True
        msg = record.getMessage()
        return "[EVENT]" in msg


def setup_logger(
    name: str,
    log_dir: str = "logs",
    level: int = logging.INFO,
    console_output: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    로거 설정 및 반환
    
    Args:
        name: 로거 이름 (파일명으로도 사용)
        log_dir: 로그 디렉토리 경로
        level: 로그 레벨
        console_output: 콘솔 출력 여부
        max_bytes: 로그 파일 최대 크기
        backup_count: 백업 파일 개수
    
    Returns:
        설정된 로거 객체
    """
    # 로그 디렉토리 생성
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 기존 핸들러 제거 (중복 방지)
    logger.handlers.clear()
    
    # 포맷터 생성
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 파일 핸들러 (로테이션)
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / f"{name}.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(SensitiveDataFilter())
    logger.addHandler(file_handler)
    
    # 콘솔 핸들러 포맷터 (간소화)
    console_formatter = logging.Formatter(
        fmt='%(asctime)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 콘솔 핸들러
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(SensitiveDataFilter())
        console_handler.addFilter(ConsoleEventFilter())
        logger.addHandler(console_handler)
    
    # 에러 전용 파일 핸들러
    error_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / "errors.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    error_handler.addFilter(SensitiveDataFilter())
    logger.addHandler(error_handler)
    
    return logger


# 기본 로거들 생성
main_logger = setup_logger("main")
strategy_logger = setup_logger("strategy")
orders_logger = setup_logger("orders")
marketdata_logger = setup_logger("marketdata")


def get_logger(name: str) -> logging.Logger:
    """
    이름으로 로거 가져오기
    
    Args:
        name: 로거 이름
    
    Returns:
        로거 객체
    """
    return logging.getLogger(name)
