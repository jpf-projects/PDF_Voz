"""Instala ou repara o leitor completo, sem modificar o Python global."""
import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def compatible(command):
    try:
        result = subprocess.run(command + ['-c',
            'import sys,struct,json;print(json.dumps([sys.version_info[:2],struct.calcsize("P")*8]))'],
            capture_output=True, text=True, timeout=20)
        return result.returncode == 0 and json.loads(result.stdout) == [[3, 12], 64]
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return False


def select_python():
    for command in ([sys.executable], ['py', '-3.12'], ['python']):
        if compatible(command):
            return command
    raise RuntimeError('Instale Python 3.12 de 64 bits e execute INSTALAR.bat novamente.\n'
                       'https://www.python.org/downloads/windows/')


def run(command, log):
    env = dict(os.environ, PYTHONUTF8='1', ORT_DISABLE_TELEMETRY='1')
    process = subprocess.Popen(command, cwd=ROOT, env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding='utf-8', errors='replace')
    try:
        for line in process.stdout:
            print(line, end='', flush=True)
            log.write(line)
            log.flush()
        if process.wait():
            raise RuntimeError('Etapa incompleta. Consulte logs/instalacao.txt e execute novamente.')
    except BaseException:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        raise
    finally:
        process.stdout.close()


def install(optional_tools=False):
    if platform.system() != 'Windows':
        raise RuntimeError('Este instalador requer Windows. Consulte README.md para desenvolvimento.')
    python = ROOT / '.venv' / 'Scripts' / 'python.exe'
    (ROOT / 'logs').mkdir(exist_ok=True)
    with (ROOT / 'logs' / 'instalacao.txt').open('w', encoding='utf-8') as log:
        if not python.exists():
            if (ROOT / '.venv').exists():
                raise RuntimeError('A pasta .venv existe, mas esta incompleta ou pertence a outro sistema. '
                                   'Renomeie-a para .venv_anterior e execute novamente. Nada foi apagado.')
            run(select_python() + ['-m', 'venv', str(ROOT / '.venv')], log)
        if not compatible([str(python)]):
            raise RuntimeError('A .venv existente precisa usar Python 3.12 de 64 bits. '
                               'Renomeie-a para .venv_anterior e execute novamente. Nada foi apagado.')
        requirements = 'dependencias/ferramentas.txt' if optional_tools else 'requirements.txt'
        print('Instalando dependencias do leitor...')
        run([str(python), '-m', 'pip', 'install', '--prefer-binary', '-r', requirements], log)
        run([str(python), '-m', 'pip', 'check'], log)
        # Model preparation no longer imports the legacy voice test or pypdf.
        run([str(python), '-m', 'leitor.preparar'], log)
        run([str(python), '-m', 'leitor.verificar_instalacao'], log)
        run([str(python), '-m', 'leitor.diagnostics'], log)
        freeze = subprocess.check_output([str(python), '-m', 'pip', 'freeze'], cwd=ROOT)
        (ROOT / 'logs' / 'dependencias_instaladas.txt').write_bytes(freeze)
    print('\nInstalacao concluida. Abra ABRIR.bat.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ferramentas', action='store_true', help='Inclui o teste de voz antigo e seus testes.')
    args = parser.parse_args()
    try:
        install(optional_tools=args.ferramentas)
    except KeyboardInterrupt:
        print('\nInstalacao interrompida. Execute INSTALAR.bat novamente para tentar concluir.')
        return 130
    except Exception as error:
        print(f'\nFalha: {error}')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
