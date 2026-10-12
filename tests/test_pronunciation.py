import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from leitor.pronunciation import apply_dictionary, load_dictionary, validate_dictionary, dictionary_revision, _matcher
from leitor.normalization import normalize_prose
from leitor.narration import prepare_spoken_text as say
from leitor.voice import VoiceEngine
from tests.test_voice_render import Model


class DictionaryTests(unittest.TestCase):
    def test_existing_rules_and_ambiguous_candidates(self):
        self.assertEqual(say('Python e Linux.'), 'páiton e línux.')
        self.assertEqual(say('Python e Linux.', 'common'), 'Python e Linux.')
        for text in ('colher', 'sede', 'gosto', 'sabia sábia sabiá', 'pais país'):
            self.assertEqual(apply_dictionary(text), text)
        self.assertEqual(len(dictionary_revision()), 12)

    def test_words_paths_and_identifiers_are_not_partially_replaced(self):
        for text in ('CPython', 'python_value', 'my_python', 'python.py', 'https://python.org',
                     'me@python.com', r'C:\Python\app.py', 'python.org'):
            self.assertEqual(apply_dictionary(text), text)
        self.assertEqual(apply_dictionary('Python.'), 'páiton.')
        self.assertNotIn('páiton', say('my_python = 1', 'code'))
        self.assertNotIn('páiton', say('print("Python")', 'code'))
        self.assertEqual(say('Veja `Python` e https://python.org.'), 'Veja `Python` e https://python.org.')

    def test_candidates_cannot_be_enabled_without_review(self):
        data = copy.deepcopy(load_dictionary())
        data['entries'][-1]['enabled'] = True
        with self.assertRaises(ValueError):
            validate_dictionary(data)

    def test_invalid_dictionary_falls_back_to_motor(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'bad.json'
            path.write_text('{')
            load_dictionary.cache_clear()
            _matcher.cache_clear()
            try:
                with patch('leitor.pronunciation.DATA', path):
                    self.assertEqual(apply_dictionary('Python'), 'Python')
            finally:
                load_dictionary.cache_clear()
                _matcher.cache_clear()

    def test_longest_match_and_no_cascade(self):
        data = {'entries': [dict(term='Alpha beta', spoken='Gamma', enabled=True, modes=['prose']),
                            dict(term='Alpha', spoken='Beta', enabled=True, modes=['prose']),
                            dict(term='Gamma', spoken='Delta', enabled=True, modes=['prose'])]}
        _matcher.cache_clear()
        try:
            with patch('leitor.pronunciation.load_dictionary', return_value=data):
                self.assertEqual(apply_dictionary('Alpha beta Alpha'), 'Gamma Beta')
        finally:
            _matcher.cache_clear()

    def test_prepared_audio_does_not_apply_dictionary_twice(self):
        engine = VoiceEngine.__new__(VoiceEngine)
        engine.model = Model(); engine.language = 'pt-br'; engine.load_seconds = 0
        with tempfile.TemporaryDirectory() as tmp:
            engine.render([{'text': 'Python', 'prepared': True}], 'pf_dora', Path(tmp)/'a.wav', lambda _: None)
        self.assertEqual(engine.model.calls, ['Python'])


class NormalizationTests(unittest.TestCase):
    def test_contextual_abbreviations_hours_and_units(self):
        self.assertEqual(say('O Dr. Paulo chegou às 14h30. Veja a pág. 12.', 'common'),
                         'O doutor Paulo chegou às 14 horas e 30 minutos. Veja a página 12.')
        self.assertEqual(normalize_prose('1 kg, 2 kg, 1 km, 3 km.'),
                         '1 quilograma, 2 quilogramas, 1 quilômetro, 3 quilômetros.')
        self.assertEqual(normalize_prose('1,000 kg'), '1,000 quilograma')
        self.assertEqual(normalize_prose('1h01 e 0h00'), '1 hora e 1 minuto e 0 horas')

    def test_invalid_or_ambiguous_forms_unchanged(self):
        for text in ('24h70', '14h99', 'm = 3', '12/10/2026', 'Dr. chegou', 'pág. exemplo', '10 km/h', '2 km²', '10 km / h', '2 kg.txt', 'x14h30'):
            self.assertEqual(normalize_prose(text), text)
        for text in ('`2 kg`', 'https://exemplo.com/14h30', r'C:\docs\14h30.txt'):
            self.assertEqual(normalize_prose(text), text)
        self.assertNotIn('quilogramas', say('x = 2 kg', 'code'))

    def test_audition_cases_are_unique_and_have_goals(self):
        data = json.loads((Path(__file__).resolve().parents[1]/'leitor/data/testes_pronuncia.json').read_text('utf-8'))
        self.assertEqual(len(data['cases']), 18)
        self.assertEqual(len({c['id'] for c in data['cases']}), 18)
        for case in data['cases']:
            self.assertTrue(case['goal'])
            self.assertTrue(say(case['text'], case['kind']))
