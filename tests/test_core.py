import tempfile
import unittest
from pathlib import Path

from leitor.domain import buffered_seconds, segment_words
from leitor.storage import Store, clean_sessions
from leitor.pdf_service import extract_book, render_page


class CoreTests(unittest.TestCase):
    def test_buffer_contiguous_only_and_speed(self):
        cache = {0: {"duration": 30}, 1: {"duration": 40}, 3: {"duration": 50}}
        seconds, end = buffered_seconds(cache, 0, 4, 10000, 2)
        self.assertEqual(seconds, 30)
        self.assertFalse(end)
        self.assertEqual(buffered_seconds(cache, 3, 4), (50, True))

    def test_words_preserved_across_pages_and_regions(self):
        text = ['O', 'Dr.', 'Paulo', 'pagou', '79,90', 'reais.', 'Depois', 'voltou.']
        words = [{"text": t, "page": i // 4, "line": i // 2,
                  "box": [i * 10, 20, i * 10 + 8, 30]} for i, t in enumerate(text)]
        segments = segment_words(words)
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0]['text'], 'O Dr. Paulo pagou 79,90 reais.')
        self.assertEqual({r['page'] for r in segments[0]['regions']}, {0, 1})
        self.assertEqual(' '.join(s['text'] for s in segments), ' '.join(text))

    def test_progress_and_cleaning_are_separate(self):
        with tempfile.TemporaryDirectory() as d:
            store = Store(d)
            store.save('book', 7, 3200, 1.25, 2, 1.4)
            audio = Path(d) / 'audio'
            (audio / 'session_old').mkdir(parents=True)
            (audio / 'session_old' / 'audio.wav').write_bytes(b'test')
            (audio / 'keep.txt').write_text('not a session')
            clean_sessions(audio)
            self.assertFalse((audio / 'session_old').exists())
            self.assertTrue((audio / 'keep.txt').exists())
            self.assertEqual(store.load('book')['offset'], 3200)
            store.close()

    def test_extraction_rotation_and_render_agree(self):
        import pymupdf as fitz
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'fixture.pdf'
            doc = fitz.open()
            page = doc.new_page(width=500, height=700)
            page.insert_text((60, 100), 'Uma frase simples. Outra frase aqui.', fontsize=14)
            page.set_rotation(90)
            doc.save(path)
            doc.close()
            book = extract_book(path)
            self.assertEqual(len(book['segments']), 1)
            self.assertEqual(book['segments'][0]['text'], 'Uma frase simples. Outra frase aqui.')
            with fitz.open(path) as doc:
                r = book['segments'][0]['regions'][0]
                self.assertEqual(r['display_box'], list(fitz.Rect(r['box']) * doc[0].rotation_matrix))
                rendered = render_page(doc, 0, 1.5)
                self.assertTrue(rendered['png'].startswith(b'\x89PNG'))

    def test_encrypted_pdf_requires_password_and_retains_no_password(self):
        import pymupdf as fitz
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'secret.pdf'
            doc = fitz.open()
            doc.new_page().insert_text((60, 100), 'Texto de teste.')
            doc.save(path, encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw='owner', user_pw='test')
            doc.close()
            with self.assertRaisesRegex(ValueError, 'protegido'):
                extract_book(path)
            book = extract_book(path, 'test')
            self.assertEqual(book['segments'][0]['text'], 'Texto de teste.')
            self.assertNotIn('password', book)


if __name__ == '__main__':
    unittest.main()
