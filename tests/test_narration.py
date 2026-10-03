import unittest
from leitor.narration import prepare_spoken_text as say, spoken_chunks
from leitor.domain import segment_words


class NarrationTests(unittest.TestCase):
    def test_spacing_does_not_change_operators(self):
        self.assertEqual(say('miles*1.61','code'), say('miles * 1.61','code'))
        self.assertEqual(say('x=-2','code'), 'x recebe menos 2')
        self.assertEqual(say('2**3','code'), '2 elevado a 3')
        self.assertEqual(say('10//2','code'), '10 dividido por, parte inteira 2')
        self.assertEqual(say('x>=2','code'), 'x maior ou igual a 2')
        self.assertEqual(say('x>2','code'), 'x maior que 2')

    def test_money_and_decimal_are_contextual(self):
        self.assertEqual(say('R$ 1.000,00'), '1000 reais')
        self.assertEqual(say('R$ 1,01'), '1 real e 1 centavo')
        self.assertEqual(say('R$ 2.500,35'), '2500 reais e 35 centavos')
        self.assertEqual(say('1.000','code'), '1 ponto zero zero zero')
        self.assertEqual(say('1.000 pessoas'), '1000 pessoas')
        self.assertEqual(say('42.182','code'), '42 ponto um oito dois')

    def test_unicode_digits_do_not_crash(self):
        self.assertEqual(say('٣.١٤','code'), '3 ponto um quatro')
        self.assertEqual(say('٣.١٤','prose'), '٣.١٤')

    def test_heading_version_and_prose_hyphen(self):
        self.assertEqual(say('2.4 - Modo script','heading'), '2 ponto 4: Modo script')
        self.assertEqual(say('Python 3.4.0'), 'páiton versão 3 ponto 4 ponto 0')
        self.assertEqual(say('guarda-chuva - explicação'), 'guarda-chuva - explicação')

    def test_strings_and_incomplete_code_preserved(self):
        string = say('x="a*b=2"','code')
        self.assertIn('asterisco',string)
        self.assertNotIn('vezes',string)
        self.assertIn('sinal de igual',string)
        self.assertIn('abre parênteses',say('print(','code'))
        self.assertIn('Comentário: x=2',say('# x=2','code'))

    def test_prompt_scientific_number_and_members(self):
        self.assertEqual(say('>>> x=-1.2e-3','code'), 'Entrada no terminal: x recebe menos 1 ponto dois vezes dez elevado a menos 3')
        self.assertEqual(say('obj.metodo()','code'), 'obj ponto metodo abre parênteses fecha parênteses')

    def test_expanded_chunks_are_bounded_and_lossless(self):
        text = say('x=' + '+'.join(['1.23456789']*60),'code')
        chunks = list(spoken_chunks(text))
        self.assertTrue(all(len(c)<=320 for c in chunks))
        self.assertEqual(' '.join(chunks),text)
        giant = 'a'*1000
        self.assertEqual(''.join(spoken_chunks(giant)),giant)

    def test_technical_line_split_does_not_repeat_full_line(self):
        text = '>>> ' + ' + '.join(['variavel']*80)
        words = []
        for i,t in enumerate(text.split()):
            words.append(dict(text=t,page=0,line=(0,0),box=[i,0,i+1,10],kind='code',line_text=text))
        parts = segment_words(words, max_chars=120)
        self.assertGreater(len(parts),1)
        self.assertTrue(all(len(s['text'])<=120 for s in parts))
        self.assertEqual(''.join(s['text'] for s in parts),text)
        self.assertEqual(sum(s['source_word_count'] for s in parts),len(words))
        self.assertTrue(all(s['regions'] for s in parts))
        self.assertEqual([s['id'] for s in parts],list(range(len(parts))))

    def test_one_huge_literal_has_explicit_fallback(self):
        text='"'+'a'*900+'"'
        word=dict(text=text,page=0,line=(0,0),box=[0,0,100,10],kind='code',line_text=text)
        parts=segment_words([word],max_chars=120)
        self.assertEqual(''.join(s['text'] for s in parts),text)
        self.assertTrue(all(s['kind']=='code_literal' for s in parts))
        self.assertTrue(all(len(s['text'])<=120 for s in parts))
        self.assertEqual(sum(s['source_word_count'] for s in parts),1)
