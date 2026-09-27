import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import unittest
from pathlib import Path
from PySide6.QtWidgets import QApplication
from leitor.window import MainWindow


class FakeProcess:
    def is_alive(self):
        return True


class FakeChannel:
    def __init__(self):
        self.jobs = []
        self.messages = []
        self.process = FakeProcess()
    def send(self, job):
        self.jobs.append(job)
    def poll(self):
        messages, self.messages = self.messages, []
        yield from messages
    def stop(self):
        pass


class ControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.w = MainWindow(self.temp.name)
        self.w.poller.stop()
        self.w.saver.stop()
        self.w.pdf = FakeChannel()
        book = {'hash': 'test', 'path': '/test.pdf', 'title': 'Livro', 'pages': [{'width': 500, 'height': 700}],
                'toc': [], 'segments': [{'id': i, 'text': f'Trecho {i}.', 'page': 0, 'regions': []} for i in range(12)]}
        self.w.book_ready(book)
        self.w.tts = FakeChannel()
        self.w.tts_ready = True
    def tearDown(self):
        self.w.close()
        self.temp.cleanup()

    def test_pause_during_buffer_never_auto_starts(self):
        self.w.desired = True
        self.w.phase = 'buffering'
        self.w.drive()
        self.assertEqual(len(self.w.tts.jobs), 1)
        job = self.w.tts.jobs[0]
        self.w.toggle_play()
        self.w.tts.messages.append({'kind': 'audio', 'token': job['token'], 'index': job['index'],
                                   'path': job['path'], 'duration': 80., 'generation': 1.})
        self.w.tick()
        self.assertFalse(self.w.desired)
        self.assertEqual(self.w.phase, 'paused')
        self.assertIsNone(self.w.loaded_index)

    def test_jump_discards_old_generation_and_prioritizes_new_position(self):
        self.w.desired = True
        self.w.phase = 'buffering'
        self.w.drive()
        channel = self.w.tts
        old = channel.jobs[0]
        Path(old['path']).write_bytes(b'stale')
        self.w.navigate(8, True)
        channel.messages.append({'kind': 'audio', 'token': old['token'], 'index': 0,
                                 'path': old['path'], 'duration': 10., 'generation': 1.})
        self.w.tick()
        self.assertNotIn(0, self.w.cache)
        self.assertFalse(Path(old['path']).exists())
        self.assertEqual(channel.jobs[-1]['index'], 8)

    def test_close_stops_workers_cleans_audio_preserves_offset(self):
        self.w.offset = 1234
        folder = self.w.folder
        (folder / 'temp.wav').write_bytes(b'fake')
        self.w.close_book()
        self.assertFalse(folder.exists())
        self.assertIsNone(self.w.tts)
        self.assertEqual(self.w.store.load('test')['offset'], 1234)

    def test_less_than_target_at_end_starts_without_infinite_wait(self):
        self.w.index = 11
        self.w.desired = True
        self.w.phase = 'buffering'
        self.w.cache[11] = {'duration': 2., 'path': 'fake.wav'}
        called = []
        self.w.load_current = lambda: called.append(True)
        self.w.drive()
        self.assertEqual(called, [True])

    def test_initial_threshold_and_pause_while_loading(self):
        self.w.reserve.setCurrentIndex(self.w.reserve.findData(60))
        self.w.desired = True
        self.w.phase = 'buffering'
        self.w.cache[0] = {'duration': 59., 'path': 'fake.wav'}
        called = []
        self.w.load_current = lambda: called.append(True)
        self.w.drive()
        self.assertFalse(called)
        self.w.cache[1] = {'duration': 3., 'path': 'fake2.wav'}
        self.w.drive()
        self.assertEqual(called, [True])
        self.w.phase = 'loading'
        self.w.offset = 2500
        self.w.toggle_play()
        self.assertFalse(self.w.desired)
        self.assertEqual(self.w.phase, 'loading')
        self.assertEqual(self.w.offset, 2500)

    def test_voice_switch_discards_pending_old_voice_and_preserves_pause(self):
        self.w.desired = True
        self.w.phase = 'buffering'
        self.w.drive()
        old = self.w.tts.jobs[-1]
        self.assertEqual(old['voice'], 'pf_dora')
        self.w.toggle_play()
        self.w.offset = 1234
        self.w.voice_choice.setCurrentIndex(1)
        self.assertFalse(self.w.desired)
        self.assertEqual(self.w.offset, 0)
        self.assertEqual(self.w.store.load('test')['voice'], 'pm_alex')
        Path(old['path']).write_bytes(b'old')
        self.w.tts.messages.append(dict(kind='audio', token=old['token'], index=0,
            path=old['path'], duration=10., generation=1.))
        self.w.tick()
        self.assertFalse(self.w.cache)
        self.assertFalse(Path(old['path']).exists())
        self.w.toggle_play()
        self.assertEqual(self.w.tts.jobs[-1]['voice'], 'pm_alex')

    def test_play_ready_bypasses_reserve_only_when_requested(self):
        self.w.desired = True
        self.w.phase = 'buffering'
        self.w.cache[0] = {'duration': 2., 'path': 'fake.wav'}
        called = []
        self.w.load_current = lambda: called.append(True)
        self.w.drive()
        self.assertFalse(called)
        self.w.play_ready()
        self.assertEqual(called, [True])
        self.w.desired = False
        self.w.play_ready()
        self.assertEqual(called, [True])

    def test_different_voice_restores_sentence_but_not_offset(self):
        book = self.w.book
        self.w.store.save('test', 4, 2200, 1., 0, 1., False, 'pm_santa')
        self.w.book_ready(book)
        self.assertEqual(self.w.index, 4)
        self.assertEqual(self.w.offset, 0)

    def test_volume_and_reserve_are_persisted(self):
        self.w.volume.setValue(25)
        self.assertAlmostEqual(self.w.audio.volume(), .25)
        self.assertEqual(self.w.store.get('volume'), '25')
        self.w.reserve.setCurrentIndex(0)
        self.assertEqual(self.w.store.get('reserve'), '15')

    def test_output_default_explicit_disconnect_and_reconnect(self):
        from unittest.mock import patch
        from PySide6.QtCore import QByteArray
        class Device:
            def __init__(self, name): self.name = name
            def id(self): return QByteArray(self.name.encode())
            def description(self): return self.name
        class Audio:
            def __init__(self, device): self.current = device
            def device(self): return self.current
            def setDevice(self, device): self.current = device
        speaker, headphone = Device('speaker'), Device('headphone')
        original = self.w.audio
        self.w.audio = Audio(speaker)
        try:
            with patch('leitor.window.QMediaDevices') as devices:
                devices.audioOutputs.return_value = [speaker, headphone]
                devices.defaultAudioOutput.return_value = speaker
                self.w.refresh_outputs()
                self.w.output_choice.setCurrentIndex(2)
                self.assertEqual(self.w.audio.device(), headphone)
                devices.audioOutputs.return_value = [speaker]
                self.w.refresh_outputs()
                self.assertEqual(self.w.audio.device(), speaker)
                devices.audioOutputs.return_value = [speaker, headphone]
                self.w.refresh_outputs()
                self.assertEqual(self.w.audio.device(), headphone)
                self.w.output_choice.setCurrentIndex(0)
                self.assertEqual(self.w.audio.device(), speaker)
                devices.defaultAudioOutput.return_value = headphone
                self.w.refresh_outputs()
                self.assertEqual(self.w.audio.device(), headphone)
        finally:
            self.w.audio = original
