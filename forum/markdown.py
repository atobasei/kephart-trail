"""Turn a post's Markdown into safe HTML. Runs once when a post is saved, never at read time.

Two layers of protection:
1. The Markdown parser is limited to the forum's subset (bold, italics, links, lists,
   quotes, line breaks, code). Raw HTML, images, and headings are switched off, so typing
   <b> or # shows those characters as text instead of formatting.
2. The result is cleaned by nh3 with a short allow-list of tags, so even a parser bug
   can't let a <script> tag or javascript: link through.
"""

import re

import markdown
import nh3

ALLOWED_TAGS = {
    "p",
    "br",
    "strong",
    "em",
    "a",
    "ul",
    "ol",
    "li",
    "blockquote",
    "code",
    "pre",
}
ALLOWED_ATTRIBUTES = {"a": {"href", "title"}}
ALLOWED_URL_SCHEMES = {"http", "https", "mailto"}

# Parser features outside the subset. Names come from Python-Markdown's registries.
DISABLED_PREPROCESSORS = ["html_block"]
DISABLED_INLINE_PATTERNS = ["html", "image_link", "image_reference", "short_image_ref"]
DISABLED_BLOCK_PROCESSORS = ["hashheader", "setextheader", "hr"]

# Bare web addresses count as links even when Markdown wouldn't make them clickable,
# because that's how most spam arrives.
BARE_LINK_PATTERN = re.compile(r"(https?://|www\.)\S", re.IGNORECASE)


def _build_parser():
    parser = markdown.Markdown(extensions=["nl2br", "sane_lists"])
    for name in DISABLED_PREPROCESSORS:
        parser.preprocessors.deregister(name)
    for name in DISABLED_INLINE_PATTERNS:
        parser.inlinePatterns.deregister(name)
    for name in DISABLED_BLOCK_PROCESSORS:
        parser.parser.blockprocessors.deregister(name)
    return parser


def render_markdown(text):
    parser = _build_parser()
    html = parser.convert(text)
    return nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=ALLOWED_URL_SCHEMES,
        link_rel="nofollow ugc noopener noreferrer",
    )


def contains_link(text):
    """True if the text has a Markdown link, an <autolink>, or a bare web address."""
    if BARE_LINK_PATTERN.search(text):
        return True
    html = render_markdown(text)
    return "<a " in html
