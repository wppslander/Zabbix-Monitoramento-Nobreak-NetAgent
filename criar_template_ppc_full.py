from pyzabbix import ZabbixAPI
import sys
import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

# --- CONFIGURAÇÃO ---
# URL fornecida (ajustei para apontar para a API. Se der erro 404, tente adicionar /zabbix no final)
ZABBIX_URL = os.getenv("ZABBIX_URL")
ZABBIX_TOKEN = os.getenv("ZABBIX_TOKEN")

if not ZABBIX_URL or not ZABBIX_TOKEN:
    print("Erro: ZABBIX_URL e ZABBIX_TOKEN devem ser definidos no arquivo .env")
    sys.exit(1)

TEMPLATE_NAME = "Template No-Break PPC (SNMPv2)"
# Grupo onde o template será salvo. O script tenta achar o ID 1, ou cria um novo se precisar.
HOST_GROUP_NAME = "Templates/Energy" 

# --- DEFINIÇÃO DOS ITENS (Baseado no Upsmate.mib) ---
# OID Base PPC: .1.3.6.1.4.1.935.1.1.1 (ups)
# Trifásico Base: .1.3.6.1.4.1.935.1.1.1.8 (upsThreePhase) [cite: 4, 6]

ITEMS_TO_CREATE = [
    # --- Status Geral ---
    {
        "name": "Status de Operação",
        "key": "ups.status",
        "oid": ".1.3.6.1.4.1.935.1.1.1.4.1.1.0", # upsBaseOutputStatus [cite: 53]
        "units": "",
        "value_type": 3, # Numeric Unsigned
        "valuemap": "UPS Output Status",
        "delay": "1m"
    },
    {
        "name": "Capacidade da Bateria",
        "key": "ups.battery.capacity",
        "oid": ".1.3.6.1.4.1.935.1.1.1.2.2.1.0", # upsSmartBatteryCapacity [cite: 33]
        "units": "%",
        "value_type": 3,
        "delay": "5m"
    },
    {
        "name": "Temperatura Interna",
        "key": "ups.temperature",
        "oid": ".1.3.6.1.4.1.935.1.1.1.2.2.3.0", # upsSmartBatteryTemperature [cite: 35]
        "units": "ºC",
        "value_type": 0, # Float
        "multiplier": 0.1, # MIB diz "tenths of Celsius" [cite: 35]
        "delay": "5m"
    },
    
    # --- ENTRADA TRIFÁSICA (Input) ---
    {
        "name": "Entrada - Voltagem Fase R",
        "key": "ups.input.voltage.r",
        "oid": ".1.3.6.1.4.1.935.1.1.1.8.2.2.0", # upsThreePhaseInputVoltageR [cite: 165]
        "units": "V",
        "value_type": 3,
        "delay": "1m"
    },
    {
        "name": "Entrada - Voltagem Fase S",
        "key": "ups.input.voltage.s",
        "oid": ".1.3.6.1.4.1.935.1.1.1.8.2.3.0", # upsThreePhaseInputVoltageS [cite: 166]
        "units": "V",
        "value_type": 3,
        "delay": "1m"
    },
    {
        "name": "Entrada - Voltagem Fase T",
        "key": "ups.input.voltage.t",
        "oid": ".1.3.6.1.4.1.935.1.1.1.8.2.4.0", # upsThreePhaseInputVoltageT
        "units": "V",
        "value_type": 3,
        "delay": "1m"
    },

    # --- SAÍDA TRIFÁSICA (Output) ---
    {
        "name": "Saída - Voltagem Fase R",
        "key": "ups.output.voltage.r",
        "oid": ".1.3.6.1.4.1.935.1.1.1.8.3.2.0", # upsThreePhaseOutputVoltageR [cite: 167]
        "units": "V",
        "value_type": 3,
        "delay": "1m"
    },
    {
        "name": "Saída - Voltagem Fase S",
        "key": "ups.output.voltage.s",
        "oid": ".1.3.6.1.4.1.935.1.1.1.8.3.3.0", # upsThreePhaseOutputVoltageS [cite: 168]
        "units": "V",
        "value_type": 3,
        "delay": "1m"
    },
    {
        "name": "Saída - Voltagem Fase T",
        "key": "ups.output.voltage.t",
        "oid": ".1.3.6.1.4.1.935.1.1.1.8.3.4.0", # upsThreePhaseOutputVoltageT [cite: 169]
        "units": "V",
        "value_type": 3,
        "delay": "1m"
    }
]

def main():
    print(f"Conectando em {ZABBIX_URL} usando TOKEN...")
    
    # Conexão simplificada com Token
    try:
        zapi = ZabbixAPI(ZABBIX_URL)
        zapi.login(api_token=ZABBIX_TOKEN)
        print(f"Conectado! Versão da API: {zapi.api_version()}")
    except Exception as e:
        print(f"Erro na conexão: {e}")
        print("Dica: Verifique se a URL precisa de '/zabbix' no final.")
        sys.exit()

    # 1. Resolver Grupo de Hosts
    # Tenta achar o grupo pelo nome, se não, usa o ID 1 (padrão)
    groups = zapi.hostgroup.get(filter={"name": HOST_GROUP_NAME})
    if groups:
        group_id = groups[0]['groupid']
        print(f"Usando grupo existente: {HOST_GROUP_NAME} (ID: {group_id})")
    else:
        print(f"Grupo '{HOST_GROUP_NAME}' não encontrado. Usando grupo ID 1 (Templates).")
        group_id = "1"

    # 2. Criar ou Atualizar Template
    print(f"Criando/Atualizando template '{TEMPLATE_NAME}'...")
    try:
        # Tenta criar
        template = zapi.template.create({
            "host": TEMPLATE_NAME,
            "groups": [{"groupid": group_id}],
            "description": "Template Trifásico PPC - Criado via Python API"
        })
        template_id = template['templateids'][0]
        print(f"Template criado com sucesso: ID {template_id}")
    except Exception as e:
        # Se der erro, assume que já existe e pega o ID
        if "already exists" in str(e):
            t = zapi.template.get(filter={"host": TEMPLATE_NAME})
            template_id = t[0]['templateid']
            print(f"Template já existia. ID recuperado: {template_id}")
        else:
            print(f"Erro crítico ao criar template: {e}")
            sys.exit()

    # 3. Value Mapping (Status)
    # [cite: 53-55]
    print("Configurando Mapeamento de Valores...")
    try:
        # Verifica se já existe para não duplicar erro
        existing_vmap = zapi.valuemap.get(filter={"hostid": template_id, "name": "UPS Output Status"})
        if not existing_vmap:
            zapi.valuemap.create({
                "hostid": template_id,
                "name": "UPS Output Status",
                "mappings": [
                    {"value": "1", "newvalue": "Unknown"},
                    {"value": "2", "newvalue": "OnLine"},
                    {"value": "3", "newvalue": "OnBattery"},
                    {"value": "4", "newvalue": "OnBoost"},
                    {"value": "5", "newvalue": "Sleeping"},
                    {"value": "6", "newvalue": "OnBypass"},
                    {"value": "7", "newvalue": "Rebooting"},
                    {"value": "8", "newvalue": "StandBy"},
                    {"value": "9", "newvalue": "OnBuck"}
                ]
            })
    except Exception as e:
        print(f"Aviso ValueMap: {e}")

    # 4. Loop de Criação dos Itens
    print("Sincronizando Itens...")
    for item in ITEMS_TO_CREATE:
        try:
            # Verifica se item já existe pelo nome (key_)
            exists = zapi.item.get(filter={"hostid": template_id, "key_": item['key']})
            
            params = {
                "name": item['name'],
                "key_": item['key'],
                "hostid": template_id,
                "type": 20, # SNMP Agent
                "snmp_oid": item['oid'],
                "value_type": item['value_type'],
                "units": item['units'],
                "interfaceid": "0",
                "delay": item['delay']
            }

            # Lógica para Value Map ID
            if "valuemap" in item:
                vm = zapi.valuemap.get(filter={"hostid": template_id, "name": item['valuemap']})
                if vm: params["valuemapid"] = vm[0]['valuemapid']

            # Lógica para Multiplicador (Pre-processing)
            if "multiplier" in item:
                params["preprocessing"] = [{"type": "1", "params": str(item['multiplier'])}]

            if exists:
                # Update (Item já existe)
                params["itemid"] = exists[0]['itemid']
                zapi.item.update(params)
                print(f"Item atualizado: {item['name']}")
            else:
                # Create (Novo item)
                zapi.item.create(params)
                print(f"Item criado: {item['name']}")

        except Exception as e:
            print(f"Erro no item {item['name']}: {e}")

    # 5. Criar Trigger de Falta de Energia
    print("Verificando Triggers...")
    try:
        description = "UPS: Falta de Energia (Operando na Bateria)"
        expression = f"last(/{TEMPLATE_NAME}/ups.status)=3" # Status 3 = OnBattery [cite: 53]
        
        # Verifica duplicidade simples
        trig_exists = zapi.trigger.get(filter={"description": description, "host": TEMPLATE_NAME})
        if not trig_exists:
            zapi.trigger.create({
                "description": description,
                "expression": expression,
                "priority": 4, # High
                "manual_close": "1"
            })
            print("Trigger de Falta de Energia criada.")
        else:
            print("Trigger já existe.")
            
    except Exception as e:
        print(f"Erro na trigger: {e}")

    print("\n--- Concluído! Verifique o template no Zabbix ---")

if __name__ == "__main__":
    main()
