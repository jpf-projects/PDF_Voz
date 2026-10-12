# PDF Voz 0.2.8.1 — marcadores de lista

Corrige o envio de marcadores tipográficos ao sintetizador, que podia narrar o círculo antes de cada tópico. Exemplos: “• à tarde”, “• à noite” e “• à medida que” são enviados como “à tarde”, “à noite” e “à medida que”.

- text_cleaning.py reconhece marcadores tipográficos destacados no início da linha. Não inclui hífen, asterisco, ponto comum nem produto escalar (·).
- pdf_service.py identifica o começo de itens em linhas não classificadas como código.
- domain.py separa os tópicos e mantém speech_text separado do texto exibido e das regiões de destaque.
- window.py envia speech_text para a voz, inclusive quando o usuário força o modo técnico. Trechos sem conteúdo falável são descartados ao abrir.
- narration.py também limpa marcadores iniciais em prosa e modo comum, e atualiza a revisão do áudio.
- __init__.py atualiza a versão. tests/test_list_markers.py cobre extração de um PDF real gerado para teste, preservação de símbolos e envio de fala no modo técnico.

A identificação é conservadora: depende dos caracteres e das linhas extraídos do PDF. Não retira globalmente símbolos de fórmulas ou strings de código. Caso um PDF classifique uma lista como código, ou extraia outro caractere para o marcador, pode ser necessário avaliar esse PDF.

## Atualizar

Feche o leitor e extraia o ZIP na raiz junto a ABRIR.bat, mesclando pastas e substituindo arquivos. O pacote cumulativo inclui 0.2.8 e o zoom 0.2.7.1 e exige uma instalação 0.2.7 ou posterior. Reabra o PDF para refazer a extração. Nenhuma dependência mudou. O trecho salvo reinicia do começo devido à revisão de áudio.

## Validação

79 testes automatizados aprovados em Linux com Qt offscreen. A extração de lista foi testada em PDF com fonte incorporada e marcador Unicode. A síntese usa modelo simulado nos testes; a conferência auditiva real permanece no Windows do usuário.
