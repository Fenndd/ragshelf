"""Turn plain Markdown/text (the parse cache's passthrough bundles) into content items.

The items use the same shape as MinerU's content list so that one builder
handles both. A text input has one logical page, `page_idx` 0.

Recognized: ATX and Setext headings, fenced code, display math, pipe tables,
lists, block quotes (as paragraphs), captions, and YAML front matter (skipped).
Not recognized: indented code blocks (they read as paragraphs) and nested
lists (flattened into one list).
"""

import re
from typing import Any

_ATX = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_LIST_ITEM = re.compile(r"^(\s*)([-*+•]|\d{1,3}[.)])[ \t]+(.*)$")
_TABLE_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_IMAGE_ONLY = re.compile(r"^\s*!\[[^\]]*\]\([^)]*\)\s*$")
_RULE = re.compile(r"^ {0,3}([-*_])( ?\1){2,}\s*$")
_SETEXT = re.compile(r"^ {0,3}(?:(={2,})|(-{2,}))[ \t]*$")
_FRONT_MATTER_KEY = re.compile(r"^[\w.-]+[ \t]*:")
_CAPTION = re.compile(
    r"^(?:figure|fig\.|table|tab\.|chart|рис\.|рисунок|таблица|obr\.|obrazok|obrázok|tabuľka|tabulka|"
    r"abbildung|abb\.|tabelle|figura|tabla)\s*\d+[.:)]",
    re.IGNORECASE,
)


def _front_matter_end(lines: list[str]) -> int:
    """Index of the first line after a YAML front matter block at the very top, else 0."""
    if not lines or lines[0].strip() != "---":
        return 0
    for end in range(1, len(lines)):
        if lines[end].strip() in {"---", "..."}:
            inside = [line for line in lines[1:end] if line.strip()]
            return end + 1 if inside and _FRONT_MATTER_KEY.match(inside[0]) else 0
    return 0


def markdown_items(text: str) -> list[dict[str, Any]]:
    lines = text.removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    items: list[dict[str, Any]] = []
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            joined = "\n".join(paragraph)
            kind = "caption" if len(joined) <= 300 and _CAPTION.match(joined) else "text"
            items.append({"type": kind, "text": joined, "page_idx": 0})
            paragraph.clear()

    i = _front_matter_end(lines)
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            flush()
            i += 1
            continue
        if fence := _FENCE.match(line):
            flush()
            marker, body = fence[1], []
            i += 1
            while i < len(lines) and not (lines[i].strip().startswith(marker[0] * len(marker))
                                          and not lines[i].strip().strip(marker[0])):
                body.append(lines[i])
                i += 1
            i += 1  # closing fence; an unclosed fence runs to the end
            items.append({"type": "code", "sub_type": "code", "code_body": "\n".join(body), "page_idx": 0})
            continue
        if heading := _ATX.match(line):
            flush()
            items.append({"type": "text", "text": heading[2], "text_level": len(heading[1]), "page_idx": 0})
            i += 1
            continue
        if line.strip() == "$$" or (line.strip().startswith("$$") and line.strip().endswith("$$") and len(line.strip()) > 4):
            flush()
            stripped = line.strip()
            if stripped != "$$":
                body = [stripped[2:-2]]
                i += 1
            else:
                body, i = [], i + 1
                while i < len(lines) and lines[i].strip() != "$$":
                    body.append(lines[i])
                    i += 1
                i += 1
            items.append({"type": "equation", "text": "\n".join(body).strip(), "text_format": "latex", "page_idx": 0})
            continue
        if ("|" in line and i + 1 < len(lines) and "|" in lines[i + 1]
                and _TABLE_SEPARATOR.match(lines[i + 1])):
            flush()
            body = []
            while i < len(lines) and lines[i].strip() and "|" in lines[i]:
                body.append(lines[i].rstrip())
                i += 1
            items.append({"type": "table", "table_body": "\n".join(body), "page_idx": 0})
            continue
        if paragraph and (setext := _SETEXT.match(line)):
            heading_text = " ".join(paragraph)
            paragraph.clear()
            items.append({"type": "text", "text": heading_text, "text_level": 1 if setext[1] else 2, "page_idx": 0})
            i += 1
            continue
        if _IMAGE_ONLY.match(line) or _RULE.match(line):
            flush()
            i += 1
            continue
        entry = _LIST_ITEM.match(line)
        # Only "1." (or a bullet) may interrupt a paragraph: a wrapped line that starts with a number
        # ("... enrolled in\n12. patients") is still the paragraph.
        if entry and paragraph and entry[2][0].isdigit() and int(entry[2][:-1]) != 1:
            entry = None
        if entry:
            flush()
            ordered = entry[2][0].isdigit()  # switching between bullets and numbers starts a new list
            # Ordered markers are bibliographic evidence for ambiguous reference headings
            # and for the body-leakage counter; bullets carry no such evidence.
            entries = [f"{entry[2]} {entry[3].strip()}" if ordered else entry[3].strip()]
            i += 1
            while i < len(lines) and lines[i].strip():
                nxt = lines[i]
                if match := _LIST_ITEM.match(nxt):
                    if match[2][0].isdigit() != ordered:
                        break
                    entries.append(f"{match[2]} {match[3].strip()}" if ordered else match[3].strip())
                elif nxt.startswith((" ", "\t")):
                    entries[-1] += "\n" + nxt.strip()  # wrapped continuation
                else:
                    break
                i += 1
            items.append({"type": "list", "sub_type": "text", "list_items": entries, "page_idx": 0})
            continue
        if line.lstrip().startswith(">"):
            line = line.lstrip()[1:].lstrip()
        paragraph.append(line.strip())
        i += 1
    flush()
    return items
