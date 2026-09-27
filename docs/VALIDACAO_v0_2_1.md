# Validação 0.2.1 — 26/09/2026

- 15 testes automatizados aprovados: buffer, pausa, saltos, descarte de resultados antigos, limpeza, progresso, PDF protegido/rotacionado, troca de voz e persistência, início antecipado e roteamento simulado de dispositivos.
- Teste integrado aprovado com processos reais: extração PDF, renderização, síntese, decodificação/reprodução no Qt, avanço automático, pausa/continuação, conclusão e limpeza.
- Síntese real validada para pf_dora, pm_alex e pm_santa com os modelos existentes e frase sintética. Não foi feita avaliação humana de qualidade de pronúncia das duas novas vozes.
- Interface revisada visualmente em 1100 × 720.
- Ambiente de teste Linux sem dispositivo físico de som: testes de dispositivo usaram simulação; áudio audível, mixer, teclas de volume e conexão/desconexão de fone no Windows não foram validados aqui.
- Nenhuma alegação de ganho de velocidade de inferência: a mudança reduz a reserva inicial de 60 para 30 s, configurável para 15/30/60 s.
- Banco antigo migra adicionando identidade da voz ao progresso, preservando os registros anteriores como Dora.

Referências oficiais consultadas para os controles implementados:
- https://doc.qt.io/qtforpython-6/PySide6/QtMultimedia/QMediaDevices.html
- https://doc.qt.io/qtforpython-6/PySide6/QtMultimedia/QAudioOutput.html

A documentação de arquitetura e validação v0.2 permanece como registro da versão anterior; os ajustes de controles e reserva acima substituem suas descrições de voz fixa e reserva fixa.
