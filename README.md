# Projeto de Monitoramento de No-Breaks Intelbras (SNMP)

**Autor:** Daniel Wppslander

Este projeto tem como objetivo principal a implementação de um sistema de monitoramento para No-Breaks (UPS) da Intelbras, utilizando as Placas SNMP instaladas nos equipamentos. A intenção é coletar dados em tempo real para garantir a estabilidade e a disponibilidade dos sistemas críticos.

A biblioteca MIB (Management Information Base) utilizada como referência para a comunicação SNMP, `Upsmate.mib`, foi obtida do site oficial da Intelbras, especificamente na página da Placa SNMP para gerenciamento remoto PGR 801L:
[https://www.intelbras.com/pt-br/placa-snmp-para-gerenciamento-remoto-pgr-801l](https://www.intelbras.com/pt-br/placa-snmp-para-gerenciamento-remoto-pgr-801l)

## Componentes do Projeto

*   **`criar_template_ppc_full.py`**: Script Python responsável por automatizar a criação e atualização de templates de monitoramento no Zabbix. Ele utiliza a API do Zabbix para configurar itens de coleta de dados (baseados nos OIDs do MIB) e triggers de alerta para os No-Breaks.
*   **`Upsmate.mib`**: Arquivo MIB que define os identificadores de objeto (OIDs) e a estrutura dos dados SNMP para os dispositivos UPS da PPC/Intelbras. Este arquivo é crucial para entender como interpretar os dados coletados via SNMP.
*   **`GEMINI.md`**: Documentação interna para o Gemini CLI, detalhando o contexto do projeto, tecnologias utilizadas, e instruções de uso para o agente.

## Funcionalidades do Script Python

O script `criar_template_ppc_full.py` executa as seguintes ações:
*   Conecta-se a um servidor Zabbix configurado.
*   Cria ou atualiza um template Zabbix chamado `"Template No-Break PPC (SNMPv2)"`.
*   Associa o template a um grupo de host (`Templates/Energy`).
*   Define um mapeamento de valores para o status de saída do UPS (Online, OnBattery, etc.).
*   Cria itens de monitoramento para:
    *   Status de Operação.
    *   Capacidade da Bateria.
    *   Temperatura Interna.
    *   Voltagens de Entrada e Saída Trifásicas (Fases R, S, T).
*   Configura uma trigger de alerta para detecção de falta de energia (UPS operando na bateria).

## Como Usar o Script (`criar_template_ppc_full.py`)

### Pré-requisitos
*   Python 3.x
*   Acesso a um servidor Zabbix (com URL e token de API válidos).
*   Biblioteca `pyzabbix` instalada.
*   Biblioteca `python-dotenv` instalada.

### Instalação das Bibliotecas
```bash
pip install pyzabbix python-dotenv
```

### Configuração
1.  Crie um arquivo `.env` na raiz do projeto (você pode copiar o `env_example.txt` como base).
2.  Adicione suas credenciais do Zabbix no arquivo `.env`:

```env
ZABBIX_URL="http://seu-servidor-zabbix/"
ZABBIX_TOKEN="seu-token-api-zabbix"
```

O script lerá essas variáveis automaticamente.

### Execução
Após a configuração, execute o script para criar ou atualizar o template no Zabbix:

```bash
python criar_template_ppc_full.py
```

Este procedimento irá provisionar o template necessário para começar o monitoramento dos seus No-Breaks Intelbras via SNMP no Zabbix.
