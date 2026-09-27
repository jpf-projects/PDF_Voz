"""Instala a interface no ambiente existente, sem baixar modelos."""
from pathlib import Path
import subprocess
import sys
import json

ROOT = Path(__file__).resolve().parent


def compatible(command):
    try:
        p = subprocess.run(command + ["-c", "import sys,struct,json;print(json.dumps([sys.version_info[:2],struct.calcsize('P')*8]))"],
                           capture_output=True, text=True, timeout=15)
        return p.returncode == 0 and json.loads(p.stdout) == [[3, 12], 64]
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return False


def main():
    env = ROOT / ".venv" / "Scripts" / "python.exe"
    if not env.exists():
        command = next((x for x in [["py", "-3.12"], [sys.executable], ["python"]] if compatible(x)), None)
        if not command:
            raise RuntimeError("Instale Python 3.12 x64 ou copie a atualização para a pasta do teste anterior.")
        subprocess.run(command + ["-m", "venv", str(ROOT / ".venv")], check=True)
    if not compatible([str(env)]):
        raise RuntimeError("O ambiente .venv precisa usar Python 3.12 x64. Envie a mensagem para ajuste.")
    (ROOT / "logs").mkdir(exist_ok=True)
    with (ROOT / "logs" / "instalacao_leitor.txt").open("w", encoding="utf-8") as log:
        process = subprocess.Popen([str(env), "-m", "pip", "install", "--prefer-binary", "-r", str(ROOT / "requirements_leitor.txt")],
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding="utf-8", errors="replace")
        for line in process.stdout:
            print(line, end="", flush=True)
            log.write(line)
        if process.wait():
            raise RuntimeError("Instalação incompleta. Veja logs/instalacao_leitor.txt.")
    print("\nInterface instalada. Execute 5_ABRIR_LEITOR.bat. Os modelos existentes serão reaproveitados.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"\nFalha: {error}")
        sys.exit(1)
