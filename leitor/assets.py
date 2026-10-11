import hashlib
import json
import os
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "models"
BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
FILES = {"kokoro-v1.0.onnx": 325532387, "voices-v1.0.bin": None}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(part)
    return digest.hexdigest()


def ensure_models(allow_download=False, progress=print):
    MODEL_DIR.mkdir(exist_ok=True)
    manifest_path = MODEL_DIR / "integridade.json"
    manifest = json.loads(manifest_path.read_text("utf-8")) if manifest_path.exists() else {}
    changed = False
    for name, size in FILES.items():
        path = MODEL_DIR / name
        if path.exists():
            digest = sha256(path)
            if name in manifest and manifest[name]["sha256"] != digest:
                raise ValueError(f"Arquivo alterado ou corrompido: models/{name}. Remova esse arquivo e prepare novamente.")
            if size and path.stat().st_size != size:
                raise ValueError(f"Tamanho inválido: models/{name}. Remova esse arquivo e prepare novamente.")
            if name not in manifest:
                manifest[name] = {"sha256": digest, "bytes": path.stat().st_size}
                changed = True
            continue
        if not allow_download:
            raise FileNotFoundError("Modelos ausentes. Execute INSTALAR.bat com internet.")
        progress(f"Baixando {name} do repositório público do Kokoro (nenhum PDF é enviado)...")
        temporary = path.with_suffix(path.suffix + ".part")
        try:
            request = urllib.request.Request(BASE + name, headers={"User-Agent": "PDFVozTeste/0.1"})
            with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as out:
                expected = int(response.headers.get("Content-Length") or 0)
                done, last = 0, -1
                while True:
                    data = response.read(1024 * 1024)
                    if not data:
                        break
                    out.write(data)
                    done += len(data)
                    bucket = done // (25 * 1024 * 1024)
                    if bucket != last:
                        progress(f"  {done / 1024**2:.0f} MiB recebidos")
                        last = bucket
                if done == 0 or (expected and expected != done) or (size and done != size):
                    raise ValueError("Download incompleto. Execute a instalação novamente.")
            os.replace(temporary, path)
            manifest[name] = {"sha256": sha256(path), "bytes": path.stat().st_size}
            changed = True
        finally:
            temporary.unlink(missing_ok=True)
    if changed:
        temp = manifest_path.with_suffix(".tmp")
        temp.write_text(json.dumps(manifest, indent=2), "utf-8")
        os.replace(temp, manifest_path)
    # Hash local detecta alterações futuras; não é uma assinatura do publicador.
    return MODEL_DIR / "kokoro-v1.0.onnx", MODEL_DIR / "voices-v1.0.bin"
