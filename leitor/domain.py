"""Regras de segmentação e reserva. Nenhuma dependência de Qt ou TTS."""
import re

ABBREVIATIONS = {"dr.", "dra.", "sr.", "sra.", "srta.", "prof.", "profa.",
                 "pág.", "págs.", "fig.", "art.", "vol.", "ex.", "etc.", "nº.", "séc."}


def sentence_end(word):
    clean = word.rstrip('"”’\')]}')
    if not re.search(r"[.!?…]$", clean):
        return False
    if clean.lower() in ABBREVIATIONS or re.fullmatch(r"[A-ZÀ-Ý]\.", clean):
        return False
    if re.fullmatch(r"\d+\.", clean):
        return False
    return True


def make_segment(words, index):
    regions = []
    for word in words:
        key = (word["page"], word["line"])
        if regions and regions[-1]["key"] == key:
            box = regions[-1]["box"]
            b = word["box"]
            regions[-1]["box"] = [min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3])]
        else:
            regions.append({"key": key, "page": word["page"], "box": list(word["box"])})
    for region in regions:
        del region["key"]
    text = " ".join(w["text"] for w in words)
    return {"id": index, "text": text, "regions": regions, "page": words[0]["page"]}


def block_starts_sentence(pending, word):
    if not word.get("break_before"):
        return False
    previous = pending[-1]["text"].rstrip('"”’\')]}')
    current = word["text"].lstrip('"“‘(—–')
    # Blocos do PDF nem sempre são parágrafos. Preserva continuações evidentes.
    if previous.endswith((',', ';')):
        return False
    if current[:1].islower() and not previous.endswith(':'):
        return False
    return True


def remap_progress(saved, old_book, new_book):
    """Reposiciona pela contagem de palavras quando apenas as divisões mudam."""
    if not saved or not old_book or not old_book.get('segments') or not new_book.get('segments'):
        return saved
    old = old_book['segments']; new = new_book['segments']
    if [s['text'] for s in old] == [s['text'] for s in new]:
        return saved
    result = dict(saved)
    old_index = min(max(0, saved['index']), len(old)-1)
    anchor = sum(len(s['text'].split()) for s in old[:old_index])
    cursor = 0
    for index, segment in enumerate(new):
        cursor += len(segment['text'].split())
        if cursor > anchor:
            result['index'] = index
            result['offset'] = 0
            return result
    result['index'] = len(new)-1
    result['offset'] = 0
    return result


def segment_words(words, max_chars=360):
    result, pending = [], []
    length = 0
    for word in words:
        if pending and (block_starts_sentence(pending, word) or length + len(word["text"]) + 1 > max_chars):
            result.append(make_segment(pending, len(result)))
            pending, length = [], 0
        pending.append(word)
        length += len(word["text"]) + 1
        if sentence_end(word["text"]):
            result.append(make_segment(pending, len(result)))
            pending, length = [], 0
    if pending:
        result.append(make_segment(pending, len(result)))
    return result


def buffered_seconds(cache, index, total, position_ms=0, rate=1.0):
    seconds, cursor = 0.0, index
    while cursor < total and cursor in cache:
        seconds += cache[cursor]["duration"]
        cursor += 1
    seconds = max(0.0, seconds - position_ms / 1000)
    return seconds / rate, cursor == total


def next_missing(cache, index, total):
    while index < total and index in cache:
        index += 1
    return index if index < total else None
