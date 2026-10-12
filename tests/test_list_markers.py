import tempfile
import unittest
from pathlib import Path
import pymupdf as fitz
from leitor.pdf_service import extract_book
from leitor.narration import prepare_spoken_text
from leitor.text_cleaning import strip_list_marker
from tests import test_controller as controller


class ListMarkerTests(unittest.TestCase):
    def test_only_leading_list_markers_removed(self):
        self.assertEqual(strip_list_marker('• à tarde\n  ● à noite\n◦ à medida que'),
                         'à tarde\nà noite\nà medida que')
        for text in ('a • b', 'a · b', '-5', '*args', 'x = "•"', '○x'):
            self.assertEqual(strip_list_marker(text), text)
        self.assertEqual(prepare_spoken_text('• à tarde', 'common'), 'à tarde')
        self.assertEqual(prepare_spoken_text('• à tarde', 'prose'), 'à tarde')
        self.assertIn('•', prepare_spoken_text('print("•")', 'code'))

    def test_pdf_lists_keep_display_and_separate_spoken_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'list.pdf'
            doc = fitz.open()
            page = doc.new_page()
            page.insert_font(fontname='testfont', fontbuffer=fitz.Font('helv').buffer)
            page.insert_text((72, 72), '• à tarde\n• à noite\n• à medida que', fontname='testfont')
            doc.save(path)
            doc.close()
            book = extract_book(path)
        self.assertEqual([s['speech_text'] for s in book['segments']],
                         ['à tarde', 'à noite', 'à medida que'])
        self.assertTrue(all(s['text'].startswith('•') for s in book['segments']))
        self.assertTrue(all(s['regions'] for s in book['segments']))


class ListMarkerControllerTests(unittest.TestCase):
    setUpClass = classmethod(controller.ControllerTests.setUpClass.__func__)
    setUp = controller.ControllerTests.setUp
    tearDown = controller.ControllerTests.tearDown

    def test_list_marker_not_sent_even_in_forced_technical_mode(self):
        self.w.book['segments'][0].update(text='• à tarde', speech_text='à tarde')
        self.w.narration_mode.blockSignals(True)
        self.w.narration_mode.setCurrentIndex(self.w.narration_mode.findData('code'))
        self.w.narration_mode.blockSignals(False)
        self.w.drive()
        self.assertEqual(self.w.tts.jobs[-1]['text'], 'à tarde')
        self.assertEqual(self.w.book['segments'][0]['text'], '• à tarde')
