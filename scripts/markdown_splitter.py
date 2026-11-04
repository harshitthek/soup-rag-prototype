r"""Markdown heading-aware splitter vendored from Soup data pipeline.

Splits a markdown document on ATX headings (^#{1,6}\s) and emits one
record per section. Preamble before the first heading is emitted as a
record with section=None / level=None.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

_MD_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_MAX_MD_SECTIONS = 10_000


def split_markdown_by_headings(text: str) -> list[dict[str, Any]]:
    """Split markdown text on ATX headings into section records.

    Each output record has three keys:
      - 'section': heading text (str) or None for preamble
      - 'level': 1-6 (int) or None for preamble
      - 'text': body content following the heading (str)
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    lines = text.splitlines()
    sections: list[dict[str, Any]] = []
    current_section: str | None = None
    current_level: int | None = None
    body: list[str] = []

    def _flush() -> None:
        if current_section is None and not body:
            return
        sections.append(
            {
                "section": current_section,
                "level": current_level,
                "text": "\n".join(body).strip(),
            }
        )

    for line in lines:
        m = _MD_HEADING_RE.match(line)
        if m:
            _flush()
            if len(sections) >= _MAX_MD_SECTIONS:
                break
            current_section = m.group(2).strip()
            current_level = len(m.group(1))
            body = []
        else:
            body.append(line)
    _flush()
    return sections
