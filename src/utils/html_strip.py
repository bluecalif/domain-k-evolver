"""HTML → plain text 변환.

FETCH body(raw HTML)에서 노이즈(script, style, nav 등)를 제거하고
본문 텍스트만 추출. LLM claim 파싱 품질 개선용 (D-120).
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

_NOISE_TAGS = ["script", "style", "nav", "header", "footer", "aside", "noscript"]


def html_to_text(html: str) -> str:
    """HTML 문자열에서 본문 텍스트 추출.

    1. script/style/nav 등 노이즈 태그 제거
    2. <main> 또는 <article> 우선 추출, 없으면 전체 body
    3. 연속 공백/빈줄 정리
    """
    if not html or not html.strip():
        return ""

    soup = BeautifulSoup(html, "html.parser")

    # 노이즈 태그 제거
    for tag in soup(_NOISE_TAGS):
        tag.decompose()

    # 본문 우선 추출: <main> → <article> → 전체
    main = soup.find("main") or soup.find("article") or soup

    text = main.get_text(separator="\n", strip=True)

    # 연속 빈줄 정리 (3줄 이상 → 2줄)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text
