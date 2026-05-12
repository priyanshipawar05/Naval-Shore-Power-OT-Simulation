"""
modbus_bridge.py — Shore Power OT Lab
OpenPLC Runtime via Modbus TCP — ALL protection decisions made by PLC ladder logic.

MODBUS REGISTER MAP (%MW = holding registers at offset 1024):
  MW0 (reg 1024) → current_raw  (Python writes: current * 10)
  MW1 (reg 1025) → voltage_raw  (Python writes: voltage * 10)
  MW2 (reg 1026) → temp_raw     (Python writes: temp * 10)
  MW3 (reg 1027) → breaker_out  (Python READS: 1=closed, 0=open)
  MW4 (reg 1028) → alarm_out    (Python READS: 1=alarm, 0=normal)
  MW5 (reg 1029) → tripped_out  (Python READS: 1=tripped, 0=normal)
  MW6 (reg 1030) → reset_cmd    (Python writes 1 to reset)
  MW7 (reg 1031) → bypass_cmd   (Python writes 1 to bypass — ATK-03)
"""

import threading
import time

try:
    from pymodbus.client import ModbusTcpClient
    PYMODBUS_AVAILABLE = True
except ImportError:
    PYMODBUS_AVAILABLE = False

OPENPLC_HOST = "127.0.0.1"
OPENPLC_PORT = 20502
MW_BASE      = 1024  # %MW registers start at Modbus address 1024

_client    = None
_connected = False
_lock      = threading.Lock()


def connect():
    global _client, _connected
    if not PYMODBUS_AVAILABLE:
        return False
    try:
        _client = ModbusTcpClient(OPENPLC_HOST, port=OPENPLC_PORT)
        result  = _client.connect()
        _connected = result
        if result:
            print(f"[BRIDGE] ✔ Connected to OpenPLC Runtime ({OPENPLC_HOST}:{OPENPLC_PORT})")
        else:
            print(f"[BRIDGE] ✘ Could not connect to OpenPLC")
        return result
    except Exception as e:
        _connected = False
        print(f"[BRIDGE] ✘ Could not connect: {e}")
        return False


def is_connected():
    return _connected and _client is not None


def get_status():
    return {
        "connected": _connected,
        "host":      OPENPLC_HOST,
        "port":      OPENPLC_PORT,
    }


def write_sensors(current, voltage, temp):
    """Write sensor values to PLC MW0-MW2. PLC ladder decides everything."""
    global _connected
    if not is_connected():
        return False
    try:
        regs = [
            max(0, min(32767, int(current * 10))),
            max(0, min(32767, int(voltage * 10))),
            max(0, min(32767, int(temp    * 10))),
        ]
        result = _client.write_registers(MW_BASE, regs)
        if result.isError():
            _connected = False
            return False
        return True
    except Exception:
        _connected = False
        return False


def read_plc_outputs():
    """Read PLC protection decisions from MW3-MW5. These are set by ladder logic."""
    global _connected
    if not is_connected():
        return None
    try:
        r = _client.read_holding_registers(MW_BASE + 3, count=3)
        if r.isError():
            return None
        return {
            "breaker_closed": r.registers[0] == 1,  # MW3
            "alarm_active":   r.registers[1] == 1,  # MW4
            "relay_tripped":  r.registers[2] == 1,  # MW5
        }
    except Exception:
        _connected = False
        return None


def send_reset():
    """Write reset command to MW6 — PLC ladder clears latched state."""
    global _connected
    if not is_connected():
        return False
    try:
        _client.write_registers(MW_BASE + 6, [1])
        time.sleep(0.15)
        _client.write_registers(MW_BASE + 6, [0])
        return True
    except Exception:
        _connected = False
        return False


def set_relay_bypass(bypass: bool):
    """ATK-03: Write bypass flag to MW7 — disables all protection rungs in PLC."""
    global _connected
    if not is_connected():
        return False
    try:
        _client.write_registers(MW_BASE + 7, [1 if bypass else 0])
        return True
    except Exception:
        _connected = False
        return False


def force_breaker_open():
    """ATK-02: Force breaker open by writing extreme current directly to PLC input."""
    global _connected
    if not is_connected():
        return False
    try:
        # Write 200A — far above 100A threshold — PLC ladder will trip
        _client.write_registers(MW_BASE, [2000, 4400, 540])
        return True
    except Exception:
        _connected = False
        return False


def start_reconnect_thread():
    """Background thread that reconnects if OpenPLC drops."""
    def _reconnect():
        global _connected
        while True:
            time.sleep(5)
            if not _connected:
                connect()
            elif is_connected():
                try:
                    _client.read_holding_registers(MW_BASE, count=1)
                    print(f"[BRIDGE] ✔ Connected to OpenPLC Runtime ({OPENPLC_HOST}:{OPENPLC_PORT})")
                except Exception:
                    _connected = False
    t = threading.Thread(target=_reconnect, daemon=True)
    t.start()
