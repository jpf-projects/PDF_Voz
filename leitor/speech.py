"""Conserva as extremidades da fala e recompõe pausas entre arquivos."""
import re
from .narration import NARRATION_REVISION
AUDIO_REVISION = 'pausas-2:' + NARRATION_REVISION


def boundary_pause(text, kind='prose', next_kind=None, continuation=False):
    """Margem final em segundos de áudio; não depende da velocidade do player."""
    clean = text.rstrip().rstrip('"”’\')]}')
    if re.search(r'[.!?…]$', clean):
        pause = .30
    elif clean.endswith(':'):
        pause = .28
    elif re.search(r'[,;]$', clean):
        pause = .18
    else:
        pause = .12
    # Partes da mesma unidade não recebem pausa de título/transição.
    if continuation:
        return pause
    if kind == 'heading' or next_kind == 'heading':
        return max(pause, .55)
    technical = kind in ('code', 'code_literal')
    next_technical = next_kind in ('code', 'code_literal')
    if next_kind is not None and technical != next_technical:
        return max(pause, .42)
    if technical:
        return max(pause, .28)
    return pause


def finish_audio(audio, rate, text, kind='prose', next_kind=None, continuation=False):
    import numpy as np
    audio = np.asarray(audio, dtype=np.float32).reshape(-1)
    if rate <= 0 or not len(audio) or not np.isfinite(audio).all():
        raise ValueError('Áudio inválido.')
    peak = float(np.max(np.abs(audio)))
    if peak < 1e-5:
        raise ValueError('Áudio silencioso.')
    # Limiar conservador: -80 dB em relação ao pico, com margem de proteção.
    active = np.flatnonzero(np.abs(audio) > max(peak * 1e-4, 1e-7))
    pause = boundary_pause(text, kind, next_kind, continuation)
    start = max(0, int(active[0]) - round(rate * .04))
    # Mantém ao menos 120 ms após o último som detectado; não altera o miolo.
    end = int(active[-1]) + 1 + round(rate * max(.12, pause))
    result = audio[start:min(end, len(audio))].copy()
    if end > len(audio):
        result = np.pad(result, (0, end - len(audio)))
    return result
