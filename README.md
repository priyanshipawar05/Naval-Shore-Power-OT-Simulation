# Naval Shore Power Distribution OT Simulation

> Educational OT/ICS cybersecurity simulation of a naval shore power distribution system using OpenPLC v3, Modbus TCP, Python Flask, and a custom SCADA HMI.

---

## Overview

This project simulates a cyber-physical Operational Technology (OT) environment representing a naval shore-to-ship power distribution system.

The simulation demonstrates how insecure industrial communication protocols such as Modbus TCP can be exploited to perform cyber-physical attacks against critical infrastructure systems.

The project integrates:
- OpenPLC v3 runtime
- Modbus TCP communication
- Flask backend APIs
- Custom SCADA/HMI dashboard
- PLC ladder logic
- Real-time attack simulation
- Cyber-physical consequence modeling

The system visualizes electrical parameters, breaker states, relay logic, event logs, thermal behavior, and live attack impact in real time.

---

# Features

- Real-time SCADA dashboard
- OpenPLC-based PLC simulation
- Modbus TCP integration
- Live electrical parameter monitoring
- Custom attack execution panel
- Simulated cyber-physical consequences
- REST API for control and monitoring
- Real-time event logging
- OT attack scenario visualization
- Cyber Kill Chain inspired escalation model

---

# Environment

The project was developed on a Windows host system using WSL Ubuntu for OpenPLC runtime execution.

## Environment Stack

- Windows 11
- WSL Ubuntu 22.04
- OpenPLC v3
- Python 3.11
- Flask
- pymodbus

---

# Project Structure

```text
shore-power-lab/
│
├── attack_scripts/
│   ├── atk01_sensor_spoof.py
│   ├── atk02_breaker_manipulation.py
│   ├── atk03_relay_bypass.py
│   ├── atk04_false_telemetry.py
│   ├── atk05_load_spike.py
│   └── reset_plc.py
│
├── openplc/
│   ├── shore_power.st
│   └── SETUP_GUIDE.md
│
├── templates/
│   └── shore_power_scada.html
│
├── screenshots/
│
├── docs/
│
├── app.py
├── modbus_bridge.py
├── modbus_server.py
├── requirements.txt
└── README.md
```

---

# System Architecture

```text
SCADA Dashboard (HTML/CSS/JS)
              ↓
        Flask Backend API
              ↓
         Modbus TCP
              ↓
       OpenPLC Runtime
              ↓
          PLC Logic
              ↓
  Simulated Shore Power System
```

---

# Simulated OT Attack Scenarios

| Attack Scenario | Technique | Simulated Impact |
|---|---|---|
| Sensor Spoofing | Register manipulation | Thermal shutdown |
| Breaker Manipulation | Unauthorized Modbus coil write | Ship blackout |
| Relay Bypass | PLC protection logic tampering | Equipment damage |
| False Telemetry Injection | SCADA deception | Voltage collapse |
| Load Spike Attack | Overcurrent injection | Relay trip / isolation |

---

# Real-World Inspiration

The simulated attack scenarios are inspired by major industrial cyber incidents including:

- Stuxnet (2010)
- Industroyer / CrashOverride (2016)

The project demonstrates how unauthenticated industrial protocols can enable cyber-physical attacks against critical infrastructure.

---

# Modbus TCP Security Findings

The simulation demonstrates several inherent weaknesses of Modbus TCP:

- No authentication
- No encryption
- No access control
- Direct register manipulation possible
- PLC protection logic bypass achievable
- False telemetry can deceive operators

A single unauthorized Modbus connection can manipulate PLC behavior and trigger physical process impact.

---

# OpenPLC Setup (WSL Ubuntu)

## Install OpenPLC

Inside WSL Ubuntu:

```bash
git clone https://github.com/thiagoralves/OpenPLC_v3.git
cd OpenPLC_v3
./install.sh linux
```

---

## Start OpenPLC Runtime

```bash
cd ~/OpenPLC_v3/webserver
python3 webserver.py
```

---

## Access OpenPLC

```text
http://localhost:8080
```

---

## Load PLC Program

Upload:

```text
openplc/shore_power.st
```

Then start the runtime from the OpenPLC dashboard.

---

# Installation

## Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/Naval-Shore-Power-OT-Simulation.git
cd Naval-Shore-Power-OT-Simulation
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Start Application

```bash
python app.py
```

---

## Access Dashboard

```text
http://localhost:5000
```

---

# REST API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/state` | Retrieve full system state |
| GET | `/api/log` | Retrieve event logs |
| POST | `/api/attack` | Trigger attack scenario |
| POST | `/api/reset` | Reset system |
| POST | `/api/breaker` | Toggle breaker state |

---


# Educational Objectives

This project was developed to:
- Study OT/ICS cybersecurity concepts
- Demonstrate cyber-physical attack impact
- Explore insecure industrial protocols
- Simulate SCADA/PLC environments
- Understand operator deception techniques
- Analyze Modbus TCP vulnerabilities

---



# Disclaimer

This project was developed strictly for educational and cybersecurity research purposes.

It does not represent any real naval infrastructure, operational environment, or classified system.

All data, architectures, and simulations are synthetic and intended solely for controlled laboratory demonstration and academic research.
