# Troubleshooting

Quando uma Ordem de Servico estiver bloqueada:

1. Verificar o status do contrato.
2. Verificar a ultima fila de processamento.
3. Verificar a mensagem de erro da fila.
4. Consultar as regras aplicaveis ao tipo de Ordem de Servico.

Contratos inativos devem ser regularizados antes do processamento
de uma Ordem de Servico de instalacao.

## Diagnóstico de erro de processamento de OS

Quando uma Ordem de Serviço apresentar erro de processamento,
o troubleshooting deve começar pela análise dos dados operacionais
da OS e da fila de processamento.

Verifique:

- status atual da OS;
- status da fila de processamento;
- mensagem de erro registrada na fila;
- situação do contrato relacionado;
- regra operacional que pode estar impedindo o processamento.

Uma OS com erro de processamento deve ser diagnosticada antes
de qualquer tentativa de correção ou novo processamento.
