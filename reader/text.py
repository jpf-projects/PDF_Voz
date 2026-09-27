import re
from pathlib import Path


def normalize(text):
    # Conservador: preserva hífens e palavras; não tenta corrigir o livro.
    return re.sub(r"\s+", " ", text.replace("\x00", " ")).strip()


def chunks(text, limit=320):
    """Blocos de teste limitados em caracteres; não são sentenças persistentes."""
    text = normalize(text)
    result = []
    while text:
        if len(text) <= limit:
            result.append(text)
            break
        stop = max(text.rfind(mark, 0, limit) for mark in (". ", "! ", "? ", "; "))
        stop = stop + 1 if stop >= limit // 3 else text.rfind(" ", 0, limit + 1)
        if stop <= 0:
            # Não dividir uma palavra gigante silenciosamente.
            raise ValueError("Palavra ou sequência muito longa. Revise o texto de teste.")
        result.append(text[:stop].strip())
        text = text[stop:].strip()
    return result


def read_pdf_page(path, page):
    from pypdf import PdfReader
    reader = PdfReader(str(Path(path)))
    if reader.is_encrypted and not reader.decrypt(""):
        raise ValueError("PDF protegido por senha. Use um PDF sem senha neste teste.")
    if not 1 <= page <= len(reader.pages):
        raise ValueError(f"Escolha uma página de 1 a {len(reader.pages)}.")
    text = normalize(reader.pages[page - 1].extract_text() or "")
    if len(text) < 30:
        raise ValueError("Página sem texto suficiente. Escolha uma página de conteúdo. Não há OCR nesta versão.")
    # Somente amostra. A numeração é a página física do PDF, iniciando em 1.
    words = text.split()
    return " ".join(words[:180]), len(reader.pages), len(words) > 180
