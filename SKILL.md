---
name: dictation-practice
description: Generate a student-friendly HTML dictation practice page for Chinese and/or English schoolwork. Use when a user asks for 听写, spelling practice, dictation homework, or wants pasted text, an uploaded photo, screenshot, or file turned into a playable dictation page. If the dictation content is already available in the conversation or attachment, use it directly; if no content is available, ask only for the dictation content before generating the page.
---

# Dictation Practice

Turn school dictation content into a simple HTML practice page that a student can open and use independently.

## Workflow

1. Determine whether the dictation content is already available.
   - If the current conversation contains the words, phrases, sentences, or a clearly readable uploaded source containing them, use that content directly. Do not ask the user to repeat it or confirm obvious content.
   - If no dictation content is available, ask one concise question: `把今天要听写的内容发给我吧。可以直接粘贴文字，也可以发学校作业的照片。`
   - Ask a follow-up only when a source item is genuinely unreadable or ambiguous enough to change the answer. Identify the specific ambiguous item.

2. Normalize the content for generation.
   - Treat each intended word, phrase, or sentence as one item.
   - Preserve spelling, Chinese characters, punctuation, capitalization, and wording from the user's source.
   - Do not split an item at commas, semicolons, or Chinese punctuation. A sentence such as `After school, I went to the library.` must remain one item.
   - When converting a visible numbered or bulleted list, remove only the list marker, not the item text.
   - Write the normalized items to a UTF-8 temporary text file with exactly one item per line.

3. Generate the page by running:

   ```bash
   python3 <skill-dir>/scripts/generate_dictation.py \
     --items-file <items.txt> \
     --out <output-dir>/dictation.html
   ```

   Add `--title "..."` only when the user supplied or clearly requested a custom title.

4. Verify before delivery.
   - Confirm `dictation.html` exists and is non-empty.
   - Confirm the generated page contains the same number of items as the normalized source list.
   - Do not deliver a page when item extraction is uncertain; resolve only the ambiguous item first.

5. Deliver the HTML file directly. Keep the response short: tell the user the page is ready and provide the file link.

## Page behavior

The bundled template is intentionally optimized for younger students:

- English tasks offer only `美音` and `英音`; do not ask the user for this preference in chat.
- Chinese-only tasks hide the English-accent section automatically.
- Playback settings stay inside the page: speed, repetitions, and writing time use clear minus/value/plus controls.
- During practice, controls use explicit text such as `上一条`, `再听一次`, `下一条`, and `播放这一条` rather than icon-only controls.
- Answers stay hidden during dictation and are revealed only after completion through `检查答案`.
- The page uses the device browser's speech synthesis for playback. Recommend Chrome, Edge, or Safari only if the user reports a playback problem; do not add setup instructions preemptively.

## Output rules

- Do not ask about accent, voice gender, speed, repeat count, or writing interval before generating the page; those are page-level settings.
- Do not invent missing dictation content.
- Do not add definitions, translations, phonetics, example sentences, or teaching material unless the user explicitly asks for them.
- Do not change the accepted student interaction pattern in `assets/dictation-template.html` unless the user explicitly requests a design change.
