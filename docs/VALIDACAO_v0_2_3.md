# Validação 0.2.3

18 testes automatizados aprovados, incluindo preservação de final de fala fraco,
pausas de sentença/cláusula, rejeição de áudio inválido, continuação entre blocos e
remapeamento do progresso após mudança na segmentação.

Teste integrado aprovado: PDF sintético, síntese real com Kokoro, reprodução Qt,
pausa, retomada, avanço, conclusão, progresso e limpeza.

Ambiente Linux sem saída física de áudio. Não foi feita avaliação auditiva da
melhora nem validação das transições no Windows. A correção atua em causas
identificadas no código; a confirmação do sintoma relatado requer ouvir o mesmo
texto no notebook do usuário.

Não houve mudança de motor, modelos, dependências, número de threads ou controles.
As notas de versões anteriores permanecem como histórico; as regras atuais de
recorte e segmentação estão em README_LEITOR.md.
