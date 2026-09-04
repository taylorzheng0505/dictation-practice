#!/usr/bin/env python3
"""Generate a self-contained dictation HTML page with embedded Microsoft neural TTS audio.

Cross-platform design: call the edge_tts Python API directly. Do not discover or invoke
an ``edge-tts`` executable, shell command, PATH entry, wrapper, .cmd, or .bat file.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

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


def load_edge_tts() -> Any:
    """Import edge_tts from the same Python environment that runs this script."""
    try:
        import edge_tts  # type: ignore
    except ModuleNotFoundError as exc:
        executable = sys.executable or "python"
        raise RuntimeError(
            "The Python package 'edge-tts' is not installed in the interpreter running this script. "
            f"Install it into this same interpreter with: {executable!r} -m pip install edge-tts. "
            "Do not troubleshoot PATH or create edge-tts CLI wrappers; this generator uses the Python API directly."
        ) from exc
    return edge_tts


async def synthesize(text: str, voice: str, output_path: Path, proxy: str | None, edge_tts: Any) -> None:
    """Synthesize one item through edge_tts.Communicate and save it as MP3."""
    kwargs: dict[str, str] = {}
    if proxy:
        kwargs["proxy"] = proxy
    try:
        communicator = edge_tts.Communicate(text, voice, **kwargs)
    except TypeError as exc:
        if proxy:
            raise RuntimeError(
                "The installed edge-tts version does not accept the proxy option used by this generator. "
                "Upgrade edge-tts in the same Python environment and retry."
            ) from exc
        raise
    await communicator.save(str(output_path))


async def synthesize_with_retries(
    text: str,
    voice: str,
    output_path: Path,
    proxy: str | None,
    edge_tts: Any,
) -> None:
    last_error: Exception | str | None = None
    for attempt in range(1, 4):
        try:
            if output_path.exists():
                output_path.unlink()
            await synthesize(text, voice, output_path, proxy, edge_tts)
            if output_path.is_file() and output_path.stat().st_size > 500:
                return
            last_error = "generated audio file is too small"
        except Exception as exc:  # noqa: BLE001
            last_error = exc
        if attempt < 3:
            await asyncio.sleep(0.6 * attempt)
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


async def build_entries(texts: list[str], proxy: str | None) -> list[dict[str, str]]:
    edge_tts = load_edge_tts()
    entries: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory(prefix="dictation-audio-") as temp_dir:
        temp_path = Path(temp_dir)
        for index, text in enumerate(texts, 1):
            lang = detect_language(text)
            voice = VOICE_BY_LANG[lang]
            mp3_path = temp_path / f"{index:03d}.mp3"
            await synthesize_with_retries(text, voice, mp3_path, proxy, edge_tts)
            entries.append({
                "text": text,
                "lang": lang,
                "voice": VOICE_LABEL_BY_LANG[lang],
                "audio": audio_data_url(mp3_path),
            })
            print(f"[{index}/{len(texts)}] {text} -> {voice}")
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a student-friendly dictation HTML page with neural TTS audio")
    parser.add_argument("--items-file", required=True, help="UTF-8 text file; one dictation item per line")
    parser.add_argument("--out", required=True, help="output HTML path")
    parser.add_argument("--title", default=None, help="optional page title")
    parser.add_argument("--proxy", default=None, help="optional proxy URL; defaults to HTTP_PROXY/http_proxy")
    args = parser.parse_args()

    source = Path(args.items_file)
    if not source.is_file():
        parser.error(f"items file not found: {source}")

    raw = source.read_text(encoding="utf-8")
    texts = parse_items(raw)
    if not texts:
        parser.error("no dictation items found; provide at least one non-empty line")

    title, subtitle = infer_title_and_subtitle(
        [{"text": text, "lang": detect_language(text)} for text in texts], args.title
    )
    proxy = args.proxy or os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")

    try:
        entries = asyncio.run(build_entries(texts, proxy))
    except RuntimeError as exc:
        parser.error(str(exc))

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
