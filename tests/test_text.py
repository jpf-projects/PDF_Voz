import tempfile
from pathlib import Path
import unittest
from reader.text import chunks, normalize, read_pdf_page


class TextTests(unittest.TestCase):
    def test_preserves_all_normalized_text_across_chunk_boundaries(self):
        text = ("Ação, saúde e atenção. Dr. Paulo pagou R$ 79,90! Um guarda-chuva.\n" * 30)
        parts = chunks(text)
        self.assertEqual(" ".join(parts), normalize(text))
        self.assertTrue(all(len(p) <= 320 for p in parts))

    def test_long_word_is_not_silently_damaged(self):
        with self.assertRaises(ValueError):
            chunks("A" * 400)

    def test_blank_and_page_bounds(self):
        from pypdf import PdfWriter
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "blank.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=600, height=800)
            with path.open("wb") as out:
                writer.write(out)
            with self.assertRaisesRegex(ValueError, "página de 1"):
                read_pdf_page(path, 0)
            with self.assertRaisesRegex(ValueError, "sem texto"):
                read_pdf_page(path, 1)


if __name__ == "__main__":
    unittest.main()
