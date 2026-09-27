# Validação da entrega 0.1

Executado em Linux/Python 3.12, em 26/09/2026. Não é benchmark do Ryzen informado.

- 3 testes automatizados aprovados: preservação do texto ao dividir blocos; rejeição de palavra excessiva sem truncamento silencioso; PDF vazio e índice fora dos limites.
- Código Python compilado sem erros de sintaxe.
- Dependências instaladas no ambiente isolado Linux.
- Resolução de todas as dependências para Windows amd64/Python 3.12 aprovada pelo pip em dry-run, com wheels disponíveis. Isso não executa DLLs no Windows nem valida os scripts BAT.
- Modelo e vozes baixados do release público; síntese real em CPU com Dora e lang=pt-br concluída usando o texto original samples/padrao.txt.
- O runtime tentou telemetria na primeira tentativa; a revisão automática bloqueou essa ação. A versão entregue usa opt-out antes do import e desativação pela API. O novo teste concluiu depois dessa correção.
- Áudio PCM16 mono gerado: aproximadamente 39.9 segundos; geração de 24.9 segundos; RTF 0.62 neste ambiente.
- Exemplo do teste incluído em samples/exemplo_dora_linux.wav; o JSON está em docs/benchmark_linux.json.

Não validado: qualidade perceptiva por escuta humana, instalação/execução no Windows, desempenho no Ryzen 5 3500U, vozes Alex e Santa, funcionamento offline verificado por captura de rede, reprodução pelo player padrão do usuário. A verificação de amplitude não detecta palavras omitidas nem garante pronúncia.

A implementação nesta entrega é um teste de voz. A medição no computador alvo decide o próximo ajuste; biblioteca e leitor visual ainda serão desenvolvidos.
