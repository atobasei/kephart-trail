import pytest

from forum.markdown import contains_link, render_markdown


def test_formatting_subset_works():
    html = render_markdown("**bold** and _italics_\nnext line\n\n> quoted\n\n- one\n- two")

    assert "<strong>bold</strong>" in html
    assert "<em>italics</em>" in html
    assert "<br>" in html
    assert "<blockquote>" in html
    assert "<li>one</li>" in html


@pytest.mark.parametrize(
    "hostile",
    [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        '<a href="javascript:alert(1)">x</a>',
        "<iframe src=https://evil.example></iframe>",
        "<div onclick=alert(1)>x</div>",
        "<style>body{display:none}</style>",
    ],
)
def test_raw_html_is_shown_as_text_never_as_tags(hostile):
    html = render_markdown(hostile)

    assert "<script" not in html
    assert "<img" not in html
    assert "<iframe" not in html
    assert "<div" not in html
    assert "<style" not in html
    assert "&lt;" in html


@pytest.mark.parametrize(
    "link",
    [
        "[x](javascript:alert(1))",
        "[x](JaVaScRiPt:alert(1))",
        "[x](  javascript:alert(1))",
        "[x](data:text/html;base64,PHNjcmlwdD4=)",
        "[x](vbscript:msgbox(1))",
    ],
)
def test_dangerous_link_schemes_are_removed(link):
    html = render_markdown(link)

    assert "javascript:" not in html.lower()
    assert "data:" not in html
    assert "vbscript:" not in html
    assert "href" not in html


def test_safe_links_get_nofollow():
    html = render_markdown("[NPS](https://www.nps.gov/grsm/)")

    assert 'href="https://www.nps.gov/grsm/"' in html
    assert 'rel="nofollow ugc noopener noreferrer"' in html


def test_images_and_headings_are_not_rendered():
    html = render_markdown("# Big heading\n\n![pic](https://example.com/a.png)")

    assert "<h1>" not in html
    assert "<img" not in html


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("[NPS](https://nps.gov)", True),
        ("<https://nps.gov>", True),
        ("check https://spam.example now", True),
        ("visit www.spam.example", True),
        ("Alum Cave was icy above the bluffs.", False),
        ("Mile 3.5, then left at the junction.", False),
    ],
)
def test_contains_link(text, expected):
    assert contains_link(text) is expected
