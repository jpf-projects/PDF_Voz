# Validação 0.2.4

46 testes unitários e de integração parcial aprovados nesta rodada. Inclui 25 testes existentes atualizados e 21 novos casos de narração, segmentação, recuperação, escrita WAV e processo PDF. O controlador usa Qt real offscreen e workers simulados; a extração/renderização também tem teste com processo PDF real.

Comando: `python -m unittest discover -v` com PySide6 6.10.2 disponível e `QT_QPA_PLATFORM=offscreen`.

Ambiente: Linux, Python 3.12; PyMuPDF 1.26.6 (o projeto fixa 1.26.7), soundfile 0.13.1. O modelo de teste devolve ondas artificiais: confirma escrita e acabamento de WAV, propagação de tipo e limites de chamadas, não a qualidade de pronúncia do Kokoro. Nenhum teste com saída física de áudio ou Windows foi executado. Os modelos não foram enviados nem baixados.

O antigo `tests/integration_smoke.py` continua disponível para teste com modelos reais, mas não integra a contagem acima e não foi executado nesta rodada. Notas 0.2.3 e anteriores são históricas.

## Relação com a auditoria

| Achado | Tratamento |
| --- | --- |
| A01 | Tipo propagado até a voz; opção de override por livro. |
| A02 | Scanner lexical contextual com operadores longos, strings e fallback. |
| A03 | Moeda/milhar tratados na prosa e decimais literais no código. |
| A04 | Fixtures/asserções compatíveis, aceitação de IDs de linha inteiros ou sequências. |
| A05 | Partes técnicas limitadas e limite pós-expansão em cada chamada TTS. |
| A06 | Revisão do normalizador integrada à identidade do áudio e modo por livro. |
| A07 | Detecção contínua de morte do PDF e prazo por falta de progresso. |
| A08 | Diagnóstico desktop, métricas recentes e freeze atualizado pelo instalador. |
| A09 | Motor compartilhado entre reader e leitor; CLI usa quatro threads. |
| A10 | Conversão explícita de dígitos Unicode no caminho de código. |
| A11 | Reuso dos dados de pronúncia, progresso sem gravações redundantes e índice por página. |
| A12 | Escolha manual de modo e remoção de histórico. Limitações documentadas. |

Otimizações adicionais, como levar toda a serialização de livros para fora da thread Qt, debounce de controles, compreensão avançada de layout e agrupamento técnico com timestamps, permanecem evoluções futuras. Não são anunciadas como implementadas. O teto de reserva é aproximado: um trecho em geração pode ultrapassá-lo. O limite de tempo de cinco minutos é por ausência de resposta/progresso, não um diagnóstico automático da causa.

## Critérios de teste no Windows

Conferir operadores com/sem espaços, valores monetários, decimais, título numerado, pausas e retomada. Testar seleção de voz/saída, geração pausada e limpeza. Ouvir o mesmo trecho antes/depois; comparar RTF no diagnóstico com os mesmos parâmetros. Nenhuma melhoria de velocidade ou naturalidade é presumida pelo simples sucesso dos testes.
