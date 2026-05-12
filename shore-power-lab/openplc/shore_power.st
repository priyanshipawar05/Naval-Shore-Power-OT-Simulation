PROGRAM shore_power_plc
VAR
    i_amp    : REAL;
    v_volt   : REAL;
    t_deg    : REAL;
    uv_count : INT;
    latched  : BOOL;
END_VAR
VAR_EXTERNAL
    current_raw : INT;
    voltage_raw : INT;
    temp_raw    : INT;
    breaker_out : INT;
    alarm_out   : INT;
    tripped_out : INT;
    reset_cmd   : INT;
    bypass_cmd  : INT;
END_VAR
i_amp  := INT_TO_REAL(current_raw) / 10.0;
v_volt := INT_TO_REAL(voltage_raw) / 10.0;
t_deg  := INT_TO_REAL(temp_raw)    / 10.0;
IF reset_cmd = 1 THEN
    latched:=FALSE; alarm_out:=0; tripped_out:=0; breaker_out:=1; uv_count:=0; reset_cmd:=0;
END_IF;
IF bypass_cmd = 0 THEN
    IF NOT latched THEN
        IF i_amp > 100.0 THEN
            latched:=TRUE; tripped_out:=1; alarm_out:=1; breaker_out:=0;
        END_IF;
    END_IF;
END_IF;
IF bypass_cmd = 0 THEN
    IF NOT latched THEN
        IF v_volt > 480.0 THEN
            latched:=TRUE; tripped_out:=1; alarm_out:=1; breaker_out:=0;
        END_IF;
    END_IF;
END_IF;
IF bypass_cmd = 0 THEN
    IF NOT latched THEN
        IF v_volt < 380.0 THEN
            IF v_volt > 0.0 THEN uv_count:=uv_count+1; END_IF;
        ELSE
            uv_count:=0;
        END_IF;
        IF uv_count >= 5 THEN
            latched:=TRUE; tripped_out:=1; alarm_out:=1; breaker_out:=0; uv_count:=0;
        END_IF;
    END_IF;
END_IF;
IF t_deg > 90.0 THEN alarm_out:=1; END_IF;
IF latched THEN breaker_out:=0; tripped_out:=1; END_IF;
END_PROGRAM

CONFIGURATION Config0
VAR_GLOBAL
    current_raw AT %MW0 : INT;
    voltage_raw AT %MW1 : INT;
    temp_raw    AT %MW2 : INT;
    breaker_out AT %MW3 : INT;
    alarm_out   AT %MW4 : INT;
    tripped_out AT %MW5 : INT;
    reset_cmd   AT %MW6 : INT;
    bypass_cmd  AT %MW7 : INT;
END_VAR
    RESOURCE Res0 ON PLC
        TASK task0(INTERVAL := T#100ms, PRIORITY := 0);
        PROGRAM inst0 WITH task0 : shore_power_plc;
    END_RESOURCE
END_CONFIGURATION
