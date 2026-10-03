"""Preparação local de fala. Nunca executa ou avalia o código do PDF."""
import re
import unicodedata

NARRATION_REVISION = 'contexto-1'
DIGITS = dict(zip('0123456789', ('zero','um','dois','três','quatro','cinco','seis','sete','oito','nove')))
TERMS = {'python':'páiton', 'linux':'línux', 'default':'difólt', 'gcc':'gê cê cê'}
OPERATORS = {
    '**=':'recebe a potência de', '//=':'recebe a divisão inteira por',
    '<<=':'recebe o deslocamento à esquerda por', '>>=':'recebe o deslocamento à direita por',
    '+=':'recebe o valor atual mais', '-=':'recebe o valor atual menos',
    '*=':'recebe o valor atual vezes', '/=':'recebe o valor atual dividido por',
    '%=':'recebe o resto da divisão por', '&=':'recebe o e bit a bit com',
    '|=':'recebe o ou bit a bit com', '^=':'recebe o ou exclusivo com', '@=':'recebe o produto matricial por',
    '**':'elevado a', '//':'dividido por, parte inteira', '==':'igual a',
    '!=':'diferente de', '>=':'maior ou igual a', '<=':'menor ou igual a',
    ':=':'recebe', '<<':'deslocamento à esquerda', '>>':'deslocamento à direita',
    '->':'seta para', '...':'reticências', '+':'mais', '-':'menos', '*':'vezes',
    '/':'dividido por', '=':'recebe', '>':'maior que', '<':'menor que',
    '%':'resto da divisão por', '&':'e bit a bit', '|':'ou bit a bit',
    '^':'ou exclusivo', '~':'inversão de bits', '@':'arroba',
    '(':'abre parênteses', ')':'fecha parênteses', '[':'abre colchetes', ']':'fecha colchetes',
    '{':'abre chaves', '}':'fecha chaves', '.':'ponto', ',':'vírgula', ':':'dois pontos',
    ';':'ponto e vírgula', '\\':'barra invertida', '#':'cerquilha',
    "'":'aspas simples', '"':'aspas duplas', '_':'sublinhado', '!':'exclamação', '?':'interrogação',
}
# Scanner tolerante a linhas incompletas. Alternativas longas vêm primeiro.
LEXER = re.compile(
    r'''(?P<string>(?:[rRuUbBfF]{0,2})(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'))'''
    r'|(?P<comment>\#[^\n]*)'
    r'|(?P<number>0[xX][0-9a-fA-F_]+|0[bB][01_]+|0[oO][0-7_]+|(?:\d[\d_]*(?:\.[\d_]*)?|\.\d[\d_]*)(?:[eE][+\-]?\d[\d_]*)?[jJ]?)'
    r'|(?P<name>[^\W\d]\w*)'
    r'|(?P<operator>' + '|'.join(re.escape(s) for s in sorted(OPERATORS, key=len, reverse=True)) + r')'
    r'|(?P<space>\s+)|(?P<other>.)', re.DOTALL)


def ascii_digits(text):
    return ''.join(str(unicodedata.decimal(c)) if c.isdecimal() else c for c in text)


def terms(text):
    return re.sub(r'\b(Python|Linux|default|GCC)\b',
                  lambda m: TERMS[m[0].lower()], text, flags=re.I)


def number(text):
    text = ascii_digits(text)
    # Separadores de dígitos são lidos explicitamente em código.
    if '_' in text or re.match(r'0[xXbBoO]', text):
        return ' '.join(DIGITS.get(c, OPERATORS.get(c, c)) for c in text)
    if text[-1:] in ('j', 'J'):
        return number(text[:-1]) + ' jota'
    exponent = re.fullmatch(r'(.+)[eE]([+\-]?\d+)', text)
    if exponent:
        e = exponent[2].replace('-', 'menos ').replace('+', 'mais ')
        return number(exponent[1]) + ' vezes dez elevado a ' + e
    if '.' in text:
        left, right = text.split('.', 1)
        return (left or 'zero') + ' ponto' + (' ' + ' '.join(DIGITS.get(c, c) for c in right) if right else '')
    return text


def literal(text):
    # Dentro de strings, símbolos são literais, não operações.
    names = {'+':'sinal de mais','-':'hífen','*':'asterisco','/':'barra',
             '=':'sinal de igual','>':'sinal de maior','<':'sinal de menor',
             '%':'por cento','&':'e comercial','|':'barra vertical','^':'circunflexo','~':'til'}
    return ''.join(' ' + names.get(c, OPERATORS[c]) + ' ' if c in OPERATORS else c for c in text)


def code_text(text):
    prefix = ''
    text = text.strip()
    if text.startswith('>>>'):
        prefix, text = 'Entrada no terminal: ', text[3:].lstrip()
    elif text.startswith('... '):
        prefix, text = 'Continuação: ', text[4:]
    out = []
    for m in LEXER.finditer(text):
        token, kind = m[0], m.lastgroup
        if kind == 'space':
            continue
        if kind == 'number':
            out.append(number(token))
        elif kind == 'operator':
            out.append(OPERATORS[token])
        elif kind == 'string':
            quote_at = min(i for i, c in enumerate(token) if c in '\"\'')
            qualifier = ('prefixo ' + token[:quote_at] + ', ') if quote_at else ''
            out.append(qualifier + 'abre aspas, ' + literal(token[quote_at+1:-1]) + ', fecha aspas')
        elif kind == 'comment':
            out.append('Comentário: ' + terms(token[1:].strip()))
        elif kind == 'name':
            out.append(terms(token.replace('_', ' sublinhado ')))
        else:
            out.append(token)
    return prefix + ' '.join(out)


def prose_text(text):
    # Moeda brasileira: não converte o ponto de milhar em ponto decimal.
    def money(m):
        whole = m[1].replace('.', '')
        cents = m[2]
        result = whole + (' real' if int(whole) == 1 else ' reais')
        if cents and int(cents):
            result += ' e ' + str(int(cents)) + (' centavo' if int(cents) == 1 else ' centavos')
        return result
    text = re.sub(r'R\$\s*([0-9]{1,3}(?:\.[0-9]{3})+|[0-9]+)(?:,([0-9]{2}))?(?![0-9,])', money, text)
    text = re.sub(r'(?<![\w.,])([0-9]{1,3}(?:\.[0-9]{3})+)(,[0-9]+)?(?![\w.]|,[0-9])',
                  lambda m: m[1].replace('.', '') + (m[2] or ''), text)
    text = re.sub(r'\bPython\s+([0-9]+(?:\.[0-9]+)+)\b',
                  lambda m: 'Python versão ' + ' ponto '.join(m[1].split('.')), text, flags=re.I)
    return terms(text)


def prepare_spoken_text(text, kind='prose'):
    if kind == 'code_literal':
        result = literal(text)
    elif kind == 'code':
        result = code_text(text)
    elif kind == 'heading':
        text = re.sub(r'^(\s*)([0-9]+(?:\.[0-9]+)+)\s*(?:[-–—]\s*)?',
                      lambda m: m[1] + ' ponto '.join(m[2].split('.')) + ': ', text)
        result = prose_text(text)
    else:
        result = prose_text(text)
    return re.sub(r'\s+', ' ', result).strip()


def spoken_chunks(text, limit=320):
    """Limita cada chamada ao TTS após expansão. Não perde palavras/caracteres."""
    if limit < 1:
        raise ValueError('Limite de fala inválido.')
    pending = ''
    for word in text.split():
        if len(word) > limit:
            if pending:
                yield pending
                pending = ''
            for start in range(0, len(word), limit):
                yield word[start:start+limit]
            continue
        if pending and len(pending) + len(word) + 1 > limit:
            yield pending
            pending = ''
        pending = (pending + ' ' + word).strip()
    if pending:
        yield pending
