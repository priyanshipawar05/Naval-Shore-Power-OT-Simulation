# OpenPLC Setup Guide — Shore Power OT Lab
## Step-by-step for Windows 10/11

---

## Step 1 — Install OpenPLC Runtime

1. Go to: https://autonomylogic.com/docs/installing-openplc-runtime-on-windows/
2. Download the Windows installer
3. Run installer — it installs OpenPLC Runtime as a service
4. Open browser → http://localhost:8080
5. Login: **user** `openplc` / **pass** `openplc`

---

## Step 2 — Upload the PLC Program

1. In OpenPLC web UI → click **Programs** in left sidebar
2. Click **Upload Program**
3. Select file: `openplc/shore_power.st`
4. Click **Upload**
5. Wait for compilation — you should see "Compilation successful"

---

## Step 3 — Configure Modbus Slave

OpenPLC Runtime exposes a Modbus TCP slave on port **502** by default.

1. In OpenPLC web UI → **Settings**
2. Scroll to **Slave Devices**
3. Make sure **Enable Modbus/TCP Slave** is checked
4. Port should be **502**
5. Click **Save Changes**

> **Note for Windows:** Port 502 requires admin. Either:
> - Run OpenPLC as Administrator, OR
> - Change port to **5020** in Settings (then update OPENPLC_PORT in modbus_bridge.py)

---

## Step 4 — Start the PLC

1. In OpenPLC web UI → **Dashboard**
2. Click **Start PLC**
3. Status should show **Running**
4. You should see scan cycle counter incrementing

---

## Step 5 — Run the Project

Open **two terminals**:

**Terminal 1 — Flask SCADA:**
```bash
cd shore-power-lab
python app.py
```

**Terminal 2 — Attack scripts (when ready to demo):**
```bash
cd shore-power-lab/attack_scripts

# ATK-01: Sensor spoofing
python atk01_sensor_spoof.py

# ATK-02: Breaker manipulation
python atk02_breaker_manipulation.py

# ATK-03: Relay bypass
python atk03_relay_bypass.py

# ATK-05: Load spike (protection works)
python atk05_load_spike.py

# Reset after any attack
python reset_plc.py
```

**Dashboard:** http://localhost:5000

---

## Variable Mapping in OpenPLC Editor

If you need to verify or recreate the program in OpenPLC Editor:

| Variable       | Address  | Type         | Description              |
|----------------|----------|--------------|--------------------------|
| current_raw    | %IW0     | INT (input)  | Current sensor ×10       |
| voltage_raw    | %IW1     | INT (input)  | Voltage sensor ×10       |
| temp_raw       | %IW2     | INT (input)  | Temperature ×10          |
| breaker_closed | %QX0.0   | BOOL (output)| Breaker coil             |
| alarm_active   | %QX0.1   | BOOL (output)| Alarm indicator          |
| relay_tripped  | %QX0.2   | BOOL (output)| Relay tripped flag       |
| manual_reset   | %MX0.0   | BOOL (memory)| Reset command from SCADA |
| relay_bypassed | %MX0.1   | BOOL (memory)| ATK-03 bypass flag       |

---

## Troubleshooting

**"Cannot connect to OpenPLC"**
- Check OpenPLC is Running (green status in web UI)
- Check port: try 502 first, then 5020
- On Windows, try running as Administrator

**"Compilation failed" when uploading .st file**
- OpenPLC Editor and Runtime must both be installed
- Check the .st file has no syntax errors
- Try OpenPLC Editor → compile first, then upload .pou

**"Modbus write failed"**
- OpenPLC must be in RUNNING state (not stopped)
- Check slave device settings in OpenPLC web UI

**Port 502 access denied on Windows**
- Open OpenPLC web UI → Settings → change Modbus port to 5020
- Update `OPENPLC_PORT = 5020` in `modbus_bridge.py`

---

## How the Integration Works

```
Python simulation (app.py)
        │
        │  every tick (0.8s):
        │  writes: current×10, voltage×10, temp×10
        ▼
OpenPLC Runtime ← modbus_bridge.py → Modbus TCP port 502
        │
        │  ladder logic runs every 100ms:
        │  checks overcurrent, UV, OV, overtemp
        │  sets: breaker_closed, alarm_active, relay_tripped
        ▼
modbus_bridge.py reads PLC outputs
        │
        ▼
Flask state updated with REAL PLC decisions
        │
        ▼
Dashboard shows live data from actual PLC
```

Attack scripts bypass the simulation entirely and write
directly to OpenPLC registers — just like a real attacker
on an OT network would.
