import requests
import json
import os
from dotenv import load_dotenv

load_dotenv(override=True)
ZABBIX_URL = os.getenv("ZABBIX_URL").rstrip("/")
if not ZABBIX_URL.endswith("api_jsonrpc.php"):
    ZABBIX_URL += "/api_jsonrpc.php"
ZABBIX_TOKEN = os.getenv("ZABBIX_TOKEN")

def call_zabbix(method, params):
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "auth": ZABBIX_TOKEN, "id": 1}
    return requests.post(ZABBIX_URL, json=payload).json().get("result")

def check_host(ip):
    # 1. Buscar Host ID pelo IP
    interfaces = call_zabbix("hostinterface.get", {"filter": {"ip": ip}})
    if not interfaces:
        print(f"Host com IP {ip} não encontrado.")
        return
    host_id = interfaces[0]['hostid']
    
    # 2. Buscar Dados Recentes (Items)
    items = call_zabbix("item.get", {
        "hostids": host_id,
        "search": {"key_": "ups."},
        "output": ["name", "key_", "lastvalue", "units"]
    })
    
    # 3. Buscar Triggers Ativas
    triggers = call_zabbix("trigger.get", {
        "hostids": host_id,
        "filter": {"value": 1},
        "output": ["description", "priority"]
    })

    print(f"\n--- Relatório para o Host: {ip} ---")
    print("\nAlertas Ativos:")
    if not triggers:
        print("Nenhum alerta ativo no momento.")
    for t in triggers:
        print(f"- {t['description']} (Severidade: {t['priority']})")

    print("\nDados de Telemetria:")
    for i in items:
        val = i['lastvalue']
        # Formata valores que sabemos que usam multiplicador se necessário (aqui pegamos o valor bruto do banco)
        print(f"- {i['name']}: {val} {i['units']}")

if __name__ == "__main__":
    check_host("10.1.71.50")
