"""Executado exclusivamente no processo de PDF; nunca na thread Qt."""
import hashlib
from pathlib import Path
from .domain import segment_words


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
            raw = page.get_text("words", sort=True)
            matrix = page.rotation_matrix
            pages.append({"width": page.rect.width, "height": page.rect.height,
                          "rotation": page.rotation, "words": len(raw)})
            for word in raw:
                text = word[4].replace("\x00", "").strip()
                if not text:
                    continue
                # Números de página isolados em margem são excluídos conservadoramente.
                if text.isdecimal() and (word[3] < page.cropbox.height * .06 or word[1] > page.cropbox.height * .94):
                    continue
                box = list(word[:4])
                # Armazenamos coordenadas canônicas não rotacionadas + regiões de exibição.
                boundary = number == last_page and word[5] != last_block
                words.append({"text": text, "box": box, "page": number,
                              "line": (word[5], word[6]), "break_before": boundary})
                last_page, last_block = number, word[5]
            progress(number + 1, len(doc))
        segments = segment_words(words)
        for segment in segments:
            for region in segment["regions"]:
                region["display_box"] = list(fitz.Rect(region["box"]) * doc[region["page"]].rotation_matrix)
        toc = [{"level": int(level), "title": title, "page": int(page) - 1}
               for level, title, page in doc.get_toc() if 1 <= page <= len(doc)]
        return {"hash": digest.hexdigest(), "path": path,
                "title": doc.metadata.get("title") or Path(path).stem,
                "pages": pages, "segments": segments, "toc": toc,
                "extraction_version": 2}


def render_page(doc, number, scale):
    import pymupdf as fitz
    page = doc[number]
    scale = min(scale, 3500 / max(page.rect.width, page.rect.height))
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csRGB, alpha=False)
    return {"png": pix.tobytes("png"), "scale": scale}
