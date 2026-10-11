import re
from pathlib import Path
import os
import time
import json
import shutil
import tempfile
from .speech import finish_audio
from .narration import prepare_spoken_text, spoken_chunks, NARRATION_REVISION


def select_portuguese(languages):
    # Retorna o código EXATO anunciado pela biblioteca, preservando caixa.
    for code in languages:
        if code.lower().replace("_", "-") == "pt-br":
            return code
    for code, name in languages.items():
        label = name.lower()
        if "brazil" in label or "brasil" in label:
            if code.lower().startswith("pt") or label.startswith("brazil"):
                return code
    raise RuntimeError("O eSpeak carregado não anunciou português brasileiro. "
                       "Envie logs/espeak_runtime.json e logs/ultimo_erro.txt. "
                       "Não foi selecionado outro idioma automaticamente.")


def prepare_espeak():
    import espeakng_loader
    from phonemizer.backend.espeak.wrapper import EspeakWrapper
    from phonemizer.backend import EspeakBackend
    library = espeakng_loader.get_library_path()
    data = Path(espeakng_loader.get_data_path())
    temporary = None
    # Bibliotecas nativas podem não resolver caminhos UTF-8 no Windows.
    # Copiamos apenas dados públicos de pronúncia; nunca PDFs nem textos.
    if os.name == "nt" and not str(data).isascii():
        bases = [os.environ.get("PUBLIC", ""), tempfile.gettempdir()]
        for base in bases:
            if not base or not base.isascii() or not Path(base).is_dir():
                continue
            try:
                target = Path(base) / "PDFVozPronuncia_0_2" / "espeak-ng-data"
                # Só reutiliza a cópia se origem/versão e arquivo principal coincidirem.
                import importlib.metadata
                signature = json.dumps([str(data), importlib.metadata.version('espeakng-loader'),
                                        (data / 'phontab').stat().st_mtime_ns])
                marker = target.parent / 'origem.json'
                if (not (target / 'phontab').is_file() or not marker.is_file()
                        or marker.read_text('utf-8') != signature):
                    shutil.copytree(data, target, dirs_exist_ok=True)
                    marker.write_text(signature, encoding='utf-8')
                data = target
                break
            except OSError:
                if temporary:
                    temporary.cleanup()
                temporary = None
        if not str(data).isascii():
            raise RuntimeError("Não foi possível preparar eSpeak num caminho sem acentos. "
                               "Envie logs/ultimo_erro.txt para ajustarmos o caminho.")
    # Escopo deste processo: evita usar uma DLL global incompatível.
    os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = library
    os.environ["PHONEMIZER_ESPEAK_DATA_PATH"] = str(data)
    EspeakWrapper.set_library(library)
    EspeakWrapper.set_data_path(str(data))
    languages = EspeakBackend.supported_languages()
    logs = Path(os.environ.get("PDFVOZ_DATA_ROOT", str(Path(__file__).resolve().parents[1]))) / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "espeak_runtime.json").write_text(json.dumps({
        "patch": "0.2.0", "biblioteca": library, "dados": str(data),
        "idiomas_disponiveis": languages, "dados_copiados_para_caminho_ascii": "PDFVozPronuncia_0_2" in str(data),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return library, str(data), select_portuguese(languages), temporary




class VoiceEngine:
    def __init__(self, model, voices, threads=2):
        # Opt-out ANTES do primeiro import: impede inicialização do uploader
        # nas plataformas que usam 1DS. API adicional cobre eventos de runtime.
        os.environ["ORT_DISABLE_TELEMETRY"] = "1"
        import onnxruntime as ort
        ort.disable_telemetry_events()
        from kokoro_onnx import Kokoro
        from kokoro_onnx.config import EspeakConfig
        start = time.perf_counter()
        library, data, self.language, self._espeak_temp = prepare_espeak()
        options = ort.SessionOptions()
        options.intra_op_num_threads = threads
        options.inter_op_num_threads = 1
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        session = ort.InferenceSession(str(model), sess_options=options,
                                       providers=["CPUExecutionProvider"])
        self.model = Kokoro.from_session(session, str(voices),
                                        espeak_config=EspeakConfig(lib_path=library, data_path=data))
        print(f"Pronúncia: português brasileiro ({self.language}).")
        self.load_seconds = time.perf_counter() - start

    def render(self, parts, voice, destination, progress=print):
        import numpy as np
        import soundfile as sf
        if voice not in self.model.get_voices():
            raise ValueError(f"Voz não encontrada: {voice}")
        destination = Path(destination)
        temporary = destination.with_suffix('.part.wav')
        rows = []
        start = time.perf_counter()
        writer = None
        expected_rate = None
        try:
            for index, part in enumerate(parts, 1):
                text = part['text'] if isinstance(part, dict) else part
                kind = part.get('kind', 'prose') if isinstance(part, dict) else 'prose'
                next_kind = part.get('next_kind') if isinstance(part, dict) else None
                if next_kind is None and index < len(parts):
                    following = parts[index]
                    next_kind = following.get('kind', 'prose') if isinstance(following, dict) else 'prose'
                spoken = prepare_spoken_text(text, kind)
                chunks = list(spoken_chunks(spoken))
                if not chunks:
                    raise ValueError(f'Texto vazio no trecho {index}.')
                generation, duration = 0., 0.
                for chunk_index, chunk in enumerate(chunks, 1):
                    progress(f'Gerando trecho {index}/{len(parts)}, parte {chunk_index}/{len(chunks)}...')
                    tick = time.perf_counter()
                    audio, rate = self.model.create(chunk, voice=voice, lang=self.language,
                                                    speed=1.0, trim=False)
                    generation += time.perf_counter() - tick
                    audio = np.asarray(audio).reshape(-1)
                    if rate <= 0 or len(audio) < rate * .05 or not np.isfinite(audio).all():
                        raise ValueError(f'Áudio inválido no trecho {index}.')
                    if float(np.max(np.abs(audio))) < 1e-5:
                        raise ValueError(f'Áudio silencioso no trecho {index}.')
                    audio = finish_audio(audio, rate, chunk, kind=kind,
                                         next_kind=next_kind, continuation=chunk_index < len(chunks))
                    if writer is None:
                        expected_rate = rate
                        writer = sf.SoundFile(str(temporary), 'w', samplerate=rate,
                                              channels=1, subtype='PCM_16')
                    if rate != expected_rate:
                        raise ValueError('Frequência do áudio mudou durante a geração.')
                    writer.write(audio)
                    duration += len(audio) / rate
                rows.append({'trecho': index, 'caracteres': len(text), 'caracteres_falados': len(spoken),
                             'kind': kind, 'geracao_s': round(generation, 4), 'audio_s': round(duration, 4)})
            if writer is None:
                raise ValueError('Texto vazio.')
            writer.close()
            writer = None
            os.replace(temporary, destination)
        finally:
            if writer:
                writer.close()
            temporary.unlink(missing_ok=True)
        duration = sum(row['audio_s'] for row in rows)
        synthesis = sum(row['geracao_s'] for row in rows)
        return {'voz': voice, 'idioma': 'pt-br', 'espeak_codigo': self.language,
                'patch_voz': NARRATION_REVISION, 'provider': 'CPUExecutionProvider',
                'carregamento_modelo_s': round(self.load_seconds, 4),
                'geracao_s': round(synthesis, 4), 'audio_s': round(duration, 4),
                'tempo_operacao_s': round(time.perf_counter() - start, 4),
                'rtf': round(synthesis / duration, 4), 'trechos': rows}
