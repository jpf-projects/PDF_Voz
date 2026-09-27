import unittest
from reader.engine import select_portuguese


class LanguageTests(unittest.TestCase):
    def test_exact_backend_spelling(self):
        self.assertEqual(select_portuguese({"pt-BR": "Portuguese (Brazil)"}), "pt-BR")

    def test_legacy_brazil_name(self):
        self.assertEqual(select_portuguese({"pt": "brazil", "pt-pt": "portugal"}), "pt")

    def test_never_silently_switch_to_portugal_or_english(self):
        with self.assertRaises(RuntimeError):
            select_portuguese({"pt": "Portuguese (Portugal)", "en-us": "English"})

    def test_prefer_brazil_code(self):
        self.assertEqual(select_portuguese({"pt": "Portuguese", "pt-br": "Portuguese (Brazil)"}), "pt-br")
