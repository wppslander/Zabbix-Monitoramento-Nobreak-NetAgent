import requests
import json
import sys
import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env (força sobrescrita)
load_dotenv(override=True)

ZABBIX_URL = os.getenv("ZABBIX_URL")
if ZABBIX_URL:
    ZABBIX_URL = ZABBIX_URL.rstrip("/")
    if not ZABBIX_URL.endswith("api_jsonrpc.php"):
        ZABBIX_URL += "/api_jsonrpc.php"

ZABBIX_TOKEN = os.getenv("ZABBIX_TOKEN")
SIGNATURE = "\n\nDaniel Wppslander - https://github.com/wppslander"
TEMPLATE_NAME = "Template_No-Break_PPC_SNMPv2"

# Instância global da sessão para eficiência
session = requests.Session()

def call_zabbix(method, params):
    """
    Realiza uma chamada para a API do Zabbix 7 garantindo resiliência.
    Focado em estabilidade: implementa timeout e tratamento de erros de rede.
    """
    headers = {"Content-Type": "application/json-rpc"}
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "auth": ZABBIX_TOKEN,
        "id": 1
    }
    
    try:
        # Timeout de 15 segundos para evitar que o script trave
        response = session.post(ZABBIX_URL, headers=headers, data=json.dumps(payload), timeout=15)
        response.raise_for_status() # Valida erros HTTP (4xx, 5xx)
        
        result = response.json()
        if "error" in result:
            print(f"ERRO API ({method}): {result['error']['message']} - {result['error']['data']}")
            return None
        return result["result"]
        
    except requests.exceptions.Timeout:
        print(f"AVISO: Tempo esgotado (timeout) ao chamar {method}. O servidor Zabbix está lento.")
    except requests.exceptions.ConnectionError:
        print(f"ERRO CRÍTICO: Falha de rede ao conectar no Zabbix Server em {ZABBIX_URL}")
    except Exception as e:
        print(f"ERRO INESPERADO em {method}: {e}")
    
    return None

def main():
    print(f"Iniciando atualização resiliente em {ZABBIX_URL}...")
    
    # 1. Validar Conexão e Template
    t = call_zabbix("template.get", {"filter": {"host": TEMPLATE_NAME}})
    if t is None: # Erro crítico de comunicação
        print("Abortando: Não foi possível validar o template devido a erros de conexão.")
        sys.exit(1)
    if not t:
        print(f"Erro: Template '{TEMPLATE_NAME}' não encontrado.")
        sys.exit(1)
    
    template_id = t[0]['templateid']
    print(f"Conexão OK! Template ID: {template_id}")

    # 2. Atualizar Descrição e Macros
    call_zabbix("template.update", {
        "templateid": template_id,
        "description": f"Template para No-Breaks Intelbras/PPC via SNMPv2 (Placa NetAgent IX).{SIGNATURE}",
        "macros": [
            {
                "macro": "{$UPS.BATTERY.VOLT.MIN}",
                "value": "72",
                "description": "Voltagem mínima do banco de baterias para disparo de alerta."
            }
        ]
    })

    # 3. Sincronizar Itens
    items_data = [
        {"name": "Carga de Saída", "key": "ups.output.load", "oid": ".1.3.6.1.4.1.935.1.1.1.4.2.3.0", "units": "%", "vtype": 3, "delay": "1m", "desc": "Carga atual."},
        {"name": "Capacidade da Bateria", "key": "ups.battery.capacity", "oid": ".1.3.6.1.4.1.935.1.1.1.2.2.1.0", "units": "%", "vtype": 3, "delay": "5m", "desc": "Nível da bateria."},
        {"name": "Tensão da Bateria", "key": "ups.battery.voltage", "oid": ".1.3.6.1.4.1.935.1.1.1.2.2.2.0", "units": "V", "vtype": 0, "delay": "1m", "desc": "Voltagem da bateria.", "mult": 0.1},
        {"name": "Status de Operação", "key": "ups.status", "oid": ".1.3.6.1.4.1.935.1.1.1.4.1.1.0", "units": "", "vtype": 3, "delay": "1m", "desc": "Status atual.", "vmap": "UPS Output Status"},
        {"name": "Temperatura Interna", "key": "ups.temperature", "oid": ".1.3.6.1.4.1.935.1.1.1.2.2.3.0", "units": "ºC", "vtype": 0, "delay": "5m", "desc": "Temp. interna.", "mult": 0.1},
        {"name": "Serial Number", "key": "ups.serial", "oid": ".1.3.6.1.4.1.935.1.1.1.1.2.3.0", "units": "", "vtype": 1, "delay": "1h", "desc": "Número de Série."}
    ]

    print("Sincronizando itens...")
    for i in items_data:
        exists = call_zabbix("item.get", {"hostids": template_id, "filter": {"key_": i['key']}})
        if exists is None: continue # Pula se houver erro de rede
        
        params = {
            "name": i['name'], "key_": i['key'], "hostid": template_id,
            "type": 20, "snmp_oid": i['oid'], "value_type": i['vtype'],
            "units": i['units'], "delay": i['delay'], "interfaceid": "0",
            "description": i['desc'] + SIGNATURE
        }

        if "mult" in i:
            params["preprocessing"] = [{
                "type": "1", "params": str(i['mult']), 
                "error_handler": "0", "error_handler_params": ""
            }]
        
        if "vmap" in i:
            vm = call_zabbix("valuemap.get", {"hostids": template_id, "filter": {"name": i['vmap']}})
            if vm: params["valuemapid"] = vm[0]['valuemapid']

        if exists:
            params["itemid"] = exists[0]['itemid']
            del params["hostid"]
            call_zabbix("item.update", params)
            print(f"OK: {i['name']}")
        else:
            call_zabbix("item.create", params)
            print(f"Criado: {i['name']}")

    # 4. Triggers com Histerese (Evita alertas falsos/spam)
    print("Configurando Triggers inteligentes...")
    triggers = [
        {
            "desc": "UPS: Falta de Energia (Operando na Bateria)", 
            "exp": f"last(/{TEMPLATE_NAME}/ups.status)=3", 
            "recovery": f"last(/{TEMPLATE_NAME}/ups.status)=2", # Só recupera quando voltar a ser OnLine (2)
            "pri": 4
        },
        {
            "desc": "UPS: Sobrecarga de Saída (>90%)", 
            "exp": f"last(/{TEMPLATE_NAME}/ups.output.load)>90",
            "recovery": f"last(/{TEMPLATE_NAME}/ups.output.load)<80", # Histerese de 10%
            "pri": 3
        },
        {
            "desc": "UPS: Bateria com Capacidade Baixa (<20%)", 
            "exp": f"last(/{TEMPLATE_NAME}/ups.battery.capacity)<20",
            "recovery": f"last(/{TEMPLATE_NAME}/ups.battery.capacity)>30", # Só recupera quando atingir 30%
            "pri": 4
        },
        {
            "desc": "UPS: Voltagem de Bateria Baixa (Macro)", 
            "exp": f"last(/{TEMPLATE_NAME}/ups.battery.voltage)<{{$UPS.BATTERY.VOLT.MIN}}",
            "recovery": f"last(/{TEMPLATE_NAME}/ups.battery.voltage)>({{$UPS.BATTERY.VOLT.MIN}}+2)", # Histerese de 2V
            "pri": 4
        }
    ]

    for t_data in triggers:
        existing = call_zabbix("trigger.get", {"host": TEMPLATE_NAME, "filter": {"description": t_data['desc']}})
        if existing is None: continue

        t_params = {
            "description": t_data['desc'],
            "expression": t_data['exp'],
            "recovery_mode": 1, # Recovery Expression
            "recovery_expression": t_data['recovery'],
            "priority": t_data['pri'],
            "comments": f"Monitoramento automático com histerese para evitar flapping.{SIGNATURE}",
            "manual_close": "1"
        }
        
        if existing:
            t_params["triggerid"] = existing[0]['triggerid']
            call_zabbix("trigger.update", t_params)
            print(f"Trigger OK: {t_data['desc']}")
        else:
            call_zabbix("trigger.create", t_params)
            print(f"Trigger Criada: {t_data['desc']}")

    print("\n--- Atualização Concluída com Resiliência e Histerese! ---")

if __name__ == "__main__":
    main()
