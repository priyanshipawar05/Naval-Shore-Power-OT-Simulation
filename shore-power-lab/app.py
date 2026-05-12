"""
app.py — Shore Power OT Lab (OpenPLC-first architecture)
Python ONLY generates sensor values.
OpenPLC makes ALL protection decisions.
Educational Simulation Only.
"""
import time, random, threading, logging
from datetime import datetime
from collections import deque
from flask import Flask, jsonify, request, render_template
import modbus_server as mb
import modbus_bridge as bridge

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel(logging.ERROR)

NOMINAL_VOLTAGE = 440.0; NOMINAL_CURRENT = 60.0; NOMINAL_LOAD = 26.0
NOMINAL_TEMP = 54.0;     NOMINAL_CTEMP   = 41.0; NOMINAL_FREQ = 50.0
NOMINAL_PF   = 0.92;     TICK_INTERVAL   = 0.8

_lock      = threading.Lock()
_event_log = deque(maxlen=200)
_state = {
    "voltage": NOMINAL_VOLTAGE, "current": NOMINAL_CURRENT,
    "load":    NOMINAL_LOAD,    "freq":    NOMINAL_FREQ,
    "pf":      NOMINAL_PF,      "temp":    NOMINAL_TEMP,
    "ctemp":   NOMINAL_CTEMP,
    # PLC decisions — read from OpenPLC, never written by Python
    "breaker_closed": True, "relay_armed": True, "alarm": False,
    # Attack tracking
    "attack_mode": None, "spoofed": False, "false_telemetry": False,
    "consequence": None, "phase": "normal",
    # Display values
    "display_voltage": NOMINAL_VOLTAGE, "display_current": NOMINAL_CURRENT,
    "tick": 0, "uptime": 0,
}

def _log(msg, level="info"):
    entry = {"ts": datetime.now().strftime("%H:%M:%S"), "msg": msg, "level": level}
    _event_log.appendleft(entry)
    prefix = {"info":"i","normal":"✔","warn":"⚠","alarm":"🔴"}.get(level," ")
    print(f"[{entry['ts']}] {prefix} {msg}")

def _jitter(s=1.0):
    return (random.random()-0.5)*2*s

def _tick(start_time):
    s = _state
    s["tick"]  += 1
    s["uptime"] = int(time.time()-start_time)
    mode = s["attack_mode"]

    # NORMAL
    if mode is None:
        s["voltage"] = NOMINAL_VOLTAGE+_jitter(3)
        s["current"] = NOMINAL_CURRENT+_jitter(4)
        s["temp"]    = NOMINAL_TEMP+_jitter(2)
        s["ctemp"]   = NOMINAL_CTEMP+_jitter(1.5)
        s["freq"]    = NOMINAL_FREQ+_jitter(0.05)
        s["pf"]      = round(NOMINAL_PF+_jitter(0.01),3)
        s["consequence"] = None; s["phase"] = "normal"

    # ATK-01: Python writes fake low current to PLC (spoofed=True)
    # PLC sees 1.8A → never trips. Real current → transformer overheats.
    elif mode == "spoof":
        t = s["tick"]
        s["current"] = min(s["current"]+1.8, 148)
        s["voltage"] = NOMINAL_VOLTAGE-(max(0,t-10)*0.4)+_jitter(2)
        s["temp"]   += 1.2; s["ctemp"] += 0.4
        if t<=8:
            s["phase"] = "escalating"
            if t==3: _log(f"⚠ PLC sees {s['current']*0.3:.0f}A — actual {s['current']:.0f}A","warn")
            if t==6: _log(f"⚠ Transformer {s['temp']:.0f}°C — relay blinded","warn")
        elif t<=16:
            s["phase"] = "critical"
            if t==9:  _log(f"🔥 CRITICAL: {s['temp']:.0f}°C — PLC thermal alarm firing","alarm"); s["alarm"]=True
            if t==12: _log(f"🔥 {s['temp']:.0f}°C — winding insulation degrading","alarm")
        else:
            if s["phase"] != "shutdown":
                s["phase"]="shutdown"; s["spoofed"]=False
                s["consequence"]="THERMAL_SHUTDOWN"; s["attack_mode"]="consequence"
                _log("🚨 THERMAL FUSE BLOWN — damage done before shutdown","alarm")
                _log(f"   {s['temp']:.0f}°C — PLC was blinded entire time","alarm")

    # ATK-02: handled by attack script directly writing to PLC coil
    # Python just logs cascading consequences
    elif mode == "breaker":
        t = s["tick"]; s["phase"]="blackout"; s["consequence"]="SHIP_BLACKOUT"
        msgs = {1:"🚨 BLACKOUT — rogue Modbus write forced breaker open",
                2:"   Navigation OFFLINE. Communication OFFLINE.",
                3:"   Cooling OFFLINE — equipment heating",
                4:"   Battery backup: 20 min reserve"}
        if t in msgs: _log(msgs[t],"alarm")
        if t==6: s["attack_mode"]="consequence"; _log("🚨 Single unauth Modbus write = full blackout","alarm")

    # ATK-03: attack script sets PLC bypass flag
    # Python writes REAL high current — PLC receives it but ignores (bypassed=TRUE)
    elif mode == "relay":
        t = s["tick"]
        s["current"]=min(s["current"]+2.2,155); s["temp"]+=1.5; s["ctemp"]+=1.0
        s["voltage"]=NOMINAL_VOLTAGE+_jitter(3)
        if t<=6:
            s["phase"]="escalating"
            if t%2==0: _log(f"⚠ {s['current']:.0f}A — PLC relay BYPASSED, no trip","alarm")
        elif t<=12:
            s["phase"]="critical"
            if t==7:  _log(f"🔥 Cable {s['ctemp']:.0f}°C — insulation burning","alarm"); s["alarm"]=True
            if t==10: _log(f"🔥 {s['current']:.0f}A in 100A cable","alarm")
        else:
            if s["phase"]!="lockout":
                s["phase"]="lockout"; s["voltage"]=0.0; s["current"]=0.0
                s["consequence"]="EQUIPMENT_DAMAGE"; s["attack_mode"]="consequence"
                _log("🚨 CABLE BURNED OPEN — physical failure","alarm")
                _log(f"   {s['ctemp']:.0f}°C — insulation destroyed, 48h downtime","alarm")

    # ATK-04: Python writes fake 440V to PLC (false_telemetry=True)
    # PLC UV protection never fires. Real voltage drops silently.
    elif mode == "telemetry":
        t = s["tick"]
        s["voltage"]=max(s["voltage"]-1.2,338); s["current"]=NOMINAL_CURRENT+_jitter(3)
        s["temp"]=NOMINAL_TEMP+_jitter(2); s["freq"]=max(s["freq"]-0.04,48.2)
        if t<=10:
            s["phase"]="deceiving"
            if t==4: _log(f"⚠ PLC reg=440V — real={s['voltage']:.0f}V","warn")
            if t==10: _log(f"⚠ Electronics at {s['voltage']:.0f}V","warn"); s["alarm"]=True
        elif t<=17:
            s["phase"]="degrading"
            if t==11: _log(f"🔴 {s['voltage']:.0f}V — radar errors","alarm")
            if t==17: _log("🔴 PLC still sees 440V — operator unaware","alarm")
        else:
            if s["phase"]!="collapse":
                s["phase"]="collapse"; s["false_telemetry"]=False
                s["consequence"]="VOLTAGE_COLLAPSE"; s["attack_mode"]="consequence"
                _log("🚨 Telemetry stopped — PLC now sees real voltage","alarm")
                _log(f"   UV relay trips at {s['voltage']:.0f}V — too late","alarm")
                _log("   18 ticks of equipment damage already done","alarm")

    # ATK-05: Python sends high current to PLC
    # PLC relay ARMED → overcurrent rung fires → PLC trips breaker itself
    elif mode == "overload":
        t = s["tick"]
        s["current"]=min(s["current"]+6,165); s["voltage"]=max(s["voltage"]-1,375); s["temp"]+=0.6
        if t%2==0: _log(f"⚠ Load spike: {s['current']:.0f}A → PLC threshold 100A","warn")
        # PLC will trip on its own — check if it already did
        if not s["breaker_closed"] and s["phase"]!="tripped":
            s["phase"]="tripped"; s["consequence"]="RELAY_TRIP_PROTECTION"; s["attack_mode"]="consequence"
            _log(f"⚡ PLC RELAY TRIPPED — ladder logic detected {s['current']:.0f}A","normal")
            _log("   Breaker opened by PLC in <100ms — equipment PROTECTED","normal")

    elif mode == "consequence":
        pass

    # Load calculation
    if not s["breaker_closed"]: s["current"]=0.0; s["load"]=0.0
    elif s["voltage"]>0: s["load"]=round(s["voltage"]*s["current"]/1000,2)

    s["display_voltage"] = 440.0 if s["false_telemetry"] else round(s["voltage"],1)
    s["display_current"] = round(s["current"]*0.3,1) if s["spoofed"] else round(s["current"],1)


def _push_modbus():
    s = _state
    if bridge.is_connected():
        # Write sensor values to PLC (possibly faked for attacks)
        bridge.write_sensors(
            current = s["current"]*0.3 if s["spoofed"] else s["current"],
            voltage = 440.0 if s["false_telemetry"] else s["voltage"],
            temp    = s["temp"],
        )
        # Read REAL PLC decisions — never override these
        plc_out = bridge.read_plc_outputs()
        if plc_out and s["phase"] not in ("lockout",):
            s["breaker_closed"] = plc_out["breaker_closed"]
            s["alarm"]          = plc_out["alarm_active"] or s["alarm"]
            s["relay_armed"]    = not plc_out["relay_tripped"]
    else:
        mb.update_registers(
            voltage=s["display_voltage"], current=s["display_current"],
            load=s["load"], temp=s["temp"], freq=s["freq"], pf=s["pf"],
            breaker_closed=s["breaker_closed"], relay_armed=s["relay_armed"], alarm=s["alarm"],
        )
        if s["relay_armed"] and s["current"]>100.0 and s["attack_mode"] not in ("spoof","relay","telemetry"):
            s["breaker_closed"]=False; s["relay_armed"]=False; s["alarm"]=True


def _simulation_loop():
    start_time = time.time()
    while True:
        time.sleep(TICK_INTERVAL)
        with _lock:
            _tick(start_time)
            _push_modbus()


@app.route("/")
def index(): return render_template("index.html")

@app.route("/api/state")
def api_state():
    with _lock:
        sc = dict(_state); sc["bridge"] = bridge.get_status()
        return jsonify(sc)

@app.route("/api/log")
def api_log():
    n = int(request.args.get("n",60))
    return jsonify(list(_event_log)[:n])

@app.route("/api/attack", methods=["POST"])
def api_attack():
    data = request.json or {}
    atype = data.get("type","")
    if atype not in {"spoof","breaker","relay","telemetry","overload"}:
        return jsonify({"error":"invalid type"}),400
    with _lock:
        s = _state
        s["attack_mode"]=atype; s["tick"]=0; s["phase"]="escalating"; s["consequence"]=None
        s["spoofed"]=False; s["false_telemetry"]=False

        if atype=="spoof":
            s["spoofed"]=True
            _log("ATK-01: Sensor spoofing — fake current sent to PLC register","alarm")
            _log("   PLC sees 1.8A — relay blinded — real current climbing","alarm")
        elif atype=="breaker":
            if bridge.is_connected(): bridge.force_breaker_open()
            else: s["breaker_closed"]=False
            _log("ATK-02: Rogue Modbus FC05 → PLC breaker coil forced OPEN","alarm")
        elif atype=="relay":
            if bridge.is_connected(): bridge.set_relay_bypass(True)
            else: s["relay_armed"]=False
            _log("ATK-03: Bypass flag set in PLC — all protection rungs disabled","alarm")
        elif atype=="telemetry":
            s["false_telemetry"]=True
            _log("ATK-04: False telemetry — 440V sent to PLC voltage register","alarm")
        elif atype=="overload":
            _log("ATK-05: Load spike — high current sent to PLC (relay armed)","normal")
    return jsonify({"status":"ok","attack":atype})

@app.route("/api/reset", methods=["POST"])
def api_reset():
    with _lock:
        s = _state
        s.update({
            "attack_mode":None,"spoofed":False,"false_telemetry":False,
            "consequence":None,"phase":"normal",
            "voltage":NOMINAL_VOLTAGE,"current":NOMINAL_CURRENT,
            "load":NOMINAL_LOAD,"temp":NOMINAL_TEMP,"ctemp":NOMINAL_CTEMP,
            "freq":NOMINAL_FREQ,"pf":NOMINAL_PF,"alarm":False,"tick":0,
            "display_voltage":NOMINAL_VOLTAGE,"display_current":NOMINAL_CURRENT,
        })
        if bridge.is_connected():
            bridge.write_sensors(NOMINAL_CURRENT,NOMINAL_VOLTAGE,NOMINAL_TEMP)
            bridge.set_relay_bypass(False)
            bridge.send_reset()
            _log("SYSTEM RESET — nominal values sent to PLC, latch cleared","normal")
        else:
            s["breaker_closed"]=True; s["relay_armed"]=True
            _log("SYSTEM RESET — simulation mode","normal")
    return jsonify({"status":"ok"})

@app.route("/api/breaker", methods=["POST"])
def api_breaker():
    data=request.json or {}; state=data.get("state",True)
    with _lock:
        if bridge.is_connected():
            bridge.force_breaker_open() if not state else bridge.send_reset()
        else: _state["breaker_closed"]=state
    return jsonify({"status":"ok","breaker":state})


if __name__ == "__main__":
    print("="*55)
    print("  SHORE POWER OT LAB — Educational Simulation")
    print("  NOT a real naval system.")
    print("="*55)
    print("  Attempting OpenPLC connection...")
    if bridge.connect():
        print("  ✔ OpenPLC connected — REAL PLC ladder logic active")
        print("  ✔ Python: sensor values only")
        print("  ✔ OpenPLC: all protection decisions")
        bridge.start_reconnect_thread()
    else:
        print("  ✘ OpenPLC not found — SIMULATION mode")
        mb.start_modbus_server()

    threading.Thread(target=_simulation_loop, daemon=True).start()
    _log("Shore Power OT Simulation starting...","info")
    _log("Transformer energized — 11kV → 440V nominal","normal")
    _log("Protection relay armed","normal")
    _log("Ship connected — 26 kW load nominal","normal")
    _log("SCADA online — all systems normal","normal")
    _log("Simulation engine started","info")
    print(f"\n  Dashboard → http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
