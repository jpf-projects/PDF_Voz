"""Diagnóstico desktop sem importar bibliotecas nativas nem incluir livros/senhas."""
import importlib.metadata
import json
import platform
from . import VERSION
from .speech import AUDIO_REVISION


def diagnostics():
    packages = {}
    for name in ('PySide6','PyMuPDF','kokoro-onnx','onnxruntime','numpy','soundfile','phonemizer','espeakng-loader'):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = 'ausente'
    return {'aplicacao': VERSION, 'python': platform.python_version(),
            'sistema': platform.system(), 'arquitetura': platform.machine(),
            'pacotes': packages, 'threads_cpu': 4, 'provider': 'CPUExecutionProvider',
            'audio_revision': AUDIO_REVISION, 'modelo': 'kokoro-v1.0.onnx',
            'vozes': 'voices-v1.0.bin'}


if __name__ == '__main__':
    print(json.dumps(diagnostics(), ensure_ascii=False, indent=2))
