# Validação da versão 0.2

Data: 26/09/2026. Ambiente de desenvolvimento Linux x64 / Python 3.12. Windows do usuário ainda precisa de teste.

## Executado

- Dez testes automatizados de domínio/controlador aprovados: reserva contígua e velocidade; preservação de palavras/regiões entre páginas; progresso independente da limpeza; PDF rotacionado/renderização; PDF com senha sem persistência da senha; pausa durante buffer; descarte de geração antiga após salto; fim com menos de 60 segundos; fechamento com limpeza e progresso; limite de 60 segundos e pausa durante carregamento.
- Teste integrado com processos reais spawn, PDF sintético, Kokoro/ONNX e voz Dora: extração, renderização, WAVs válidos, carregamento e avanço da posição no QMediaPlayer, destaque, pausa/retomada, avanço automático entre dois trechos, conclusão e limpeza aprovados.
- O ambiente não tem dispositivo de som. A validação integrada acompanha decodificação, posição e estados; não é uma avaliação auditiva nem comprovação de saída nos alto-falantes do Windows.
- Extração do arquivo A Startup Enxuta enviado: 210 páginas e 4.864 trechos na versão de extração 1. Página física 15 renderizada com destaque correspondente e interface revisada visualmente. Isso não é auditoria de cada frase do livro.
- Dependências resolvidas pelo pip para Windows amd64 / Python 3.12 com pacotes binários disponíveis; versões principais e transitivas fixadas. Os BATs e DLLs não foram executados no Windows neste ambiente.
- Código verificado por compilação Python e ZIP conferido antes da entrega.

## Ainda depende do computador alvo

Saída audível no Windows, estabilidade por leitura longa, pausas entre arquivos, desempenho real da geração por sentença, quantidade de RAM usada, compensação de tonalidade do backend, preparação dos dados eSpeak em caminhos Windows com acentos e exclusão de arquivos que o backend mantenha abertos temporariamente.

## Política de não prometer desempenho

Reserva de 60 segundos mede áudio pronto e não cronometra uma espera fixa. Trechos longos ou fim do livro mudam o momento de iniciar. Não prometemos geração em tempo real no Ryzen 5 3500U. Ao esgotar a reserva, a interface volta à preparação e retoma quando houver áudio suficiente.

## Diagnóstico

O menu Arquivo abre o diretório de dados. O log registra índice/duração/tempo de geração e exceções, sem copiar intencionalmente o texto narrado. Caminhos locais podem aparecer. Não há envio automático de logs. A instalação registra seu próprio log na pasta do projeto.
