import tempfile
import time
import unittest
from pathlib import Path
import pymupdf as fitz
from leitor.workers import ProcessChannel, pdf_worker


class PDFProcessTests(unittest.TestCase):
    def test_real_process_extracts_and_renders(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'sample.pdf'
            doc=fitz.open();p=doc.new_page()
            p.insert_text((50,60),'2.4 - Modo script',fontname='hebo',fontsize=16)
            p.insert_text((50,100),'>>> miles = 26.2\n>>> miles*1.61\n42.182',fontname='cour',fontsize=12)
            doc.save(path);doc.close()
            channel=ProcessChannel(pdf_worker)
            def wait_for(kind):
                until=time.monotonic()+15
                while time.monotonic()<until:
                    for m in channel.poll():
                        if m['kind']=='error': self.fail(m['error'])
                        if m['kind']==kind:return m
                    time.sleep(.02)
                self.fail('Timeout do processo PDF no teste')
            try:
                channel.send({'kind':'open','path':str(path)})
                book=wait_for('book')['book']
                self.assertEqual([s['kind'] for s in book['segments']],['heading','code','code','code'])
                self.assertEqual(book['segments'][2]['text'],'>>> miles*1.61')
                channel.send({'kind':'render','page':0,'request':1,'scale':1})
                page=wait_for('page')
                self.assertTrue(page['png'].startswith(b'\x89PNG'))
            finally: channel.stop()
            self.assertFalse(channel.process.is_alive())
