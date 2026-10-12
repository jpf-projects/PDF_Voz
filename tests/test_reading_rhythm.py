import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from leitor.narration import prepare_spoken_text as say, spoken_chunks
from leitor.speech import boundary_pause, finish_audio
from leitor.voice import VoiceEngine
from tests.test_voice_render import Model
from tests import test_controller as controller_tests


class RhythmTests(unittest.TestCase):
    def test_leading_zeros_and_commas_are_explicit(self):
        self.assertEqual(say('>>> 1,000,000','code'),
                         'Entrada no terminal: 1 vírgula zero zero zero vírgula zero zero zero')
        self.assertEqual(say('007','code'), 'zero zero sete')
        self.assertEqual(say('O Python interpreta 1,000,000 como uma sequência.'),
                         'O páiton interpreta 1 vírgula zero zero zero vírgula zero zero zero como uma sequência.')
        self.assertEqual(say('Valor 1,50 e R$ 1.000,00.'), 'Valor 1,50 e 1000 reais.')

    def test_sentence_boundary_is_preferred_and_text_preserved(self):
        text='Esta frase termina aqui. Outra explicação ocupa mais espaço e continua até o final.'
        parts=list(spoken_chunks(text,45))
        self.assertEqual(parts[0], 'Esta frase termina aqui.')
        self.assertEqual(' '.join(parts), text)
        self.assertTrue(all(len(x)<=45 for x in parts))

    def test_clause_boundary_is_preferred(self):
        text='Primeira parte bastante longa; segunda parte segue com mais palavras para terminar.'
        self.assertEqual(list(spoken_chunks(text,48))[0], 'Primeira parte bastante longa;')

    def test_abbreviation_is_not_sentence_boundary(self):
        text='Uma consulta com o Dr. Paulo acontece amanhã na clínica.'
        self.assertFalse(list(spoken_chunks(text,32))[0].endswith('Dr.'))

    def test_small_limits_and_long_tokens_never_lose_characters(self):
        for limit in (1,2,8,20,320):
            text='x'*650+' fim. Mais texto aqui.'
            chunks=list(spoken_chunks(text,limit))
            self.assertTrue(all(0<len(x)<=limit for x in chunks))
            self.assertEqual(''.join(chunks).replace(' ',''),text.replace(' ',''))

    def test_pauses_distinguish_structural_boundaries(self):
        self.assertEqual(boundary_pause('resultará em:', 'prose', 'code'), .42)
        self.assertEqual(boundary_pause('fecha parênteses', 'code', 'prose'), .42)
        self.assertEqual(boundary_pause('Título','heading','prose'),.55)
        self.assertEqual(boundary_pause('Acabou.','prose','heading'),.55)
        self.assertEqual(boundary_pause('Título longo','heading','prose',True),.12)
        self.assertEqual(boundary_pause('Uma frase.','prose','prose'),.30)

    def test_heading_preserves_quiet_speech_then_adds_margin(self):
        raw=np.zeros(500,dtype=np.float32);raw[100:200]=.5;raw[200:240]=.0002
        output=finish_audio(raw,1000,'Título','heading','prose')
        np.testing.assert_array_equal(output[:180],raw[60:240])
        self.assertEqual(len(output),180+550)

    def test_render_only_applies_next_kind_to_final_chunk_boundary(self):
        engine=VoiceEngine.__new__(VoiceEngine)
        engine.model=Model();engine.language='pt-br';engine.load_seconds=0
        with tempfile.TemporaryDirectory() as tmp, patch('leitor.voice.finish_audio', wraps=finish_audio) as finish:
            engine.render([{'text':'Uma frase. '*90,'kind':'prose','next_kind':'heading'}],
                          'pf_dora',Path(tmp)/'test.wav',lambda _:None)
            self.assertGreater(len(finish.call_args_list),1)
            self.assertTrue(all(c.kwargs['continuation'] for c in finish.call_args_list[:-1]))
            self.assertFalse(finish.call_args_list[-1].kwargs['continuation'])
            self.assertEqual(finish.call_args_list[-1].kwargs['next_kind'],'heading')


class RhythmControllerTests(unittest.TestCase):
    setUpClass = classmethod(controller_tests.ControllerTests.setUpClass.__func__)
    setUp = controller_tests.ControllerTests.setUp
    tearDown = controller_tests.ControllerTests.tearDown

    def test_job_carries_following_kind_and_respects_forced_mode(self):
        self.w.book['segments'][1]['kind']='heading'
        self.w.drive()
        self.assertEqual(self.w.tts.jobs[-1]['next_kind'],'heading')
        self.w.pending_audio=None
        self.w.narration_mode.blockSignals(True)
        self.w.narration_mode.setCurrentIndex(self.w.narration_mode.findData('common'))
        self.w.narration_mode.blockSignals(False)
        self.w.drive()
        self.assertEqual(self.w.tts.jobs[-1]['next_kind'],'common')
