# Layout 0.2.6 — alterações e validação

Base: commit `5f672d4` do GitHub, versão 0.2.5 confirmada pelo usuário no Windows.

## Alterações

- Painel lateral recolhível pelo botão ou Ctrl+B, com visibilidade persistida.
- Título e ações principais no topo; navegação de página e zoom em uma linha própria.
- Reprodução, velocidade e volume em uma barra inferior única.
- Configurações agrupadas em QDialog não modal, criado uma vez e reutilizado.
- Fechar livro no menu Arquivo; limpeza de áudios nas configurações.
- Reserva de áudio em faixa fina, com informação textual separada.
- Estilo estático em `leitor/theme.py`, sem fontes externas, animações, sombras ou novas dependências.

A interface usa os mesmos controles e sinais do motor. Não foram alterados geração de voz, processos, intervalos dos timers, segmentação, modelos ou formato do progresso. A única preferência nova é a visibilidade do painel. A revisão do áudio permanece igual.

## Validação

58 testes aprovados em Linux/Qt offscreen: 55 existentes e 3 novos para verificar painel lateral, reutilização da janela não modal e espaço de leitura em janela pequena. Abrir configurações e alternar o painel não solicitam nova página nem síntese nesses testes.

Inspeção visual realizada em 1100 × 740 e 850 × 600, além da janela de configurações. Nenhuma nova imagem de página é solicitada pela simples mudança de layout; Qt ajusta a área de exibição. Não foi medido desempenho de síntese nem consumo de RAM no Windows. A ausência de novas dependências e efeitos reduz o risco de sobrecarga, mas não representa garantia quantitativa de impacto zero.

## Aplicar

Com o leitor fechado, mescle os arquivos deste pacote na raiz da instalação 0.2.5. Preserve todos os arquivos não incluídos. Execute ABRIR.bat. Não reinstale dependências. Confira painel, configurações, saída de áudio e pausa/retomada no Windows antes do commit.

Mensagem sugerida: `Atualiza layout do PDF Voz para 0.2.6`.

Este pacote não publica alterações no GitHub e não restaura os atalhos antigos excluídos.
