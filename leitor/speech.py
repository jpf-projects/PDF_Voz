"""Conserva as extremidades da fala e recompõe pausas entre arquivos."""
import re
from .narration import NARRATION_REVISION
AUDIO_REVISION = 'pausas-1:' + NARRATION_REVISION


def finish_audio(audio, rate, text):
    import numpy as np
    audio = np.asarray(audio, dtype=np.float32).reshape(-1)
    if rate <= 0 or not len(audio) or not np.isfinite(audio).all():
        raise ValueError('Áudio inválido.')
    peak = float(np.max(np.abs(audio)))
    if peak < 1e-5:
        raise ValueError('Áudio silencioso.')
    # Limiar conservador: -80 dB em relação ao pico, com margem de proteção.
    active = np.flatnonzero(np.abs(audio) > max(peak * 1e-4, 1e-7))
    clean = text.rstrip().rstrip('\"”’\')]}')
    if re.search(r'[.!?…]$', clean):
        pause = .30
    elif re.search(r'[,;:]$', clean):
        pause = .18
    else:
        pause = .10
    start = max(0, int(active[0]) - round(rate * .04))
    # Mantém ao menos 120 ms após o último som detectado; não altera o miolo.
    end = int(active[-1]) + 1 + round(rate * max(.12, pause))
    result = audio[start:min(end, len(audio))].copy()
    if end > len(audio):
        result = np.pad(result, (0, end - len(audio)))
    return result
