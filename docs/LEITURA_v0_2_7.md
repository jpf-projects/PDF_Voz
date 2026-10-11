# Leitura 0.2.7 — alterações e validação

Atualização incremental sobre o layout 0.2.6 entregue nesta conversa. Sem novas dependências, mudança de modelo, threads, timers ou formato do banco. A preparação permanece local por CPU.

## Alterações

O controlador informa o tipo do próximo trecho ao processo de voz. O renderizador utiliza esse contexto somente na margem de encerramento da última parte sintetizada da unidade. Partes internas de uma mesma unidade não recebem a pausa estrutural de título ou transição.

A margem para título é 550 ms; transição prosa/código 420 ms; código 280 ms; ponto final em prosa 300 ms; dois-pontos 280 ms; vírgula/ponto e vírgula 180 ms; continuação sem pontuação 120 ms. A velocidade de reprodução comprime essas durações. Latência de troca de arquivo e sons do modelo também afetam o intervalo percebido. As regras não substituem a prosódia do sintetizador.

A divisão após expansão da fala procura finais de frase, depois limites de oração e, como alternativa, espaços. Protege abreviações e mantém o limite de 320 caracteres. Frases maiores que o limite ainda precisam ser divididas; palavras individuais maiores que o limite continuam subdivididas sem perda de caracteres. Não junta o livro em um único áudio nem aumenta o limite para obter contexto.

Números de código com zeros à esquerda passam a ter os dígitos explicitados. Em prosa, sequências numéricas com múltiplas vírgulas também recebem leitura explícita. Exemplo: `1,000,000` torna-se `1 vírgula zero zero zero vírgula zero zero zero`. Não se atribui automaticamente o significado de um milhão. Valores monetários e decimais com uma vírgula preservam as regras anteriores.

A revisão passa a `pausas-2:contexto-2`. A duração pode mudar; o progresso retoma no início do trecho salvo, mantendo a posição geral do livro. Os novos WAVs são gerados ao abrir/iniciar a leitura.

## Validação e limites

67 testes passaram em Linux/Qt offscreen, incluindo 9 novos para pausas estruturais, passagem do contexto ao job, proteção de fala fraca, números e divisão sem perda. Testes de renderização usam motor simulado e verificam WAV e encaminhamento dos parâmetros; não avaliam percepção de naturalidade. Os 58 testes existentes continuaram passando.

Não foi realizada síntese com o modelo Kokoro real neste ambiente nem medição de desempenho no equipamento do usuário. A classificação automática do PDF continua heurística. Não foi alterada a ordem de leitura do PDF, a segmentação inicial por blocos ou a troca de arquivos do player. As mudanças visam os problemas diagnosticados, sem garantir sua eliminação completa.

## Atualizar e comparar

Feche a versão 0.2.6. Copie estes arquivos para a raiz do projeto, preservando as pastas existentes. Não execute o instalador novamente. Abra ABRIR.bat e o mesmo PDF. Ouça a passagem de `resultará em:` até o título `1.6 - Linguagens formais e naturais`, usando a mesma voz Dora, modo Automático e velocidade 1,10× da gravação. Para uma comparação adicional, use 1,00× em ambas as versões.

Se persistir uma falha, registre a frase e o instante da gravação. Isso permite distinguir pronúncia do modelo, classificação incorreta e troca de trechos. Mensagem de commit sugerida: `Melhora pausas e leitura de números no PDF Voz 0.2.7`.
