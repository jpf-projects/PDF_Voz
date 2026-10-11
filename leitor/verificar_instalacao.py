"""Verifica imports nativos e dados de pronúncia; não gera áudio nem abre PDFs."""

def main():
    import os
    os.environ['ORT_DISABLE_TELEMETRY'] = '1'
    import pymupdf
    import numpy
    import soundfile
    import onnxruntime as ort
    ort.disable_telemetry_events()
    from kokoro_onnx import Kokoro
    from PySide6 import QtCore, QtGui, QtWidgets, QtMultimedia
    from .voice import prepare_espeak
    from .window import MainWindow
    if 'CPUExecutionProvider' not in ort.get_available_providers():
        raise RuntimeError('ONNX Runtime nao anunciou o processamento por CPU.')
    _, _, language, temporary = prepare_espeak()
    if temporary:
        temporary.cleanup()
    print(f'Bibliotecas carregadas e pronuncia {language} disponivel.')
    print('A reproducao em fones/alto-falantes deve ser conferida ao abrir o leitor.')


if __name__ == '__main__':
    main()
