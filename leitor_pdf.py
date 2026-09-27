"""Entrada desktop. Imports Qt somente no processo principal."""
import multiprocessing
import os
import sys


def main():
    os.environ["ORT_DISABLE_TELEMETRY"] = "1"
    from pathlib import Path
    import logging
    from logging.handlers import RotatingFileHandler
    from PySide6.QtCore import QStandardPaths, QLockFile, QUrl
    from PySide6.QtWidgets import QApplication, QMessageBox
    from leitor.window import MainWindow
    from leitor.storage import clean_sessions
    app = QApplication(sys.argv)
    app.setApplicationName("PDFVoz")
    app.setOrganizationName("PDFVozLocal")
    root = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation))
    root.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(root / "aplicacao.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        QMessageBox.information(None, "PDF Voz", "O leitor já está aberto. Use a janela existente.")
        return 0
    (root / "logs").mkdir(exist_ok=True)
    os.environ["PDFVOZ_DATA_ROOT"] = str(root)
    handler = RotatingFileHandler(root / "logs" / "leitor.log", maxBytes=1024 * 1024, backupCount=2, encoding="utf-8")
    logging.basicConfig(level=logging.INFO, handlers=[handler], format="%(asctime)s %(levelname)s %(message)s")
    def exception_hook(kind, value, tb):
        logging.error("Falha inesperada", exc_info=(kind, value, tb))
        QMessageBox.critical(None, "Falha no leitor", f"{value}\n\nDetalhes na pasta de diagnóstico, menu Arquivo.")
    sys.excepthook = exception_hook
    window = MainWindow(root)
    screen = app.primaryScreen().availableGeometry()
    window.resize(min(1160, int(screen.width() * .95)), min(800, int(screen.height() * .92)))
    window.show()
    result = app.exec()
    window.player.setSource(QUrl())
    app.processEvents()
    clean_sessions(root / "audio")
    lock.unlock()
    return result


if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.exit(main())
