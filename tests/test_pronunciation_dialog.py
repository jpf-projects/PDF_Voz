import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from leitor.pronunciation_dialog import PronunciationDialog
from tests import test_controller as controller


class PronunciationDialogTests(unittest.TestCase):
    setUpClass = classmethod(controller.ControllerTests.setUpClass.__func__)
    setUp = controller.ControllerTests.setUp
    tearDown = controller.ControllerTests.tearDown

    def make_dialog(self):
        d = PronunciationDialog(self.w, 'models', Path(self.temp.name)/'test_audio',
                                'pf_dora', self.w.audio.device(), .5)
        d.timer.stop()
        self.addCleanup(d.reject)
        return d

    def test_preview_and_sequential_generation(self):
        d = self.make_dialog()
        d.original.setPlainText('Dr. Paulo chegou às 14h30.')
        self.assertEqual(d.prepared.toPlainText(), 'doutor Paulo chegou às 14 horas e 30 minutos.')
        d.channel = controller.FakeChannel()
        d.ready = True
        d.start_comparison()
        self.assertEqual(len(d.channel.jobs), 1)
        self.assertEqual(d.channel.jobs[0]['text'], 'Dr. Paulo chegou às 14h30.')
        self.assertTrue(d.channel.jobs[0]['prepared'])
        self.assertTrue(d.busy)
        d.channel.messages.append({'kind': 'audio'})
        d.poll()
        self.assertEqual(len(d.channel.jobs), 2)
        self.assertEqual(d.channel.jobs[1]['text'], d.prepared.toPlainText())
        d.channel.messages.append({'kind': 'audio'})
        d.poll()
        self.assertFalse(d.busy)
        self.assertTrue(d.play_a.isEnabled())
        d.prepared.setPlainText('Uma nova proposta.')
        self.assertFalse(d.play_a.isEnabled())
        self.assertFalse(d.play_b.isEnabled())

    def test_empty_input_no_worker_and_close_cleans(self):
        d = self.make_dialog()
        d.original.setPlainText('')
        d.start_comparison()
        self.assertIsNone(d.channel)
        (d.folder/'temp.wav').write_bytes(b'test')
        d.reject()
        self.assertFalse(d.folder.exists())

    def test_worker_error_is_recoverable(self):
        d = self.make_dialog()
        channel = controller.FakeChannel()
        channel.stop = MagicMock()
        d.channel = channel
        d.ready = True
        d.start_comparison()
        channel.messages.append({'kind':'error', 'error':'Teste de falha'})
        d.poll()
        channel.stop.assert_called_once()
        self.assertIsNone(d.channel)
        self.assertFalse(d.busy)
        self.assertIn('Teste de falha', d.status.text())

    def test_open_test_pauses_reader_and_stops_old_inference(self):
        self.w.desired = True
        self.w.phase = 'buffering'
        self.w.drive()
        old = self.w.tts
        old.stop = MagicMock()
        with patch('leitor.pronunciation_dialog.PronunciationDialog') as dialog, \
                patch.object(self.w, 'select_models', return_value='models'):
            self.w.open_pronunciation_test()
        old.stop.assert_called_once()
        self.assertFalse(self.w.desired)
        self.assertIsNone(self.w.tts)
        self.assertIsNone(self.w.pending_audio)
        dialog.return_value.exec.assert_called_once()
        self.assertEqual(self.w.index, 0)
