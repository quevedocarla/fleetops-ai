# Regras de Contratos

REGRA CONTR-001

Uma Ordem de Servico de instalacao somente pode ser processada
quando o contrato relacionado estiver com status ACTIVE.

Caso o contrato esteja INACTIVE, a Ordem de Servico deve permanecer
bloqueada ate que a situacao contratual seja regularizada.

O sistema nao deve realizar processamento automatico de instalacoes
associadas a contratos inativos.
