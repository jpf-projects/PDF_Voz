import unittest
import numpy as np
from leitor.speech import finish_audio
from leitor.domain import segment_words, remap_progress

class SpeechTests(unittest.TestCase):
    def test_quiet_tail_preserved_and_sentence_pause_added(self):
        rate=1000
        raw=np.zeros(500,dtype=np.float32)
        raw[100:200]=.5
        raw[200:240]=.0002  # ending much quieter than the vowel
        out=finish_audio(raw,rate,'Uma frase.')
        np.testing.assert_array_equal(out[:180],raw[60:240])
        self.assertEqual(len(out)-180,300)
        self.assertTrue(np.all(out[-300:]==0))

    def test_clause_pause_and_invalid_audio(self):
        raw=np.ones(100,dtype=np.float32)*.1
        self.assertEqual(len(finish_audio(raw,1000,'Então,')),280)
        with self.assertRaises(ValueError):finish_audio(np.zeros(100),1000,'Teste.')
        with self.assertRaises(ValueError):finish_audio(np.array([np.nan]),1000,'Teste.')

    def test_pdf_block_continuation_and_progress_remap(self):
        words=[dict(text=t,page=0,line=i,box=[0,i,10,i+1],break_before=i==3)
               for i,t in enumerate(['Uma','frase','que','continua','na','linha.','Outra.'])]
        segments=segment_words(words)
        self.assertEqual([s['text'] for s in segments],['Uma frase que continua na linha.','Outra.'])
        old={'segments':[{'text':'Uma frase que'},{'text':'continua na linha.'},{'text':'Outra.'}]}
        progress={'index':1,'offset':400,'rate':1,'page':0,'zoom':1,'voice':'pf_dora','completed':False}
        mapped=remap_progress(progress,old,{'segments':segments})
        self.assertEqual((mapped['index'],mapped['offset']),(0,0))
        progress['index']=2
        self.assertEqual(remap_progress(progress,old,{'segments':segments})['index'],1)
