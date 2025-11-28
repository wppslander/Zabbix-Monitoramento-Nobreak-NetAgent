# Project Context: FontIntelbras (Zabbix UPS Integration)

This project contains tools to automate the creation of Zabbix monitoring templates for Intelbras/PPC UPS (Uninterruptible Power Supply) devices using SNMP.

## Key Components

### 1. Scripts
*   **`criar_template_ppc_full.py`**: The core Python automation script.
    *   **Function:** Connects to a Zabbix API, creates a template named `"Template No-Break PPC (SNMPv2)"`, and populates it with Items (sensors) and Triggers (alerts) based on the PPC MIB.
    *   **Key Features:**
        *   Creates Host Group `Templates/Energy` (or uses ID 1 if not found).
        *   Sets up Value Mapping for UPS Status (OnLine, OnBattery, etc.).
        *   Adds items for Battery Capacity, Temperature, and 3-Phase Input/Output Voltages.
        *   Adds a trigger for Power Failure (OnBattery status).

### 2. Data Definitions
*   **`Upsmate.mib`**: Management Information Base (MIB) file defining the SNMP OID structure for the target UPS hardware (PPC/Intelbras). Used as a reference for the OIDs in the Python script.

### 3. Other
*   **`package-lock.json`**: Existing but currently appears unused/empty. Indicates a potential previous or future Node.js context, but the current active project is Python-based.

## Setup & Usage

### Prerequisites
*   Python 3.x
*   Zabbix Server (accessible network-wise)
*   `pyzabbix` library

### Installation
```bash
pip install pyzabbix
```

### Configuration
Open `criar_template_ppc_full.py` and modify the configuration section at the top:

```python
ZABBIX_URL = "http://your-zabbix-server/" 
ZABBIX_TOKEN = "your-api-token"
TEMPLATE_NAME = "Template No-Break PPC (SNMPv2)"
HOST_GROUP_NAME = "Templates/Energy"
```

### Execution
Run the script to generate/update the template in Zabbix:

```bash
python criar_template_ppc_full.py
```

## Development Notes

*   **OIDs**: The OIDs mapped in the script (e.g., `.1.3.6.1.4.1.935...`) correspond to the definitions in `Upsmate.mib`. If adding new metrics, cross-reference this file.
*   **Zabbix API**: The script handles authentication and basic CRUD operations (Create/Read/Update) for Templates, Items, and Triggers.
*   **Error Handling**: The script includes basic error handling for connection failures and existing objects (to support re-running the script for updates).
