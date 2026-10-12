"""Limpeza conservadora de artefatos do PDF, sem dependências externas."""
import unicodedata
import re


def clean_text(text):
    # Preserva acentos, operadores e sequências literais como r"\u200b".
    # Remove controles de formatação sem pronúncia (ZWSP, BOM, soft hyphen,
    # marcadores direcionais). Mantém tabulações e quebras para linhas de código.
    return ''.join(
        ' ' if char == '\u00a0' else char
        for char in text
        if unicodedata.category(char) not in ('Cf', 'Cc') or char in '\n\r\t'
    )


# Marcadores tipográficos; não inclui ponto, hífen, asterisco ou produto escalar.
_LIST_MARKER = re.compile(r"^[ \t]*[•●○◦▪▫‣⁃](?:[ \t]+|$)", re.MULTILINE)


def strip_list_marker(text):
    """Retira só marcadores destacados no começo de uma linha."""
    return _LIST_MARKER.sub('', text)
