import time
import unittest
from unittest.mock import patch
from tests import test_controller as fixture
from leitor.window import WORKER_TIMEOUT


class RecoveryTests(unittest.TestCase):
    setUpClass = classmethod(fixture.ControllerTests.setUpClass.__func__)
    setUp = fixture.ControllerTests.setUp
    tearDown = fixture.ControllerTests.tearDown
    def test_kind_and_override_reach_job(self):
        self.w.book['segments'][0]['kind']='code'
        self.w.drive()
        self.assertEqual(self.w.tts.jobs[-1]['kind'],'code')
        self.w.pending_audio=None
        self.w.narration_mode.setCurrentIndex(self.w.narration_mode.findData('prose'))
        self.w.drive()
        self.assertEqual(self.w.tts.jobs[-1]['kind'],'prose')
        self.assertEqual(self.w.store.get('narration_mode:test'),'prose')

    def test_paused_generation_stops_at_cap_and_completion(self):
        self.w.cache={0:{'duration':90,'path':'unused'}}
        self.w.drive()
        self.assertEqual(self.w.tts.jobs,[])
        self.w.cache={}
        self.w.completed=True
        self.w.drive()
        self.assertEqual(self.w.tts.jobs,[])
        self.w.completed=False
        self.w.drive()
        self.assertEqual(len(self.w.tts.jobs),1)
        self.assertFalse(self.w.desired)
        self.assertIsNone(self.w.loaded_index)

    def test_dead_pdf_after_import_is_detected(self):
        self.w.pdf.process.is_alive=lambda:False
        self.w.render_busy=True
        self.w.tick()
        self.assertIsNone(self.w.pdf)
        self.assertFalse(self.w.render_busy)
        self.assertEqual(self.w.phase,'error')

    def test_pdf_timeout_and_idle_pdf(self):
        self.w.pdf_activity=time.monotonic()-WORKER_TIMEOUT-1
        self.w.render_busy=False
        self.w.tick()
        self.assertIsNotNone(self.w.pdf)
        self.w.render_busy=True
        self.w.tick()
        self.assertIsNone(self.w.pdf)

    def test_tts_timeout_discards_partial_file(self):
        self.w.drive()
        path=self.w.folder / 'partial.part.wav'
        final=path.with_name('partial.wav')
        path.write_bytes(b'partial')
        self.w.pending_audio['path']=str(final)
        self.w.tts_activity=time.monotonic()-WORKER_TIMEOUT-1
        self.w.tick()
        self.assertIsNone(self.w.tts)
        self.assertFalse(path.exists())
        self.assertEqual(self.w.phase,'error')

    def test_idle_tts_is_not_timed_out(self):
        self.w.tts_activity=time.monotonic()-WORKER_TIMEOUT-1
        self.w.cache={0:{'duration':90,'path':'unused'}}
        self.w.tick()
        self.assertIsNotNone(self.w.tts)

    def test_changed_audio_revision_resets_offset(self):
        self.w.store.save('test',3,2500,1,0,1,False,'pf_dora')
        self.w.store.set('audio_revision:test','pausas-1')
        self.w.book_ready(self.w.book)
        self.assertEqual(self.w.index,3)
        self.assertEqual(self.w.offset,0)

    def test_unchanged_progress_does_not_commit(self):
        self.w.save_progress()
        changes=self.w.store.db.total_changes
        self.w.save_progress()
        self.assertEqual(self.w.store.db.total_changes,changes)

    def test_forget_removes_book_and_progress_not_other_books(self):
        self.w.store.save('other',1,0,1,0,1)
        self.w.forget_book()
        self.assertIsNone(self.w.store.load('test'))
        self.assertIsNone(self.w.store.book_payload('test'))
        self.assertIsNotNone(self.w.store.load('other'))
        self.assertIsNone(self.w.book)
