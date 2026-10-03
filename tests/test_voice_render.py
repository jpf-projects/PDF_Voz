import tempfile
import unittest
from pathlib import Path
import numpy as np
import soundfile as sf
from leitor.voice import VoiceEngine


class Model:
    def __init__(self): self.calls=[]
    def get_voices(self): return ['pf_dora']
    def create(self, text, **kwargs):
        self.calls.append(text)
        return np.sin(np.arange(2400)*.1).astype('float32')*.1, 24000


class VoiceRenderTests(unittest.TestCase):
    def test_context_expansion_is_chunked_and_wav_atomic(self):
        engine=VoiceEngine.__new__(VoiceEngine)
        engine.model=Model();engine.language='pt-br';engine.load_seconds=0
        text='x='+'+'.join(['1.2345']*60)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'audio.wav'
            metrics=engine.render([{'text':text,'kind':'code'}],'pf_dora',path,lambda _:None)
            self.assertGreater(len(engine.model.calls),1)
            self.assertTrue(all(len(t)<=320 for t in engine.model.calls))
            self.assertIn('recebe',engine.model.calls[0])
            self.assertNotIn('+',' '.join(engine.model.calls))
            self.assertFalse(path.with_suffix('.part.wav').exists())
            audio,rate=sf.read(path)
            self.assertAlmostEqual(len(audio)/rate,metrics['audio_s'],places=3)
            self.assertEqual(metrics['trechos'][0]['kind'],'code')

    def test_failure_removes_partial_wav(self):
        engine=VoiceEngine.__new__(VoiceEngine)
        model=Model();engine.model=model;engine.language='pt-br';engine.load_seconds=0
        original=model.create
        def create(text,**kwargs):
            if model.calls: raise RuntimeError('Falha simulada')
            return original(text,**kwargs)
        model.create=create
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'audio.wav'
            with self.assertRaises(RuntimeError):
                engine.render(['Uma frase. '*100],'pf_dora',path,lambda _:None)
            self.assertFalse(path.exists())
            self.assertFalse(path.with_suffix('.part.wav').exists())
