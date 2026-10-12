"""Segmentação de prosa e linhas técnicas, sem dependências de Qt ou TTS."""
import re
from .narration import LEXER
from .text_cleaning import strip_list_marker

ABBREVIATIONS = {"dr.", "dra.", "sr.", "sra.", "srta.", "prof.", "profa.",
                 "pág.", "págs.", "fig.", "art.", "vol.", "ex.", "etc.", "nº.", "séc."}
CLOSING = "\"”’\\')]}"


def sentence_end(word):
    clean = word.rstrip(CLOSING)
    return bool(re.search(r"[.!?…]$", clean)) and not (
        clean.lower() in ABBREVIATIONS
        or re.fullmatch(r"[A-ZÀ-Ý]\.", clean)
        or re.fullmatch(r"\d+\.", clean)
    )


def make_segment(words, index):
    regions = []
    for word in words:
        key = (word["page"], tuple(word["line"]) if isinstance(word["line"], (tuple, list)) else word["line"])
        if regions and regions[-1]["key"] == key:
            box, b = regions[-1]["box"], word["box"]
            regions[-1]["box"] = [min(box[0], b[0]), min(box[1], b[1]),
                                  max(box[2], b[2]), max(box[3], b[3])]
        else:
            regions.append({"key": key, "page": word["page"], "box": list(word["box"])})
    for region in regions:
        del region["key"]
    kind = words[0].get("kind", "prose")
    text = " ".join(w["text"] for w in words)
    # Uma linha técnica completa preserva espaços internos da extração.
    if kind != "prose" and all(w["line"] == words[0]["line"] for w in words):
        text = words[0].get("line_text", text)
    return {"id": index, "text": text,
            "speech_text": strip_list_marker(text) if words[0].get("list_start") else text,
            "regions": regions,
            "page": words[0]["page"], "kind": kind,
            "source_word_count": len(words)}


def block_starts_sentence(pending, word):
    if not word.get("break_before"):
        return False
    previous = pending[-1]["text"].rstrip(CLOSING)
    current = word["text"].lstrip('"“‘(—–')
    if previous.endswith((',', ';')):
        return False
    if current[:1].islower() and not previous.endswith(':'):
        return False
    return True


def segment_words(words, max_chars=360):
    groups, pending = [], []
    length, complete_start = 0, True
    pos = 0
    while pos < len(words):
        word = words[pos]
        if word.get("kind", "prose") != "prose":
            if pending:
                groups.append((pending, False))
                pending, length = [], 0
            line = [word]
            pos += 1
            while pos < len(words) and (words[pos]["page"], words[pos]["line"]) == (word["page"], word["line"]):
                line.append(words[pos])
                pos += 1
            groups.append((line, False))
            complete_start = True
            continue
        if pending:
            new_block = word.get("list_start", False) or block_starts_sentence(pending, word)
            if new_block or length + len(word["text"]) + 1 > max_chars:
                groups.append((pending, False))
                pending, length = [], 0
                complete_start = new_block
        pending.append(word)
        length += len(word["text"]) + (1 if len(pending) > 1 else 0)
        if sentence_end(word["text"]):
            groups.append((pending, complete_start))
            pending, length, complete_start = [], 0, True
        pos += 1
    if pending:
        groups.append((pending, False))
    result, index = [], 0
    while index < len(groups):
        first, complete = groups[index]
        selected, consumed = first, 1
        if complete and index + 1 < len(groups):
            second, second_complete = groups[index + 1]
            a = len(" ".join(w["text"] for w in first))
            b = len(" ".join(w["text"] for w in second))
            if (second_complete and a <= 120 and b <= 120
                    and a + b + 1 <= min(240, max_chars)
                    and all(w["page"] == first[0]["page"] for w in first + second)
                    and not second[0].get("break_before")
                    and not second[0].get("list_start")):
                selected, consumed = first + second, 2
        if selected[0].get('kind', 'prose') != 'prose':
            result.extend(technical_segments(selected, len(result), max_chars))
        else:
            result.append(make_segment(selected, len(result)))
        index += consumed
    return result


def technical_segments(words, index, limit):
    """Divide linhas por unidades lexicais; guarda as regiões de cada parte."""
    if limit < 1:
        raise ValueError('Limite de trecho inválido.')
    original = make_segment(words, index)
    text = original['text']
    if len(text) <= limit:
        return [original]
    # Localiza as palavras no texto da linha para mapear cada fragmento ao PDF.
    positions, cursor = [], 0
    for word in words:
        start = text.find(word['text'], cursor)
        if start < 0:
            start = cursor
        end = start + len(word['text'])
        positions.append((start, end, word))
        cursor = end
    units = [(m.start(), m.end()) for m in LEXER.finditer(text)]
    cuts, start, end = [], 0, 0
    for a, b in units:
        if b - a > limit:
            if end > start:
                cuts.append((start, end, False))
            # Um único literal/identificador enorme é narrado literalmente em partes.
            for offset in range(a, b, limit):
                cuts.append((offset, min(b, offset + limit), True))
            start = end = b
        else:
            if b - start > limit and end > start:
                cuts.append((start, end, False))
                start = a
            end = b
    if end > start:
        cuts.append((start, end, False))
    result = []
    for a, b, literal_part in cuts:
        part = text[a:b]
        if not part.strip():
            continue
        included = [w for x, y, w in positions if y > a and x < b]
        if not included:
            included = words[:1]
        segment = make_segment(included, index + len(result))
        segment['text'] = part
        segment['speech_text'] = strip_list_marker(part) if a == 0 and words[0].get('list_start') else part
        segment['source_word_count'] = sum(1 for x, y, w in positions if a <= x < b)
        if literal_part:
            segment['kind'] = 'code_literal'
        result.append(segment)
    return result


def remap_progress(saved, old_book, new_book):
    """Reposiciona pela contagem de palavras de origem, sem adivinhar tempos."""
    if not saved or not old_book or not old_book.get('segments') or not new_book.get('segments'):
        return saved
    old, new = old_book['segments'], new_book['segments']
    if [s['text'] for s in old] == [s['text'] for s in new]:
        return saved
    def count(segment):
        return segment.get('source_word_count', len(segment['text'].split()))
    result = dict(saved)
    old_index = min(max(0, saved['index']), len(old) - 1)
    anchor = sum(count(s) for s in old[:old_index])
    cursor = 0
    for index, segment in enumerate(new):
        cursor += count(segment)
        if cursor > anchor:
            result.update(index=index, offset=0)
            return result
    result.update(index=len(new) - 1, offset=0)
    return result


def buffered_seconds(cache, index, total, position_ms=0, rate=1.0):
    seconds, cursor = 0.0, index
    while cursor < total and cursor in cache:
        seconds += cache[cursor]["duration"]
        cursor += 1
    return max(0.0, seconds - position_ms / 1000) / rate, cursor == total


def next_missing(cache, index, total):
    while index < total and index in cache:
        index += 1
    return index if index < total else None
