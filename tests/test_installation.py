"""Contrato do instalador sem rede, sem pip real e sem alterar o ambiente."""
import importlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import instalar
from leitor import assets


class InstallationTests(unittest.TestCase):
    def test_probe_requires_python_312_64_bits(self):
        for data, expected in [([[3, 12], 64], True), ([[3, 11], 64], False),
                               ([[3, 12], 32], False)]:
            with self.subTest(data=data), patch('instalar.subprocess.run',
                    return_value=subprocess.CompletedProcess([], 0, json.dumps(data))):
                self.assertEqual(instalar.compatible(['python']), expected)
        with patch('instalar.subprocess.run', side_effect=FileNotFoundError):
            self.assertFalse(instalar.compatible(['python']))

    def exercise(self, existing=False, optional=False, fail=False):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            if existing:
                python = root / '.venv/Scripts/python.exe'
                python.parent.mkdir(parents=True)
                python.touch()
            model = root / 'models/keep.bin'
            model.parent.mkdir()
            model.write_bytes(b'keep')
            commands = []
            def run(command, log):
                commands.append(command)
                if fail and 'pip' in command:
                    raise RuntimeError('pip falhou')
            with patch.object(instalar, 'ROOT', root), \
                 patch('instalar.platform.system', return_value='Windows'), \
                 patch.object(instalar, 'compatible', return_value=True), \
                 patch.object(instalar, 'select_python', return_value=['py', '-3.12']), \
                 patch.object(instalar, 'run', side_effect=run), \
                 patch('instalar.subprocess.check_output', return_value=b'package==1\n'):
                if fail:
                    with self.assertRaisesRegex(RuntimeError, 'pip falhou'):
                        instalar.install(optional)
                else:
                    instalar.install(optional)
                    self.assertTrue((root / 'logs/dependencias_instaladas.txt').exists())
            self.assertEqual(model.read_bytes(), b'keep')
            return commands

    def test_fresh_install_orders_environment_dependencies_models_check(self):
        commands = self.exercise()
        self.assertIn('venv', commands[0])
        self.assertEqual(commands[1][-1], 'requirements.txt')
        self.assertEqual(commands[2][-2:], ['pip', 'check'])
        self.assertEqual(commands[3][-1], 'leitor.preparar')
        self.assertEqual(commands[4][-1], 'leitor.verificar_instalacao')
        self.assertFalse(any('app.py' in cmd for cmd in commands))

    def test_update_reuses_existing_environment(self):
        commands = self.exercise(existing=True)
        self.assertFalse(any('venv' in cmd for cmd in commands))
        self.assertEqual(commands[0][-1], 'requirements.txt')

    def test_optional_dependencies_are_explicit(self):
        commands = self.exercise(optional=True)
        self.assertEqual(commands[1][-1], 'dependencias/ferramentas.txt')

    def test_failure_stops_before_downloading_models(self):
        commands = self.exercise(fail=True)
        self.assertFalse(any('leitor.preparar' in cmd for cmd in commands))

    def test_existing_models_are_not_downloaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'model.onnx').write_bytes(b'abc')
            with patch.object(assets, 'MODEL_DIR', root), \
                 patch.object(assets, 'FILES', {'model.onnx': 3}), \
                 patch('leitor.assets.urllib.request.urlopen') as download:
                assets.ensure_models(allow_download=True)
                assets.ensure_models(allow_download=True)
                download.assert_not_called()
                self.assertEqual((root / 'model.onnx').read_bytes(), b'abc')

    def test_incomplete_download_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            response = io.BytesIO(b'a')
            response.headers = {'Content-Length': '3'}
            root = Path(tmp)
            with patch.object(assets, 'MODEL_DIR', root), \
                 patch.object(assets, 'FILES', {'model.onnx': 3}), \
                 patch('leitor.assets.urllib.request.urlopen', return_value=response):
                with self.assertRaisesRegex(ValueError, 'incompleto'):
                    assets.ensure_models(allow_download=True, progress=lambda _: None)
            self.assertFalse((root / 'model.onnx').exists())
            self.assertFalse((root / 'model.onnx.part').exists())

    def test_legacy_models_module_uses_same_function(self):
        from reader.assets import ensure_models
        self.assertIs(ensure_models, assets.ensure_models)

    def test_prepare_does_not_depend_on_legacy_test(self):
        import sys
        code = ('import sys; import leitor.preparar; '
                'assert "ferramentas.testar_voz" not in sys.modules; '
                'assert "pypdf" not in sys.modules; '
                'assert "PySide6" not in sys.modules')
        subprocess.run([sys.executable, '-c', code], check=True)
