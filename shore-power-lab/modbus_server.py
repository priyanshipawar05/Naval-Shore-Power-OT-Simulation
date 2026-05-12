"""
modbus_server.py  — Shore Power OT Lab
Compatible with pymodbus 3.x (tested on 3.6+, Python 3.12)
Educational Simulation Only.

Register Map:
  Holding Registers (FC03):
    addr 0 → Voltage ×10       (4400 = 440.0V)
    addr 1 → Current ×10       ( 600 =  60.0A)
    addr 2 → Load ×10          ( 260 =  26.0kW)
    addr 3 → Temp ×10          ( 540 =  54.0°C)
    addr 4 → Frequency ×100    (5000 =  50.00Hz)
    addr 5 → Power Factor ×100 (  92 =   0.92)

  Coils (FC01/FC05):
    addr 0 → Breaker  1=CLOSED 0=OPEN
    addr 1 → Relay    1=ARMED  0=OFF
    addr 2 → Alarm    1=ALARM  0=NONE
"""

import threading
import logging

logging.basicConfig(level=logging.WARNING)

MODBUS_PORT = 5020

_context = None
_lock    = threading.Lock()


def _build_context():
    """
    Build Modbus datastore.
    Tries multiple import paths to support different pymodbus 3.x builds.
    """
    # ── Try 1: standard pymodbus 3.x path ─────────────────────
    try:
        from pymodbus.datastore import ModbusServerContext
        from pymodbus.datastore import ModbusSlaveContext
        from pymodbus.datastore import ModbusSequentialDataBlock

        coils = ModbusSequentialDataBlock(0, [1, 1, 0, 0, 0, 0, 0, 0])
        hreg  = ModbusSequentialDataBlock(0, [4400, 600, 260, 540, 5000, 92, 0, 0])
        slave = ModbusSlaveContext(co=coils, hr=hreg, zero_mode=True)
        return ModbusServerContext(slaves=slave, single=True)
    except ImportError:
        pass

    # ── Try 2: context submodule ───────────────────────────────
    try:
        from pymodbus.datastore import ModbusServerContext
        from pymodbus.datastore.context import ModbusSlaveContext
        from pymodbus.datastore.store  import ModbusSequentialDataBlock

        coils = ModbusSequentialDataBlock(0, [1, 1, 0, 0, 0, 0, 0, 0])
        hreg  = ModbusSequentialDataBlock(0, [4400, 600, 260, 540, 5000, 92, 0, 0])
        slave = ModbusSlaveContext(co=coils, hr=hreg, zero_mode=True)
        return ModbusServerContext(slaves=slave, single=True)
    except ImportError:
        pass

    # ── Try 3: store submodule only ────────────────────────────
    try:
        from pymodbus.datastore import ModbusServerContext
        from pymodbus.datastore.store import ModbusSequentialDataBlock
        from pymodbus.datastore.store import ModbusSlaveContext

        coils = ModbusSequentialDataBlock(0, [1, 1, 0, 0, 0, 0, 0, 0])
        hreg  = ModbusSequentialDataBlock(0, [4400, 600, 260, 540, 5000, 92, 0, 0])
        slave = ModbusSlaveContext(co=coils, hr=hreg, zero_mode=True)
        return ModbusServerContext(slaves=slave, single=True)
    except ImportError:
        pass

    # ── All failed → print diagnostic and disable Modbus ──────
    import pymodbus, pymodbus.datastore as ds, pymodbus.datastore.store as st
    print(f"\n[MODBUS] WARNING: Could not build context.")
    print(f"  pymodbus version : {pymodbus.__version__}")
    print(f"  datastore exports: {[x for x in dir(ds) if not x.startswith('_')]}")
    print(f"  store exports    : {[x for x in dir(st) if not x.startswith('_')]}")
    print(f"  Modbus TCP will be DISABLED — Flask dashboard still works.\n")
    return None


def update_registers(voltage, current, load, temp, freq, pf,
                     breaker_closed, relay_armed, alarm):
    if _context is None:
        return
    with _lock:
        slave = _context[0]
        slave.setValues(3, 0, [
            int(voltage * 10),
            int(current * 10),
            int(load    * 10),
            int(temp    * 10),
            int(freq    * 100),
            int(pf      * 100),
        ])
        slave.setValues(1, 0, [
            int(breaker_closed),
            int(relay_armed),
            int(alarm),
        ])


def read_coils():
    if _context is None:
        return {}
    with _lock:
        slave = _context[0]
        coils = slave.getValues(1, 0, count=3)
        return {
            "breaker_closed": bool(coils[0]),
            "relay_armed":    bool(coils[1]),
            "alarm":          bool(coils[2]),
        }


def start_modbus_server():
    global _context
    _context = _build_context()

    if _context is None:
        print("[MODBUS] Skipping Modbus TCP server — context unavailable.")
        return None

    def _run():
        try:
            from pymodbus.server import StartTcpServer
            print(f"[MODBUS] TCP server on 0.0.0.0:{MODBUS_PORT}")
            StartTcpServer(context=_context, address=("0.0.0.0", MODBUS_PORT))
        except ImportError:
            try:
                from pymodbus.server.sync import StartTcpServer
                print(f"[MODBUS] TCP server on 0.0.0.0:{MODBUS_PORT} (sync)")
                StartTcpServer(context=_context, address=("0.0.0.0", MODBUS_PORT))
            except Exception as e:
                print(f"[MODBUS] Server failed to start: {e}")
        except Exception as e:
            print(f"[MODBUS] Server error: {e}")

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t
