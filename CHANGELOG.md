# Patch Notes - Zabbix UPS Monitoring (PPC/Intelbras)

## [1.1.0] - 2026-03-18

### ✨ Novas Funcionalidades
- **Monitoramento Dinâmico de Bateria**: Adicionado o item "Tensão Nominal das Baterias (Rating)" via SNMP (OID `.1.3.6.1.4.1.935.1.1.1.8.8.7.0`).
- **Trigger de Falha Iminente**: Nova trigger inteligente que compara a Tensão Atual vs Tensão Nominal (Rating) do hardware.
- **Caso de Uso Real**: Adicionada seção no README descrevendo o sucesso na detecção preventiva de falha de bateria.

### 🚀 Melhorias Técnicas
- **Lógica de Disparo**: A trigger de voltagem agora só é ativada quando o UPS está efetivamente em modo bateria (`Status = 3`), evitando alarmes falsos em modo rede.
- **Histerese e Resiliência**: Implementada histerese nas triggers para evitar "flapping" e recuperação automática ao retornar para a rede elétrica.
- **Refatoração do Script**: Melhoria na estabilidade das chamadas de API do Zabbix com uso de `requests.Session` e timeouts configurados.

### 🔧 Correções
- Ajuste na escala de leitura de temperatura e voltagem (multiplicador 0.1) conforme especificações da MIB.
- Normalização de URLs de API para compatibilidade com Zabbix 7.x.

---
*Desenvolvido por: Daniel Wppslander*
