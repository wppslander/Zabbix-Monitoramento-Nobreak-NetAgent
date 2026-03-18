# Zabbix Monitoring: Intelbras/PPC UPS (SNMPv2) - NetAgent IX

Este projeto contém ferramentas de automação para criação e atualização de templates de monitoramento Zabbix para No-Breaks da linha Intelbras/PPC utilizando o protocolo SNMPv2 e especificamente a placa de comunicação **NetAgent IX** (vendida pela Intelbras).

Desenvolvido por: **Daniel Wppslander** - [GitHub](https://github.com/wppslander)

---

## 🚀 Itens Monitorados (Sensores)

O template coleta as seguintes métricas essenciais do No-Break:

| Item | Descrição | OID | Frequência |
| :--- | :--- | :--- | :--- |
| **Status de Operação** | Estado atual (OnLine, OnBattery, Bypass, etc) | `.1.3.6.1.4.1.935.1.1.1.4.1.1.0` | 1m |
| **Carga de Saída (Load)** | Percentual de uso da potência nominal do UPS | `.1.3.6.1.4.1.935.1.1.1.4.2.3.0` | 1m |
| **Capacidade da Bateria** | Nível de carga atual da bateria (%) | `.1.3.6.1.4.1.935.1.1.1.2.2.1.0` | 5m |
| **Tensão da Bateria** | Voltagem atual do banco de baterias (V) | `.1.3.6.1.4.1.935.1.1.1.2.2.2.0` | 1m |
| **Temperatura Interna** | Temperatura do sistema de baterias (ºC) | `.1.3.6.1.4.1.935.1.1.1.2.2.3.0` | 5m |
| **Tensão de Entrada (R/S/T)** | Voltagem de entrada (Fases R, S e T) | `.1.3.6.1.4.1.935.1.1.1.8.2.x.0` | 1m |
| **Tensão de Saída (R/S/T)** | Voltagem de saída (Fases R, S e T) | `.1.3.6.1.4.1.935.1.1.1.8.3.x.0` | 1m |
| **Serial Number** | Identificação única do hardware | `.1.3.6.1.4.1.935.1.1.1.1.2.3.0` | 1h |
| **Modelo do UPS** | Nome do modelo do equipamento | `.1.3.6.1.4.1.935.1.1.1.1.1.1.0` | 1h |

---

## 🔔 Triggers de Alerta (Alertas Automáticos)

O sistema conta com inteligência para notificar as seguintes condições críticas:

1.  **UPS: Falta de Energia (Operando na Bateria)**
    *   **Severidade:** Desastre (High)
    *   **Condição:** Dispara quando o status de saída muda para `OnBattery` (3).
2.  **UPS: Sobrecarga de Saída (>90%)**
    *   **Severidade:** Média (Average)
    *   **Condição:** Dispara se a carga conectada ultrapassar 90% da capacidade do UPS.
3.  **UPS: Bateria com Capacidade Baixa (<20%)**
    *   **Severidade:** Desastre (High)
    *   **Condição:** Alerta crítico quando a autonomia da bateria cai abaixo de 20%.
4.  **UPS: Voltagem de Bateria Baixa (Macro)**
    *   **Severidade:** Alta (High)
    *   **Condição:** Dispara se a voltagem cair abaixo da macro `{$UPS.BATTERY.VOLT.MIN}` **somente quando o UPS estiver em modo bateria**. Evita alarmes falsos enquanto o equipamento está em modo rede.
5.  **UPS: Serial Number Alterado**
    *   **Severidade:** Informação (Warning)
    *   **Condição:** Detecta se o hardware foi trocado ou se houve alteração na placa NetAgent.

---

## 💡 Caso de Uso Real

Em um cenário real, este template detectou uma queda na voltagem nominal das baterias em um site remoto. Enquanto o painel físico do equipamento não indicava alarmes, a telemetria via Zabbix permitiu o acionamento da manutenção preventiva. O hardware falhou 24h depois, mas a substituição já havia sido programada, resultando em 0% de impacto na operação.

---

## 🛠️ Como Utilizar

### 1. Requisitos
*   Python 3.x
*   Ambiente Virtual (venv) configurado
*   Bibliotecas: `requests`, `python-dotenv`

### 2. Configuração
Edite o arquivo `.env` na raiz do projeto:
```env
ZABBIX_URL="http://seu-servidor/zabbix/"
ZABBIX_TOKEN="seu-api-token-aqui"
```

### 3. Scripts e Arquivos Disponíveis

*   **`Upsmate.mib`**: Arquivo MIB original para consulta de OIDs e documentação técnica da Intelbras/PPC.
*   **`criar_template_ppc_full.py`**: Cria o template do zero, incluindo grupos de hosts, mapeamento de valores (Value Maps) e todos os itens.
*   **`atualizar_template_ppc.py`**: Atualiza um template existente com os itens mais recentes, novas triggers e assinatura do autor.

### 4. Execução
Para atualizar o template atual:
```bash
./venv/bin/python atualizar_template_ppc.py
```

---

## 📝 Notas de Versão
*   Todos os itens e triggers incluem a assinatura: `Daniel Wppslander - https://github.com/wppslander`.
*   Suporte completo para Zabbix 7.x utilizando autenticação via API Token (Bearer).
*   Normalização automática de URL para evitar erros de endpoint da API.
