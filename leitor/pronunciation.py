"""Dicionário global: dados literais, sem código executável ou regras por livro."""
import hashlib
import json
import logging
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).with_name('data') / 'pronuncias_pt_br.json'
MODES = {'common', 'prose', 'heading', 'code'}


def validate_dictionary(data):
    if data.get('schema_version') != 1 or not isinstance(data.get('entries'), list):
        raise ValueError('Formato de dicionário incompatível.')
    seen = set()
    for entry in data['entries']:
        term = entry.get('term')
        if not isinstance(term, str) or not term.strip() or len(term) > 120:
            raise ValueError('Termo inválido no dicionário.')
        key = unicodedata.normalize('NFC', term).casefold()
        if key in seen:
            raise ValueError('Termo duplicado no dicionário: ' + term)
        seen.add(key)
        if not isinstance(entry.get('enabled'), bool):
            raise ValueError('Campo enabled inválido.')
        if not isinstance(entry.get('modes'), list) or not set(entry['modes']) <= MODES:
            raise ValueError('Modo inválido no dicionário.')
        if entry.get('locale') != 'pt-BR':
            raise ValueError('Variante incompatível.')
        if entry['enabled']:
            if entry.get('context') != 'palavra_completa':
                raise ValueError('Contexto ainda não implementado para regra ativa.')
            if entry.get('status') not in ('herdada', 'aprovada'):
                raise ValueError('Uma candidata não pode ser ativada sem revisão.')
            if not isinstance(entry.get('spoken'), str) or not entry['spoken'].strip() or len(entry['spoken']) > 300:
                raise ValueError('Pronúncia ativa inválida.')
    return data


@lru_cache(maxsize=1)
def load_dictionary():
    try:
        return validate_dictionary(json.loads(DATA.read_text('utf-8')))
    except (OSError, ValueError, TypeError, AttributeError) as error:
        # A leitura continua com o motor original; a falha fica no log.
        logging.warning('Dicionário indisponível; usando pronúncia do motor: %s', error)
        return {'schema_version': 1, 'entries': []}


def dictionary_revision():
    payload = json.dumps(load_dictionary(), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()[:12]


@lru_cache(maxsize=4)
def _matcher(mode):
    mapping = {unicodedata.normalize('NFC', e['term']).casefold(): e['spoken']
               for e in load_dictionary()['entries'] if e['enabled'] and mode in e['modes']}
    if not mapping:
        return None, mapping
    # Não substitui partes de identificadores, domínios, caminhos ou palavras.
    pattern = r'(?<![\w@/\\.\-])(?:' + '|'.join(re.escape(t) for t in sorted(mapping, key=len, reverse=True)) + r')(?![\w@/\\\-]|\.[\w])'
    return re.compile(pattern, re.I), mapping


def apply_dictionary(text, mode='prose'):
    text = unicodedata.normalize('NFC', text)
    pattern, mapping = _matcher(mode)
    # Uma única passagem impede substituições em cascata.
    return pattern.sub(lambda m: mapping[m[0].casefold()], text) if pattern else text
