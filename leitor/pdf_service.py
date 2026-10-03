"""Executado exclusivamente no processo de PDF; nunca na thread Qt."""
import hashlib
import re
from collections import Counter
from pathlib import Path
from .domain import segment_words


def _clean(text):
    # Não altera hífens, decimais, operadores nem nomes de variáveis.
    return text.replace("\x00", "").replace("\u00a0", " ")


def _line_metadata(textpage, fitz):
    lines = {}
    sizes = Counter()
    blocks = textpage.extractDICT()["blocks"]
    for block in blocks:
        if block.get("type") != 0:
            continue
        for number, line in enumerate(block.get("lines", [])):
            spans = line.get("spans", [])
            text = _clean("".join(s["text"] for s in spans))
            total = sum(len(s["text"].strip()) for s in spans) or 1
            mono = sum(len(s["text"].strip()) for s in spans
                       if s.get("flags", 0) & fitz.TEXT_FONT_MONOSPACED) / total
            bold = sum(len(s["text"].strip()) for s in spans
                       if s.get("flags", 0) & fitz.TEXT_FONT_BOLD) / total
            size = max((s["size"] for s in spans), default=0)
            for span in spans:
                sizes[round(span["size"], 1)] += len(span["text"].strip())
            lines[(block["number"], number)] = {
                "text": text, "size": size, "mono": mono, "bold": bold,
                "box": line["bbox"], "block_x": block["bbox"][0],
            }
    body_size = sizes.most_common(1)[0][0] if sizes else 12
    for meta in lines.values():
        text = meta["text"].strip()
        if text.startswith(">>>") or meta["mono"] >= .8:
            meta["kind"] = "code"
        elif (len(text) <= 160 and (
                re.match(r"^\d+(?:\.\d+)+\s*[-–—]\s+\S", text)
                or (meta["bold"] >= .8 and meta["size"] >= body_size * 1.15))):
            meta["kind"] = "heading"
        else:
            meta["kind"] = "prose"
    return lines


def extract_book(path, password="", progress=lambda *args: None):
    import pymupdf as fitz
    path = str(Path(path).resolve())
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    with fitz.open(path) as doc:
        if doc.needs_pass and not doc.authenticate(password):
            raise ValueError("PDF protegido: informe a senha correta ao abrir.")
        words, pages = [], []
        last_page, last_block = -1, -1
        for number, page in enumerate(doc):
            # Mesma TextPage para palavras e fontes: IDs de linha compatíveis.
            textpage = page.get_textpage(flags=fitz.TEXTFLAGS_WORDS)
            raw = page.get_text("words", textpage=textpage, sort=True)
            metadata = _line_metadata(textpage, fitz)
            line_counts = Counter((w[5], w[6]) for w in raw)
            pages.append({"width": page.rect.width, "height": page.rect.height,
                          "rotation": page.rotation, "words": len(raw)})
            for word in raw:
                text = _clean(word[4]).strip()
                if not text:
                    continue
                line_key = (word[5], word[6])
                meta = metadata.get(line_key, {})
                kind = meta.get("kind", "prose")
                # Exclui apenas linha numérica isolada na margem; preserva código.
                if (kind != "code" and text.isdecimal() and line_counts[line_key] == 1
                        and (word[3] < page.cropbox.height * .06
                             or word[1] > page.cropbox.height * .94)):
                    continue
                boundary = number == last_page and word[5] != last_block
                item = {"text": text, "box": list(word[:4]), "page": number,
                        "line": line_key, "break_before": boundary, "kind": kind}
                if kind != "prose" and meta:
                    line_text = meta["text"].rstrip()
                    if kind == "code":
                        # Estimativa de recuo em fontes monoespaçadas.
                        indent = round(max(0, meta["box"][0] - meta["block_x"])
                                       / max(1, meta["size"] * .6))
                        line_text = " " * min(indent, 80) + line_text
                    item["line_text"] = line_text
                words.append(item)
                last_page, last_block = number, word[5]
            progress(number + 1, len(doc))
        segments = segment_words(words)
        for segment in segments:
            for region in segment["regions"]:
                region["display_box"] = list(
                    fitz.Rect(region["box"]) * doc[region["page"]].rotation_matrix)
        toc = [{"level": int(level), "title": title, "page": int(page) - 1}
               for level, title, page in doc.get_toc() if 1 <= page <= len(doc)]
        return {"hash": digest.hexdigest(), "path": path,
                "title": doc.metadata.get("title") or Path(path).stem,
                "pages": pages, "segments": segments, "toc": toc,
                "extraction_version": 3}


def render_page(doc, number, scale):
    import pymupdf as fitz
    page = doc[number]
    scale = min(scale, 3500 / max(page.rect.width, page.rect.height))
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csRGB, alpha=False)
    return {"png": pix.tobytes("png"), "scale": scale}
