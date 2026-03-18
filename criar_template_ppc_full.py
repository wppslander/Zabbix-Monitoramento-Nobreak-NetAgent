from pyzabbix import ZabbixAPI
import sys
import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

# --- CONFIGURAÇÃO ---
ZABBIX_URL = os.getenv("ZABBIX_URL")
ZABBIX_TOKEN = os.getenv("ZABBIX_TOKEN")
SIGNATURE = "\n\nDaniel Wppslander - https://github.com/wppslander"

if not ZABBIX_URL or not ZABBIX_TOKEN:
    print("Erro: ZABBIX_URL e ZABBIX_TOKEN devem ser definidos no arquivo .env")
    sys.exit(1)

TEMPLATE_NAME = "Template_No-Break_PPC_SNMPv2"
TEMPLATE_VISIBLE_NAME = "Template No-Break PPC (SNMPv2)"
HOST_GROUP_NAME = "Templates/Energy" 

# --- DEFINIÇÃO DOS ITENS ---
ITEMS_TO_CREATE = [
    {
        "name": "Serial Number",
        "key": "ups.serial",
        "oid": ".1.3.6.1.4.1.935.1.1.1.1.2.3.0",
        "units": "",
        "value_type": 1, 
        "delay": "1h",
        "description": "Número de série do equipamento."
    },
    {
        "name": "Modelo do UPS",
        "key": "ups.model",
        "oid": ".1.3.6.1.4.1.935.1.1.1.1.1.1.0",
        "units": "",
        "value_type": 1,
        "delay": "1h",
        "description": "Modelo identificado via SNMP."
    },
    {
        "name": "Status de Operação",
        "key": "ups.status",
        "oid": ".1.3.6.1.4.1.935.1.1.1.4.1.1.0",
        "units": "",
        "value_type": 3,
        "valuemap": "UPS Output Status",
        "delay": "1m",
        "description": "Status atual da saída de energia."
    },
    {
        "name": "Carga de Saída",
        "key": "ups.output.load",
        "oid": ".1.3.6.1.4.1.935.1.1.1.4.2.3.0",
        "units": "%",
        "value_type": 3,
        "delay": "1m",
        "description": "Percentual de carga sendo utilizado pelo UPS."
    },
    {
        "name": "Capacidade da Bateria",
        "key": "ups.battery.capacity",
        "oid": ".1.3.6.1.4.1.935.1.1.1.2.2.1.0",
        "units": "%",
        "value_type": 3,
        "delay": "5m",
        "description": "Nível de carga atual da bateria."
    },
    {
        "name": "Temperatura Interna",
        "key": "ups.temperature",
        "oid": ".1.3.6.1.4.1.935.1.1.1.2.2.3.0",
        "units": "ºC",
        "value_type": 0,
        "multiplier": 0.1,
        "delay": "5m",
        "description": "Temperatura interna do sistema de baterias."
    },
    # --- ENTRADA TRIFÁSICA ---
    {
        "name": "Entrada - Voltagem Fase R",
        "key": "ups.input.voltage.r",
        "oid": ".1.3.6.1.4.1.935.1.1.1.8.2.2.0",
        "units": "V",
        "value_type": 3,
        "delay": "1m",
        "description": "Tensão de entrada na Fase R."
    },
    {
        "name": "Entrada - Voltagem Fase S",
        "key": "ups.input.voltage.s",
        "oid": ".1.3.6.1.4.1.935.1.1.1.8.2.3.0",
        "units": "V",
        "value_type": 3,
        "delay": "1m",
        "description": "Tensão de entrada na Fase S."
    },
    {
        "name": "Entrada - Voltagem Fase T",
        "key": "ups.input.voltage.t",
        "oid": ".1.3.6.1.4.1.935.1.1.1.8.2.4.0",
        "units": "V",
        "value_type": 3,
        "delay": "1m",
        "description": "Tensão de entrada na Fase T."
    },
    # --- SAÍDA TRIFÁSICA ---
    {
        "name": "Saída - Voltagem Fase R",
        "key": "ups.output.voltage.r",
        "oid": ".1.3.6.1.4.1.935.1.1.1.8.3.2.0",
        "units": "V",
        "value_type": 3,
        "delay": "1m",
        "description": "Tensão de saída na Fase R."
    },
    {
        "name": "Saída - Voltagem Fase S",
        "key": "ups.output.voltage.s",
        "oid": ".1.3.6.1.4.1.935.1.1.1.8.3.3.0",
        "units": "V",
        "value_type": 3,
        "delay": "1m",
        "description": "Tensão de saída na Fase S."
    },
    {
        "name": "Saída - Voltagem Fase T",
        "key": "ups.output.voltage.t",
        "oid": ".1.3.6.1.4.1.935.1.1.1.8.3.4.0",
        "units": "V",
        "value_type": 3,
        "delay": "1m",
        "description": "Tensão de saída na Fase T."
    }
]

def main():
    print(f"Conectando em {ZABBIX_URL}...")
    try:
        zapi = ZabbixAPI(ZABBIX_URL)
        zapi.login(api_token=ZABBIX_TOKEN)
    except Exception as e:
        print(f"Erro na conexão: {e}")
        sys.exit()

    # 1. Grupo de Hosts
    groups = zapi.hostgroup.get(filter={"name": HOST_GROUP_NAME})
    group_id = groups[0]['groupid'] if groups else "1"

    # 2. Criar/Atualizar Template
    print(f"Sincronizando template '{TEMPLATE_NAME}'...")
    try:
        template = zapi.template.create({
            "host": TEMPLATE_NAME,
            "name": TEMPLATE_VISIBLE_NAME,
            "groups": [{"groupid": group_id}],
            "description": f"Template para No-Breaks Intelbras/PPC via SNMPv2.{SIGNATURE}"
        })
        template_id = template['templateids'][0]
    except Exception:
        t = zapi.template.get(filter={"host": TEMPLATE_NAME})
        template_id = t[0]['templateid']
        zapi.template.update({"templateid": template_id, "description": f"Template para No-Breaks Intelbras/PPC via SNMPv2.{SIGNATURE}"})

    # 3. Value Mapping
    try:
        if not zapi.valuemap.get(filter={"hostid": template_id, "name": "UPS Output Status"}):
            zapi.valuemap.create({
                "hostid": template_id,
                "name": "UPS Output Status",
                "mappings": [
                    {"value": "1", "newvalue": "Unknown"}, {"value": "2", "newvalue": "OnLine"},
                    {"value": "3", "newvalue": "OnBattery"}, {"value": "4", "newvalue": "OnBoost"},
                    {"value": "5", "newvalue": "Sleeping"}, {"value": "6", "newvalue": "OnBypass"},
                    {"value": "7", "newvalue": "Rebooting"}, {"value": "8", "newvalue": "StandBy"},
                    {"value": "9", "newvalue": "OnBuck"}
                ]
            })
    except: pass

    # 4. Itens
    print("Sincronizando Itens...")
    for item in ITEMS_TO_CREATE:
        exists = zapi.item.get(filter={"hostid": template_id, "key_": item['key']})
        params = {
            "name": item['name'], "key_": item['key'], "hostid": template_id,
            "type": 20, "snmp_oid": item['oid'], "value_type": item['value_type'],
            "units": item['units'], "interfaceid": "0", "delay": item['delay'],
            "description": item.get('description', '') + SIGNATURE
        }
        if "multiplier" in item:
            params["preprocessing"] = [{"type": "1", "params": str(item['multiplier'])}]
        if "valuemap" in item:
            vm = zapi.valuemap.get(filter={"hostid": template_id, "name": item['valuemap']})
            if vm: params["valuemapid"] = vm[0]['valuemapid']

        if exists:
            params["itemid"] = exists[0]['itemid']
            del params["hostid"]
            zapi.item.update(params)
        else:
            zapi.item.create(params)

    # 5. Triggers
    print("Configurando Triggers...")
    triggers_data = [
        {"desc": "UPS: Falta de Energia (Operando na Bateria)", "exp": f"last(/{TEMPLATE_NAME}/ups.status)=3", "pri": 4},
        {"desc": "UPS: Sobrecarga de Saída (>90%)", "exp": f"last(/{TEMPLATE_NAME}/ups.output.load)>90", "pri": 3},
        {"desc": "UPS: Bateria com Capacidade Baixa (<20%)", "exp": f"last(/{TEMPLATE_NAME}/ups.battery.capacity)<20", "pri": 4},
        {"desc": "UPS: Serial Number Alterado", "exp": f"change(/{TEMPLATE_NAME}/ups.serial)=1", "pri": 2}
    ]

    for trig in triggers_data:
        existing = zapi.trigger.get(filter={"description": trig['desc'], "host": TEMPLATE_NAME})
        t_params = {
            "description": trig['desc'], "expression": trig['exp'], "priority": trig['pri'],
            "comments": f"Alerta automático.{SIGNATURE}", "manual_close": "1"
        }
        if existing:
            t_params["triggerid"] = existing[0]['triggerid']
            zapi.trigger.update(t_params)
        else:
            zapi.trigger.create(t_params)

    print("\n--- Template Full Sincronizado com Assinatura ---")

if __name__ == "__main__":
    main()
