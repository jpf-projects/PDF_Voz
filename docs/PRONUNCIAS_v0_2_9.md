# PDF Voz 0.2.9 — base global e validação de pronúncias

## Entrega

- Dicionário global JSON com as quatro adaptações herdadas (Python, Linux, default e GCC). Estão ativas nos modos em que já eram usadas; o modo Comum não força essas adaptações técnicas.
- Três registros candidatos (colher, sede, gosto), desativados e sem grafia substituta inventada. Precisam de desambiguação antes de qualquer ativação.
- 18 frases de avaliação com categoria, objetivo, tratamento e referência. Os manuais orientam os fenômenos de teste; as frases de avaliação foram redigidas para o projeto. Não se trata de um corpus de pronúncias aprovado.
- Normalização contextual de pág./págs. antes de número, títulos como Dr./Dra. antes de nome com inicial maiúscula, horários no formato 14h30, kg e km após quantidade. Datas ambíguas e a unidade/variável m permanecem sem regra nova. Código classificado como código não passa por essas expansões.
- Tela Configurações → Testar pronúncia, com texto preparado editável, escolha de voz e comparação A/B. Não salva alterações no dicionário nem modifica o PDF.

## Fluxo e desempenho

O dicionário é validado e carregado uma vez por processo. A busca preserva acentos e usa termos literais completos, sem executar expressões fornecidas no JSON e sem substituições em cascata. Expressões mais longas têm prioridade. Caminhos, domínios e identificadores não devem receber substituições parciais. A normalização de prosa também preserva endereços e código explicitamente delimitado por crases.

Não há API, dependência nova nem modelo novo. No teste A/B, a geração do livro é encerrada, mantendo progresso e áudios já prontos. Um processo gera A e B em sequência. O motor do livro será recarregado ao retomar; isso pode exigir nova espera. O teste não roda inferência na thread da interface.

A original passa apenas pela limpeza de controles; B passa pela preparação selecionada, podendo ser editada. O sintetizador recebe cada versão exatamente uma vez, com a mesma voz e velocidade. As pausas de acabamento usam o mesmo tratamento de prosa nas duas versões para permitir comparação. Portanto, esta tela não reproduz todas as transições entre títulos/código de um livro.

Os WAVs são temporários. Ao fechar, o processo de voz é encerrado e os arquivos são removidos. Arquivos eventualmente bloqueados pelo Windows entram na limpeza posterior do leitor. Propostas de pronúncia não são persistidas pela tela.

## Estrutura dos dados

Cada entrada traz id, term, spoken, locale, category, modes, status, enabled, context, reference, phonetic_reference e validation. A referência fonética pode ser nula quando não foi verificada. A forma enviada ao motor não é considerada automaticamente uma transcrição fonética.

Estados:
- herdada: comportamento já existente, mantido por compatibilidade; não significa validação auditiva formal.
- candidata: proposta ou problema a avaliar; não pode ser ativado pelo carregador.
- aprovada: correção revisada que pode ser ativada pelo mantenedor após avaliação.

Somente o contexto palavra_completa está implementado para entradas ativas. Condições gramaticais ou semânticas ainda não estão implementadas. Registros ambíguos não podem ser habilitados mudando apenas uma flag.

O arquivo JSON fica em leitor/data/pronuncias_pt_br.json. Reinicie após editar. O conteúdo influencia a revisão do áudio, evitando reaproveitar deslocamentos temporais incompatíveis. Se estiver ausente ou inválido, o aplicativo registra aviso no log e usa a pronúncia original do motor, sem aplicar o dicionário. A janela do teste ainda permite experimentar manualmente.

## Fontes e limites

Tatiana Keller, Caderno didático de Fonética e Fonologia do Português, UFSM, 2019, arquivo enviado de 84 páginas: orientação principal para tonicidade, vogais, nasalidade, consoantes, hiatos e ligação entre palavras. Páginas de referência acompanham os casos.

Joseph Ghanime López e Valentim Fagim, Pronúncia do português passo a passo, 2025, recorte enviado de 20 páginas: apoio comparativo. A referência principal é portuguesa/europeia; não foram transpostas indiscriminadamente suas regras para o português brasileiro. O recorte não contém todos os capítulos citados no sumário.

Não foram importadas automaticamente transcrições fonéticas: a extração apresenta problemas com fontes de símbolos. Os materiais não fornecem uma solução pronta para expressividade. Os exemplos de normalização de horários, unidades e abreviações são regras de engenharia do projeto, não transcrições retiradas desses manuais.

## Validação auditiva no Windows

1. Atualize o programa e abra Configurações → Testar pronúncia.
2. Comece pelo caso de abreviações/horário e compare os dois textos antes de gerar.
3. Prepare e ouça A e B na mesma voz. Anote precisão, naturalidade e alguma perda de significado.
4. Use os casos linguísticos para identificar erros; A e B podem ser idênticos quando não há correção ativa.
5. Para experimentar uma hipótese, altere só o campo B e gere novamente.
6. Repita com contexto diferente e, antes de distribuir uma regra, com todas as vozes que ela pretende atender.

## Arquivos

Novos: leitor/pronunciation.py, leitor/normalization.py, leitor/pronunciation_dialog.py, leitor/data/pronuncias_pt_br.json, leitor/data/testes_pronuncia.json, testes de dicionário e diálogo, este guia.

Integração: narration.py utiliza o dicionário e normalização; voice.py e workers.py permitem comparar texto já preparado sem aplicar regras novamente; window.py abre o teste e pausa o leitor; __init__.py define 0.2.9. Documentação atualizada.

## Instalação e testes

Atualização cumulativa sobre 0.2.7 ou posterior: feche o leitor, extraia na raiz junto a ABRIR.bat, mescle as pastas e substitua os arquivos. Preserve ambiente, modelos e dados. Reabra o PDF; o trecho salvo poderá recomeçar do início devido à revisão do áudio.

92 testes automatizados aprovados no Linux com Qt offscreen. A interface também foi conferida em captura local. Testes de síntese usam modelo simulado. A qualidade auditiva, saída de som e comportamento nativo do Windows ainda precisam de validação no computador de uso.
