"""Etapa A: teste local de voz, com menu de terminal e benchmark."""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import traceback
import uuid

from reader import VERSION
from reader.assets import ROOT, ensure_models
from reader.text import chunks, normalize, read_pdf_page

VOICES = {"1": "pf_dora", "2": "pm_alex", "3": "pm_santa"}


def load_sample(name="padrao.txt"):
    return (ROOT / "samples" / name).read_text("utf-8")


def diagnostics():
    packages = {}
    for name in ("kokoro-onnx", "onnxruntime", "numpy", "soundfile", "pypdf", "phonemizer", "espeakng-loader"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = "ausente"
    return {"aplicacao": VERSION, "python": platform.python_version(),
            "sistema": platform.system(), "arquitetura": platform.machine(),
            "pacotes": packages}


def run(text, voice, engine, open_audio=True):
    text = normalize(text)
    if not text:
        raise ValueError("Não há texto para narrar.")
    if len(text) > 6000:
        raise ValueError("Use até 6.000 caracteres nesta etapa de teste.")
    output = ROOT / "resultados"
    output.mkdir(exist_ok=True)
    key = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
    wav = output / (key + ".wav")
    result = engine.render(chunks(text), voice, wav)
    result.update(diagnostics())
    result["data_utc"] = datetime.now(timezone.utc).isoformat()
    result["arquivo_audio"] = wav.name
    (output / (key + ".json")).write_text(json.dumps(result, ensure_ascii=False, indent=2), "utf-8")
    print(f"\nÁudio: {result['audio_s']:.1f}s | Geração: {result['geracao_s']:.1f}s | RTF: {result['rtf']:.2f}")
    print("RTF abaixo de 1: geração mais rápida que a fala em 1x, nesta amostra.")
    print("Para 2x, seria necessário RTF abaixo de 0,5, com margem. Isso não garante um livro inteiro.")
    print(f"Resultado salvo em: {wav}")
    if open_audio and os.name == "nt":
        try:
            os.startfile(str(wav))
        except OSError:
            print("Abra o WAV manualmente na pasta resultados.")
    return result


def interactive(engine):
    while True:
        print("\nPDF Voz — teste 0.1 | Português | CPU")
        print("1. Texto padrão  2. Trecho do livro enviado  3. Página de um PDF  4. Arquivo TXT  0. Sair")
        option = input("Escolha [1]: ").strip() or "1"
        if option == "0":
            return
        try:
            if option == "1":
                text = load_sample()
            elif option == "2":
                text = load_sample("startup_amostra.txt")
            elif option == "3":
                path = input("Caminho do PDF (pode arrastar o arquivo para esta janela): ").strip().strip('"')
                page = int(input("Número da página física do PDF (começa em 1): "))
                text, total, truncated = read_pdf_page(path, page)
                print(f"Página {page} de {total}. Amostra limitada a 180 palavras: {'sim' if truncated else 'não'}.")
            elif option == "4":
                path = input("Caminho do TXT em UTF-8: ").strip().strip('"')
                text = Path(path).read_text("utf-8-sig")
            else:
                print("Escolha inválida.")
                continue
            print("\nTexto que será narrado:\n" + text)
            print("\n1. Dora  2. Alex  3. Santa")
            choice = input("Voz [1]: ").strip() or "1"
            if choice not in VOICES:
                raise ValueError("Escolha 1, 2 ou 3.")
            if input("Gerar este texto? [S/n]: ").strip().lower() == "n":
                continue
            run(text, VOICES[choice], engine)
        except (ValueError, OSError) as error:
            print(f"Não foi possível concluir: {error}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparar", action="store_true", help="Baixa apenas os modelos ausentes")
    parser.add_argument("--diagnostico", action="store_true")
    parser.add_argument("--texto", type=Path, help="TXT em UTF-8")
    parser.add_argument("--voz", choices=list(VOICES.values()), default="pf_dora")
    parser.add_argument("--sem-abrir", action="store_true")
    args = parser.parse_args()
    if args.diagnostico:
        print(json.dumps(diagnostics(), ensure_ascii=False, indent=2))
        return
    model, voices = ensure_models(allow_download=args.preparar)
    if args.preparar:
        print("Modelos preparados. Agora execute 2_TESTAR_VOZ.bat.")
        return
    from reader.engine import VoiceEngine
    print("Preparando voz no processador. Aguarde...")
    engine = VoiceEngine(model, voices, threads=2)
    print(f"Modelo carregado em {engine.load_seconds:.1f}s.")
    if args.texto:
        run(args.texto.read_text("utf-8-sig"), args.voz, engine, not args.sem_abrir)
    else:
        interactive(engine)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTeste interrompido. Downloads e WAVs parciais são descartados.")
        sys.exit(130)
    except Exception as error:
        logs = ROOT / "logs"
        logs.mkdir(exist_ok=True)
        (logs / "ultimo_erro.txt").write_text(traceback.format_exc(), "utf-8")
        print(f"\nFalha: {error}\nDetalhes em logs/ultimo_erro.txt. Envie esse arquivo se precisar de correção.")
        sys.exit(1)
