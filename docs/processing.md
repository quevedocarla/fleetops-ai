# Regras de Processamento de OS

REGRA OS-001

Ordens de Servico com fila em status PENDING ainda aguardam processamento.

REGRA OS-002

Ordens de Servico com fila em status ERROR devem ser analisadas antes
de qualquer tentativa de novo processamento.

O erro registrado na fila deve ser considerado durante o diagnostico.
