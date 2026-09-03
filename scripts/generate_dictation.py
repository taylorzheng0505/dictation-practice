#!/usr/bin/env python3
"""Generate a standalone dictation HTML page from one-item-per-line UTF-8 text."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
LIST_PREFIX_RE = re.compile(r"^\s*(?:[-*•·]|\d+[.)、．]|[A-Za-z][.)])\s+")


def parse_items(raw: str) -> list[str]:
    """Use line breaks as item boundaries and preserve item text otherwise."""
    items: list[str] = []
    for line in raw.splitlines():
        text = line.strip()
        if not text:
            continue
        text = LIST_PREFIX_RE.sub("", text, count=1).strip()
        if text:
            items.append(text)
    return items


def detect_language(text: str) -> str:
    return "zh" if CJK_RE.search(text) else "en"


def infer_title_and_subtitle(items: list[dict[str, str]], requested_title: str | None) -> tuple[str, str, bool]:
    has_en = any(item["lang"] == "en" for item in items)
    has_zh = any(item["lang"] == "zh" for item in items)
    count = len(items)
    if has_en and has_zh:
        default_title = "今日听写"
        subtitle = f"英语 + 语文混合练习 · 共 {count} 条"
    elif has_en:
        default_title = "英语听写"
        subtitle = f"英语听写 · 共 {count} 条"
    else:
        default_title = "语文听写"
        subtitle = f"语文听写 · 共 {count} 条"
    return requested_title or default_title, subtitle, has_en


def render(template: str, items: list[dict[str, str]], title: str, subtitle: str, has_en: bool) -> str:
    items_json = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
    replacements = {
        "__TITLE__": title,
        "__SUBTITLE__": subtitle,
        "__COUNT__": str(len(items)),
        "__ITEMS_JSON__": items_json,
        "__ACCENT_CLASS__": "" if has_en else "hidden-card",
        "__SETTINGS_STEP__": "2" if has_en else "1",
    }
    html = template
    for key, value in replacements.items():
        html = html.replace(key, value)
    leftovers = sorted(set(re.findall(r"__[A-Z0-9_]+__", html)))
    if leftovers:
        raise RuntimeError(f"unresolved template placeholders: {', '.join(leftovers)}")
    return html


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a student-friendly dictation HTML page")
    parser.add_argument("--items-file", required=True, help="UTF-8 text file; one dictation item per line")
    parser.add_argument("--out", required=True, help="output HTML path")
    parser.add_argument("--title", default=None, help="optional page title")
    args = parser.parse_args()

    source = Path(args.items_file)
    if not source.is_file():
        parser.error(f"items file not found: {source}")

    raw = source.read_text(encoding="utf-8")
    texts = parse_items(raw)
    if not texts:
        parser.error("no dictation items found; provide at least one non-empty line")

    items = [{"text": text, "lang": detect_language(text)} for text in texts]
    title, subtitle, has_en = infer_title_and_subtitle(items, args.title)

    template_path = Path(__file__).resolve().parent.parent / "assets" / "dictation-template.html"
    template = template_path.read_text(encoding="utf-8")
    html = render(template, items, title, subtitle, has_en)

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")

    counts = {"en": sum(i["lang"] == "en" for i in items), "zh": sum(i["lang"] == "zh" for i in items)}
    print(f"OK: {len(items)} items -> {output} (English: {counts['en']}, Chinese: {counts['zh']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
