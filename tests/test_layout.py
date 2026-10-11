"""Layout não deve alterar a navegação, síntese ou intenção de reprodução."""
import tempfile
import unittest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from leitor.window import MainWindow


class LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.w = MainWindow(self.temp.name)
        self.w.poller.stop()
        self.w.saver.stop()
        self.w.show()
        self.app.processEvents()

    def tearDown(self):
        self.w.close()
        self.temp.cleanup()

    def test_sidebar_preserves_playback_and_does_not_request_page(self):
        self.w.desired = True
        self.w.phase = 'playing'
        with patch.object(self.w, 'show_page') as show_page, patch.object(self.w, 'drive') as drive:
            self.w.sidebar_button.setChecked(False)
            self.assertTrue(self.w.sidebar.isHidden())
            self.assertFalse(self.w.sidebar_action.isChecked())
            self.assertEqual(self.w.store.get('sidebar_visible'), '0')
            self.w.sidebar_action.setChecked(True)
            self.assertFalse(self.w.sidebar.isHidden())
            self.assertTrue(self.w.sidebar_button.isChecked())
            show_page.assert_not_called()
            drive.assert_not_called()
        self.assertTrue(self.w.desired)
        self.assertEqual(self.w.phase, 'playing')

    def test_preferences_are_nonmodal_and_reused(self):
        dialog = self.w.preferences
        with patch.object(self.w, 'change_voice') as voice, patch.object(self.w, 'show_page') as page:
            self.w.open_preferences()
            self.assertTrue(dialog.isVisible())
            self.assertFalse(dialog.isModal())
            self.assertTrue(dialog.isAncestorOf(self.w.voice_choice))
            self.assertTrue(dialog.isAncestorOf(self.w.output_choice))
            self.assertFalse(dialog.isAncestorOf(self.w.play_button))
            dialog.close()
            self.w.open_preferences()
            self.assertIs(dialog, self.w.preferences)
            voice.assert_not_called()
            page.assert_not_called()

    def test_small_window_preserves_reading_space(self):
        self.w.resize(850, 600)
        self.app.processEvents()
        self.assertLessEqual(self.w.minimumSizeHint().width(), 850)
        self.assertGreater(self.w.viewer.height(), 300)
        self.assertTrue(self.w.play_button.isVisible())
        self.assertTrue(self.w.volume.isVisible())
        width = self.w.viewer.width()
        self.w.sidebar_button.setChecked(False)
        self.app.processEvents()
        self.assertGreater(self.w.viewer.width(), width)
