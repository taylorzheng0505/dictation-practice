#!/usr/bin/env python3
"""Generate a self-contained dictation HTML page with pre-synthesized neural TTS audio."""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
LIST_PREFIX_RE = re.compile(r"^\s*(?:[-*•·]|\d+[.)、．]|[A-Za-z][.)])\s+")

VOICE_BY_LANG = {
    "en": "en-GB-SoniaNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
}
VOICE_LABEL_BY_LANG = {
    "en": "英音 Sonia",
    "zh": "普通话 晓晓",
}


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


def infer_title_and_subtitle(items: list[dict[str, str]], requested_title: str | None) -> tuple[str, str]:
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
    return requested_title or default_title, subtitle


def synthesize(
    text: str,
    voice: str,
    output_path: Path,
    tts_command: str,
    proxy: str | None,
) -> None:
    command = [tts_command, "--voice", voice, "--text", text, "--write-media", str(output_path)]
    if proxy:
        command += ["--proxy", proxy]
    subprocess.run(command, check=True, capture_output=True, timeout=60)


def synthesize_with_retries(
    text: str,
    voice: str,
    output_path: Path,
    tts_command: str,
    proxy: str | None,
) -> None:
    last_error: Exception | str | None = None
    for _ in range(3):
        try:
            synthesize(text, voice, output_path, tts_command, proxy)
            if output_path.is_file() and output_path.stat().st_size > 500:
                return
            last_error = "generated audio file is too small"
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    raise RuntimeError(f'TTS failed for "{text}": {last_error}')


def audio_data_url(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return "data:audio/mpeg;base64," + encoded


def render(template: str, items: list[dict[str, str]], title: str, subtitle: str) -> str:
    items_json = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
    replacements = {
        "__TITLE__": title,
        "__SUBTITLE__": subtitle,
        "__COUNT__": str(len(items)),
        "__ITEMS_JSON__": items_json,
    }
    html = template
    for key, value in replacements.items():
        html = html.replace(key, value)
    leftovers = sorted(set(re.findall(r"__[A-Z0-9_]+__", html)))
    if leftovers:
        raise RuntimeError(f"unresolved template placeholders: {', '.join(leftovers)}")
    return html


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a student-friendly dictation HTML page with neural TTS audio")
    parser.add_argument("--items-file", required=True, help="UTF-8 text file; one dictation item per line")
    parser.add_argument("--out", required=True, help="output HTML path")
    parser.add_argument("--title", default=None, help="optional page title")
    parser.add_argument("--tts-command", default="edge-tts", help="edge-tts executable name or path")
    parser.add_argument("--proxy", default=None, help="optional proxy URL; defaults to HTTP_PROXY/http_proxy")
    args = parser.parse_args()

    source = Path(args.items_file)
    if not source.is_file():
        parser.error(f"items file not found: {source}")

    tts_path = shutil.which(args.tts_command) if os.path.sep not in args.tts_command else args.tts_command
    if not tts_path or not Path(tts_path).exists():
        parser.error(
            "edge-tts is not available. Install it with `python3 -m pip install edge-tts` "
            "before generating the dictation page."
        )

    raw = source.read_text(encoding="utf-8")
    texts = parse_items(raw)
    if not texts:
        parser.error("no dictation items found; provide at least one non-empty line")

    title, subtitle = infer_title_and_subtitle(
        [{"text": text, "lang": detect_language(text)} for text in texts], args.title
    )
    proxy = args.proxy or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")

    entries: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory(prefix="dictation-audio-") as temp_dir:
        temp_path = Path(temp_dir)
        for index, text in enumerate(texts, 1):
            lang = detect_language(text)
            voice = VOICE_BY_LANG[lang]
            mp3_path = temp_path / f"{index:03d}.mp3"
            synthesize_with_retries(text, voice, mp3_path, str(tts_path), proxy)
            entries.append({
                "text": text,
                "lang": lang,
                "voice": VOICE_LABEL_BY_LANG[lang],
                "audio": audio_data_url(mp3_path),
            })
            print(f"[{index}/{len(texts)}] {text} -> {voice}")

    template_path = Path(__file__).resolve().parent.parent / "assets" / "dictation-template.html"
    template = template_path.read_text(encoding="utf-8")
    html = render(template, entries, title, subtitle)

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")

    counts = {"en": sum(i["lang"] == "en" for i in entries), "zh": sum(i["lang"] == "zh" for i in entries)}
    print(f"OK: {len(entries)} items -> {output} (English: {counts['en']}, Chinese: {counts['zh']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
