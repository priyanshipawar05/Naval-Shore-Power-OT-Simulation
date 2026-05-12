"""
attack_scripts/reset_plc.py
─────────────────────────────────────────────────────────────
Reset PLC to normal operating state after any attack.
Writes manual reset command to PLC and restores sensor values.
"""
import sys, time
try:
    from pymodbus.client import ModbusTcpClient
except ImportError:
    from pymodbus.client.sync import ModbusTcpClient

def reset(host="127.0.0.1", port=502):
    print("[RESET] Connecting to OpenPLC...")
    client = ModbusTcpClient(host=host, port=port, timeout=3)
    if not client.connect():
        print(f"[!] Cannot connect to {host}:{port}"); sys.exit(1)

    print("[RESET] Clearing relay bypass flag (coil 4)...")
    client.write_coil(4, False, slave=1)

    print("[RESET] Sending manual reset command (coil 3)...")
    client.write_coil(3, True, slave=1)
    time.sleep(0.2)
    client.write_coil(3, False, slave=1)

    print("[RESET] Restoring nominal sensor values...")
    client.write_registers(0, [600, 4400, 540], slave=1)  # 60A, 440V, 54°C

    time.sleep(0.5)
    coils = client.read_coils(0, count=3, slave=1)
    if not coils.isError():
        print(f"[RESET] Breaker: {'CLOSED' if coils.bits[0] else 'OPEN'}")
        print(f"[RESET] Alarm:   {'ON' if coils.bits[1] else 'OFF'}")
        print(f"[RESET] Tripped: {'YES' if coils.bits[2] else 'NO'}")

    client.close()
    print("[RESET] Done. System should be back to normal.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=502, type=int)
    args = parser.parse_args()
    reset(args.host, args.port)
