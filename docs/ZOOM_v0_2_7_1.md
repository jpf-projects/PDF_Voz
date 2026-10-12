# Correção do controle de zoom — 0.2.7.1

Base: commit 8e127c2, versão 0.2.7 do GitHub.

Substituídas as setas nativas do campo de zoom por botões − e + com largura de 36 pixels, rótulos de acessibilidade e repetição ao manter pressionado. Campo editável, passo de 0,10 e limites de 0,50 a 2,50 preservados. O sinal valueChanged continua usando zoom_changed e a renderização existente. Sem alteração no áudio ou nas dependências.

A captura sugere problema de geometria/estilo do controle no Windows; a causa nativa não foi reproduzida neste ambiente Linux. Esta correção elimina o uso dessas setas no zoom.

Validação: 69 testes aprovados em Linux/Qt offscreen, incluindo clique de mouse nos novos botões, transformação do visualizador, pedido de renderização e limites do zoom. Conferir os botões no Windows após atualizar.

Feche o leitor e extraia estes arquivos na raiz da instalação 0.2.7, mesclando as pastas. Abra ABRIR.bat. Não reinstale dependências. Mensagem de commit sugerida: Corrige botões de zoom no PDF Voz 0.2.7.1.
