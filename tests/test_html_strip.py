"""html_to_text 단위 테스트 — D-120 HTML→text 변환 검증."""

from __future__ import annotations

from src.utils.html_strip import html_to_text


class TestHtmlToText:
    def test_script_style_removed(self) -> None:
        """script, style 태그 내용이 제거됨."""
        html = """<html><head><style>body{color:red}</style></head>
        <body><script>alert('x')</script><p>Hello world</p></body></html>"""
        text = html_to_text(html)
        assert "alert" not in text
        assert "color:red" not in text
        assert "Hello world" in text

    def test_nav_header_footer_removed(self) -> None:
        """nav, header, footer, aside 태그 제거."""
        html = """<html><body>
        <header>Site Header</header>
        <nav>Menu Item 1</nav>
        <main><p>Main content here</p></main>
        <aside>Sidebar ad</aside>
        <footer>Copyright 2026</footer>
        </body></html>"""
        text = html_to_text(html)
        assert "Main content here" in text
        assert "Site Header" not in text
        assert "Menu Item" not in text
        assert "Sidebar ad" not in text
        assert "Copyright" not in text

    def test_main_tag_prioritized(self) -> None:
        """<main> 태그가 있으면 그 안의 내용만 추출."""
        html = """<html><body>
        <div>Outside noise</div>
        <main><p>Important content</p></main>
        <div>More noise</div>
        </body></html>"""
        text = html_to_text(html)
        assert "Important content" in text
        assert "Outside noise" not in text
        assert "More noise" not in text

    def test_article_tag_fallback(self) -> None:
        """<main> 없으면 <article> 우선."""
        html = """<html><body>
        <div>Noise</div>
        <article><p>Article body</p></article>
        <div>More noise</div>
        </body></html>"""
        text = html_to_text(html)
        assert "Article body" in text
        assert "Noise" not in text

    def test_no_main_no_article_uses_full_body(self) -> None:
        """<main>/<article> 없으면 전체 body에서 추출."""
        html = "<html><body><p>Some content</p><p>More content</p></body></html>"
        text = html_to_text(html)
        assert "Some content" in text
        assert "More content" in text

    def test_empty_input(self) -> None:
        """빈 입력 → 빈 문자열."""
        assert html_to_text("") == ""
        assert html_to_text("   ") == ""

    def test_plain_text_passthrough(self) -> None:
        """HTML 태그 없는 plain text → 그대로 반환."""
        text = html_to_text("Just plain text content")
        assert "Just plain text content" in text

    def test_malformed_html(self) -> None:
        """malformed HTML도 크래시 없이 처리."""
        html = "<p>Unclosed tag <div>Mixed <b>nesting</p></div>"
        text = html_to_text(html)
        assert "Unclosed tag" in text
        assert "nesting" in text

    def test_multiple_blank_lines_collapsed(self) -> None:
        """연속 빈줄이 2줄로 정리됨."""
        html = "<p>Line 1</p><br><br><br><br><br><p>Line 2</p>"
        text = html_to_text(html)
        # 3줄 이상 연속 빈줄이 없어야 함
        assert "\n\n\n" not in text

    def test_noscript_removed(self) -> None:
        """noscript 태그 제거."""
        html = "<body><noscript>Enable JS</noscript><p>Real content</p></body>"
        text = html_to_text(html)
        assert "Enable JS" not in text
        assert "Real content" in text

    def test_realistic_html_extracts_content(self) -> None:
        """실제 웹페이지와 유사한 구조에서 본문 추출."""
        html = """<!DOCTYPE html>
        <html><head>
            <title>JR Pass Prices</title>
            <style>.nav{display:flex}</style>
            <script>window.ga=function(){}</script>
        </head>
        <body>
            <header><nav><a href="/">Home</a><a href="/about">About</a></nav></header>
            <main>
                <h1>JR Pass Pricing 2026</h1>
                <p>The 7-day JR Pass costs 50,000 yen for adults.</p>
                <p>Children aged 6-11 pay half price: 25,000 yen.</p>
            </main>
            <footer><p>Contact us at info@jrpass.com</p></footer>
        </body></html>"""
        text = html_to_text(html)
        assert "50,000 yen" in text
        assert "25,000 yen" in text
        assert "JR Pass Pricing 2026" in text
        assert "window.ga" not in text
        assert "Home" not in text
        assert "Contact us" not in text
