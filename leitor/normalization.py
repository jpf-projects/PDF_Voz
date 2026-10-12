"""Normalização conservadora de texto corrente em português brasileiro."""
import re
from decimal import Decimal

# Trechos explícitos de código, endereços e caminhos não recebem estas regras.
PROTECTED = re.compile(r'`[^`]*`|https?://\S+|www\.\S+|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|[A-Za-z]:\\\S+', re.I)


def map_unprotected(text, transform):
    out, cursor = [], 0
    for match in PROTECTED.finditer(text):
        out.extend((transform(text[cursor:match.start()]), match[0]))
        cursor = match.end()
    out.append(transform(text[cursor:]))
    return ''.join(out)


def _normalize(text):
    # Abreviações somente em contextos reconhecíveis.
    text = re.sub(r'(?<![\w.])pág\.(?=\s+\d)', 'página', text, flags=re.I)
    text = re.sub(r'(?<![\w.])págs\.(?=\s+\d)', 'páginas', text, flags=re.I)
    titles = {'dr': 'doutor', 'dra': 'doutora', 'sr': 'senhor', 'sra': 'senhora', 'prof': 'professor', 'profa': 'professora'}
    text = re.sub(r'(?<![\w.])(Dr|Dra|Sr|Sra|Prof|Profa)\.(?=\s+[A-ZÀ-Ý][a-zà-ÿ])',
                  lambda m: titles[m[1].lower()], text)
    def hour(m):
        hours, minutes = int(m[1]), int(m[2])
        if hours > 23 or minutes > 59:
            return m[0]
        result = f'{hours} ' + ('hora' if hours == 1 else 'horas')
        if minutes:
            result += f' e {minutes} ' + ('minuto' if minutes == 1 else 'minutos')
        return result
    text = re.sub(r'(?<![\w./])([0-9]{1,2})h([0-9]{2})(?![\w/]|\.[\w])', hour, text)
    units = {'kg': ('quilograma', 'quilogramas'), 'km': ('quilômetro', 'quilômetros')}
    def unit(m):
        singular = Decimal(m[1].replace(',', '.')) == 1
        return m[1] + ' ' + units[m[2]][0 if singular else 1]
    return re.sub(r'(?<![\w.,/])([0-9]+(?:,[0-9]+)?)\s+(kg|km)(?![\w²³^]|\.[\w]|\s*[/²³^])', unit, text)


def normalize_prose(text):
    return map_unprotected(text, _normalize)
