import tempfile
import unittest
from pathlib import Path
from leitor.text_cleaning import clean_text
from leitor.pdf_service import _clean
from leitor.narration import prepare_spoken_text as say
from leitor.voice import VoiceEngine
from tests.test_voice_render import Model
from tests import test_controller as controller


class TextCleaningTests(unittest.TestCase):
    def test_invisible_controls_removed_without_damaging_code(self):
        text = '\ufeffação\u200b\u2060\x00 = 2.4 + 1\u00a0# comentário\n\tprint(r"\\u200b")'
        expected = 'ação = 2.4 + 1 # comentário\n\tprint(r"\\u200b")'
        self.assertEqual(clean_text(text), expected)
        self.assertEqual(_clean(text), expected)
        self.assertEqual(clean_text('pro\u00adgramação'), 'programação')
        self.assertEqual(say('\u200b\ufeff\u2060'), '')

    def test_modes_produce_different_speech(self):
        text = 'Valor (2.4): x += 1.'
        self.assertEqual(say(text, 'common'), text)
        technical = say(text, 'code')
        self.assertIn('abre parênteses', technical)
        self.assertIn('2 ponto quatro', technical)
        self.assertIn('recebe o valor atual mais', technical)
        self.assertEqual(say('Fim. Outra frase!', 'common'), 'Fim. Outra frase!')
        self.assertEqual(say('R$ 1.000,00', 'common'), '1000 reais')

    def test_invisibles_never_reach_synthesis(self):
        engine = VoiceEngine.__new__(VoiceEngine)
        engine.model = Model()
        engine.language = 'pt-br'
        engine.load_seconds = 0
        with tempfile.TemporaryDirectory() as tmp:
            engine.render(['Olá. \u200b\ufeff\u2060 Outra frase.'], 'pf_dora',
                          Path(tmp) / 'test.wav', lambda _: None)
        self.assertEqual(engine.model.calls, ['Olá. Outra frase.'])


class ModeControllerTests(unittest.TestCase):
    setUpClass = classmethod(controller.ControllerTests.setUpClass.__func__)
    setUp = controller.ControllerTests.setUp
    tearDown = controller.ControllerTests.tearDown

    def test_mode_saved_and_restored_per_book(self):
        self.w.narration_mode.setCurrentIndex(self.w.narration_mode.findData('common'))
        self.assertEqual(self.w.store.get('narration_mode:test'), 'common')
        self.w.book_ready(self.w.book)
        self.assertEqual(self.w.narration_mode.currentData(), 'common')
        self.w.drive()
        self.assertEqual(self.w.tts.jobs[-1]['kind'], 'common')

    def test_legacy_prose_selection_migrates(self):
        self.w.store.set('narration_mode:test', 'prose')
        self.w.book_ready(self.w.book)
        self.assertEqual(self.w.narration_mode.currentData(), 'common')

    def test_empty_segments_removed_and_region_preserved(self):
        book = dict(self.w.book)
        region = {'page': 0, 'box': [10, 20, 100, 40]}
        book['segments'] = [
            {'id': 0, 'text': '\u200b\ufeff', 'page': 0, 'regions': []},
            {'id': 1, 'text': 'Texto\u200b válido.', 'page': 0, 'regions': [region]},
        ]
        self.w.book_ready(book)
        segments = self.w.book['segments']
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]['id'], 0)
        self.assertEqual(segments[0]['text'], 'Texto válido.')
        self.assertEqual(segments[0]['regions'], [region])
        self.w.drive()
        self.assertEqual(self.w.tts.jobs[-1]['text'], 'Texto válido.')

    def test_all_invisible_book_does_not_queue_audio(self):
        book = dict(self.w.book)
        book['segments'] = [{'id': 0, 'text': '\u200b', 'page': 0, 'regions': []}]
        self.w.book_ready(book)
        self.w.drive()
        self.assertEqual(self.w.book['segments'], [])
        self.assertEqual(self.w.tts.jobs, [])
