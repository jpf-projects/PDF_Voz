"""Teste manual automatizado: processos reais de PDF e voz, interface offscreen.
Uso: python -m tests.integration_smoke MODELS_DIR (ver documentação).
"""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['ORT_DISABLE_TELEMETRY'] = '1'
import sys
import tempfile
import time
from pathlib import Path


def main():
    import pymupdf as fitz
    from PySide6.QtWidgets import QApplication
    from leitor.window import MainWindow
    app = QApplication([])
    with tempfile.TemporaryDirectory() as d:
        os.environ['PDFVOZ_DATA_ROOT'] = d
        doc = fitz.open()
        page = doc.new_page(width=500, height=700)
        page.insert_text((60, 100), 'Este e um teste de leitura. A voz funciona localmente.', fontsize=16)
        path = Path(d) / 'teste.pdf'
        doc.save(path)
        doc.close()
        window = MainWindow(d)
        window.store.set('models', str(Path(sys.argv[1]).resolve()))
        window.show()
        window.open_book(path)
        def wait_for(condition, timeout):
            start = time.monotonic()
            while not condition():
                app.processEvents()
                if time.monotonic() - start > timeout:
                    raise AssertionError('Timeout: ' + window.status.text())
                if window.phase == 'error':
                    raise AssertionError(window.status.text())
                time.sleep(.02)
        try:
            wait_for(lambda: window.book is not None and window.shown_page == 0, 30)
            assert len(window.book['segments']) == 2
            window.toggle_play()
            wait_for(lambda: window.phase == 'playing', 90)
            assert window.index in window.cache
            assert window.player.source().toLocalFile().endswith('.wav')
            assert window.viewer.highlights
            wait_for(lambda: window.player.position() > 100, 15)
            window.toggle_play()
            assert not window.desired
            saved_offset = window.offset
            window.save_progress()
            assert window.store.load(window.book['hash'])['offset'] == saved_offset
            window.toggle_play()
            wait_for(lambda: window.index == 1, 20)
            wait_for(lambda: window.completed, 20)
            assert window.store.load(window.book['hash'])['completed'] == 1
            folder = window.folder
            window.close_book()
            app.processEvents()
            assert not list(folder.glob('*.wav'))
            print('PASS: extração + renderização + TTS + reprodução + destaque + pausa/retomada + avanço automático + fim + progresso + limpeza')
        finally:
            window.close()


if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
