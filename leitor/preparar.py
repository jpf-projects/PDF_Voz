"""Prepara modelos sem carregar Qt, ONNX ou ferramentas antigas."""
from .assets import ensure_models


def main():
    ensure_models(allow_download=True)
    print('Modelos preparados.')


if __name__ == '__main__':
    main()
