"""Instalação isolada. Não altera o Python global nem configurações do Windows."""
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def probe(command):
    try:
        result = subprocess.run(command + ["-c", "import sys,struct,json;print(json.dumps([sys.version_info[:2],struct.calcsize('P')*8]))"],
                                capture_output=True, text=True, timeout=20)
        return result.returncode == 0 and json.loads(result.stdout) == [[3, 12], 64]
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return False


def execute(command, log):
    process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    for line in process.stdout:
        print(line, end="", flush=True)
        log.write(line)
        log.flush()
    if process.wait():
        raise RuntimeError("Etapa de instalação falhou. Consulte logs/instalacao.txt.")


def main():
    if platform.system() != "Windows":
        raise RuntimeError("Este instalador foi preparado para Windows. Consulte README.md para execução manual.")
    candidates = [[sys.executable], ["py", "-3.12"], ["python"]]
    command = next((cmd for cmd in candidates if probe(cmd)), None)
    if not command:
        raise RuntimeError("É necessário Python 3.12 de 64 bits para este pacote.\n"
                           "Você pode instalar essa versão em paralelo, sem remover a atual.\n"
                           "Consulte https://www.python.org/downloads/windows/ e execute novamente.")
    (ROOT / "logs").mkdir(exist_ok=True)
    env_python = ROOT / ".venv" / "Scripts" / "python.exe"
    with (ROOT / "logs" / "instalacao.txt").open("w", encoding="utf-8") as log:
        if not env_python.exists():
            execute(command + ["-m", "venv", str(ROOT / ".venv")], log)
        if not probe([str(env_python)]):
            raise RuntimeError("A pasta .venv usa outra versão. Renomeie essa pasta e tente novamente.")
        execute([str(env_python), "-m", "pip", "install", "--prefer-binary", "-r", "requirements.txt"], log)
        freeze = subprocess.check_output([str(env_python), "-m", "pip", "freeze"], cwd=ROOT)
        (ROOT / "logs" / "dependencias_instaladas.txt").write_bytes(freeze)
        execute([str(env_python), "-u", "app.py", "--preparar"], log)
    print("\nInstalação concluída. Abra 2_TESTAR_VOZ.bat.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Instalação interrompida. Pode executar novamente.")
        sys.exit(130)
    except Exception as error:
        print("\n" + str(error))
        sys.exit(1)
