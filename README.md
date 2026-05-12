# Shore Power OT Lab — BTech Major Project

## Naval Dockyard Shore Power Distribution System — OT Cybersecurity Simulation

> **Educational Simulation Only — Not a real naval system.**

---

## What This Is

A full-stack OT (Operational Technology) cybersecurity testbed that simulates a naval dockyard shore power distribution system. It runs a real Modbus TCP server alongside a Flask web server with a live SCADA dashboard.

You can trigger cyber attack scenarios and watch them affect:
- Modbus registers in real time
- The SCADA dashboard
- Protection relay and breaker behavior
- Thermal and electrical parameters

---

## Stack

```
shore-power-lab/
├── app.py               Flask server + simulation engine
├── modbus_server.py     Modbus TCP server (pymodbus)
├── templates/
│   └── index.html       SCADA dashboard (polls Flask API)
└── requirements.txt
```

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run
```bash
python app.py
```

### 3. Open dashboard
```
http://localhost:5000
```

### 4. (Optional) Connect a real Modbus client
```
Host: localhost
Port: 5020
```
Tools you can use: **ModScan32**, **QModMaster**, or your own pymodbus script.

---

## REST API

| Method | Endpoint       | Body / Params               | Description            |
|--------|---------------|-----------------------------|------------------------|
| GET    | /api/state    | —                           | Full system state JSON |
| GET    | /api/log      | ?n=60                       | Last N log entries     |
| POST   | /api/attack   | {"type": "spoof"}           | Trigger attack         |
| POST   | /api/reset    | —                           | Reset to nominal       |
| POST   | /api/breaker  | {"state": true}             | Manual breaker toggle  |

### Attack types
| Type        | Effect                                                     |
|-------------|-----------------------------------------------------------|
| `spoof`     | Falsify current sensor → relay blinded → overheating      |
| `breaker`   | Force breaker OPEN via Modbus write → ship blackout       |
| `relay`     | Bypass protection relay → unsafe current allowed          |
| `telemetry` | SCADA shows 440V while actual voltage degrades silently   |
| `overload`  | Inject load spike → relay trips → breaker opens           |

---

## Modbus Register Map

### Holding Registers (FC03, values ×10 or ×100)
| Address | Register | Description              | Scale |
|---------|----------|--------------------------|-------|
| 0       | 40001    | Voltage (V)              | ×10   |
| 1       | 40002    | Current (A)              | ×10   |
| 2       | 40003    | Load (kW)                | ×10   |
| 3       | 40004    | Transformer Temp (°C)    | ×10   |
| 4       | 40005    | Frequency (Hz)           | ×100  |
| 5       | 40006    | Power Factor             | ×100  |

### Coils (FC01 read / FC05 write)
| Address | Coil  | Description   | Values          |
|---------|-------|---------------|-----------------|
| 0       | 00001 | Breaker State | 1=CLOSED 0=OPEN |
| 1       | 00002 | Relay Armed   | 1=ARMED 0=OFF   |
| 2       | 00003 | Alarm Flag    | 1=ALARM 0=NONE  |

---

## Physics Model

```
Load (kW)  = Voltage × Current / 1000
Current    = Load / Voltage          (simplified)
Relay trip = Current > 100A         (overcurrent threshold)
```

Sensor spoofing: register 40002 is written with current × 0.3 (fake low value).
The real internal current continues to rise — relay gets the fake value.

---


## Disclaimer
This is an academic educational simulation.
It does not model any real naval installation, dockyard, or classified system.
All data is synthetic and randomly generated.
