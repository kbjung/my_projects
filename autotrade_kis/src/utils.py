"""
utils.py

유틸리티 함수 모음
"""

import unicodedata

def get_display_width(text: str) -> int:
    """
    문자열의 화면 표시 너비를 계산합니다.
    (한글 등 동아시아 문자는 2, 그 외는 1로 계산)
    """
    width = 0
    for char in text:
        if unicodedata.east_asian_width(char) in ('F', 'W', 'A'):
            width += 2
        else:
            width += 1
    return width

def pad_left(text: str, width: int, fillchar: str = " ") -> str:
    """
    주어진 너비만큼 왼쪽에 패딩을 추가합니다 (우측 정렬).
    화면 표시 너비를 기준으로 계산합니다.
    """
    text_width = get_display_width(text)
    padding = max(0, width - text_width)
    return (fillchar * padding) + text

def pad_right(text: str, width: int, fillchar: str = " ") -> str:
    """
    주어진 너비만큼 오른쪽에 패딩을 추가합니다 (좌측 정렬).
    화면 표시 너비를 기준으로 계산합니다.
    """
    text_width = get_display_width(text)
    padding = max(0, width - text_width)
    return text + (fillchar * padding)

def pad_center(text: str, width: int, fillchar: str = " ") -> str:
    """
    주어진 너비만큼 양쪽에 패딩을 추가합니다 (가운데 정렬).
    """
    text_width = get_display_width(text)
    padding = max(0, width - text_width)
    left_padding = padding // 2
    right_padding = padding - left_padding
    return (fillchar * left_padding) + text + (fillchar * right_padding)
