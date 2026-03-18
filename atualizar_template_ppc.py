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

if not ZABBIX_URL or not ZABBIX_TOKEN:
    print("Erro: ZABBIX_URL e ZABBIX_TOKEN devem ser definidos no arquivo .env")
    sys.exit(1)

TEMPLATE_NAME = "Template_No-Break_PPC_SNMPv2"

def call_zabbix(method, params):
    headers = {
        "Content-Type": "application/json-rpc"
    }
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "auth": ZABBIX_TOKEN,
        "id": 1
    }
    response = requests.post(ZABBIX_URL, headers=headers, data=json.dumps(payload))
    if response.status_code != 200:
        print(f"Erro HTTP {response.status_code}: {response.text}")
        return None
    
    result = response.json()
    if "error" in result:
        print(f"Erro na API ({method}): {result['error']['message']} - {result['error']['data']}")
        return None
    return result["result"]

def main():
    print(f"DEBUG: URL={ZABBIX_URL}")
    print(f"DEBUG: TOKEN={ZABBIX_TOKEN}")
    print(f"Conectando em {ZABBIX_URL}...")
    
    # 1. Buscar Template
    t = call_zabbix("template.get", {"filter": {"host": TEMPLATE_NAME}})
    if not t:
        print(f"Erro: Template '{TEMPLATE_NAME}' não encontrado.")
        sys.exit(1)
    
    template_id = t[0]['templateid']
    print(f"Template encontrado: ID {template_id}")

    # 2. Atualizar Descrição do Template
    call_zabbix("template.update", {
        "templateid": template_id,
        "description": f"Template para No-Breaks Intelbras/PPC via SNMPv2.{SIGNATURE}"
    })

    # 3. Itens
    items_data = [
        {"name": "Carga de Saída", "key": "ups.output.load", "oid": ".1.3.6.1.4.1.935.1.1.1.4.2.3.0", "units": "%", "vtype": 3, "delay": "1m", "desc": "Percentual de carga."},
        {"name": "Capacidade da Bateria", "key": "ups.battery.capacity", "oid": ".1.3.6.1.4.1.935.1.1.1.2.2.1.0", "units": "%", "vtype": 3, "delay": "5m", "desc": "Nível de carga da bateria."},
        {"name": "Status de Operação", "key": "ups.status", "oid": ".1.3.6.1.4.1.935.1.1.1.4.1.1.0", "units": "", "vtype": 3, "delay": "1m", "desc": "Status da saída.", "vmap": "UPS Output Status"},
        {"name": "Temperatura Interna", "key": "ups.temperature", "oid": ".1.3.6.1.4.1.935.1.1.1.2.2.3.0", "units": "ºC", "vtype": 0, "delay": "5m", "desc": "Temperatura bateria.", "mult": 0.1},
        {"name": "Serial Number", "key": "ups.serial", "oid": ".1.3.6.1.4.1.935.1.1.1.1.2.3.0", "units": "", "vtype": 1, "delay": "1h", "desc": "SN do UPS."}
    ]

    print("Sincronizando itens...")
    for i in items_data:
        # Busca item existente
        exists = call_zabbix("item.get", {"hostids": template_id, "filter": {"key_": i['key']}})
        
        params = {
            "name": i['name'], "key_": i['key'], "hostid": template_id,
            "type": 20, "snmp_oid": i['oid'], "value_type": i['vtype'],
            "units": i['units'], "delay": i['delay'], "interfaceid": "0",
            "description": i['desc'] + SIGNATURE
        }

        if "mult" in i:
            params["preprocessing"] = [{"type": "1", "params": str(i['mult'])}]
        
        if "vmap" in i:
            vm = call_zabbix("valuemap.get", {"hostids": template_id, "filter": {"name": i['vmap']}})
            if vm: params["valuemapid"] = vm[0]['valuemapid']

        if exists:
            params["itemid"] = exists[0]['itemid']
            del params["hostid"]
            call_zabbix("item.update", params)
            print(f"OK: {i['name']} (Atualizado)")
        else:
            call_zabbix("item.create", params)
            print(f"OK: {i['name']} (Criado)")

    # 4. Triggers
    print("Configurando Triggers...")
    triggers = [
        {"desc": "UPS: Falta de Energia (Operando na Bateria)", "exp": f"last(/{TEMPLATE_NAME}/ups.status)=3", "pri": 4},
        {"desc": "UPS: Sobrecarga de Saída (>90%)", "exp": f"last(/{TEMPLATE_NAME}/ups.output.load)>90", "pri": 3},
        {"desc": "UPS: Bateria com Capacidade Baixa (<20%)", "exp": f"last(/{TEMPLATE_NAME}/ups.battery.capacity)<20", "pri": 4}
    ]

    for t_data in triggers:
        existing = call_zabbix("trigger.get", {"host": TEMPLATE_NAME, "filter": {"description": t_data['desc']}})
        t_params = {
            "description": t_data['desc'], "expression": t_data['exp'], "priority": t_data['pri'],
            "comments": f"Alerta automático.{SIGNATURE}", "manual_close": "1"
        }
        if existing:
            t_params["triggerid"] = existing[0]['triggerid']
            call_zabbix("trigger.update", t_params)
            print(f"Trigger Atualizada: {t_data['desc']}")
        else:
            call_zabbix("trigger.create", t_params)
            print(f"Trigger Criada: {t_data['desc']}")

    print("\n--- Atualização Concluída com Sucesso! ---")

if __name__ == "__main__":
    main()
