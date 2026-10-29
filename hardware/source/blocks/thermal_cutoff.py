"""Hardware over-temperature cutoff: a temperature switch that removes the drive of a group of
loads without any MCU or firmware in the path (CLAUDE.md rule 11).

    +3V3 -- TMP302A VS (100 nF), GND
    TRIPSET1 = VS, TRIPSET0 = GND        -> trip at 60 C (TMP302 Table 1, p7)
    HYSTSET = VS                         -> 10 C hysteresis (p5): released at about 50 C, so a hung
                                            MCU cannot make the loads cycle tightly at the trip point
    OUT (open drain, LOW when hot, p3)   = HW_OT_N, pulled up to +3V3 (10-100k, p4)
    HW_OT_N -- gate of Q_EN; Q_EN drain = RTN (the loads' return), source = GND
    HW_OT_N -- R_SENSE -- SENSE (a GPIO, so firmware can report the trip)

The loads (here the SSR drive MOSFETs) return through RTN, so a trip turns all of them off
whatever their gates say. The sense resistor sits between HW_OT_N and the GPIO: a GPIO driven
high by mistake cannot lift the gate while the switch sinks it. Pull-up to +3V3, not +5V: OUT and
the inputs are limited to 4 V (p4), and losing +3V3 then drops the gate, so the loads go OFF.
"""

from skidl import Net, subcircuit

from .spec import PartSpec, make


@subcircuit
def thermal_cutoff(
    rtn: Net,
    sense: Net,
    v3v3: Net,
    gnd: Net,
    *,
    switch: PartSpec,
    fet: PartSpec,
    r_pullup: PartSpec,
    r_sense: PartSpec,
    c_bypass: PartSpec,
) -> Net:
    u = make(switch)
    q = make(fet)
    rpu, rs, c = make(r_pullup), make(r_sense), make(c_bypass)
    ot_n = Net("HW_OT_N")
    u["VS"] += v3v3
    u["GND"] += gnd
    u["TRIPSET1"] += v3v3
    u["TRIPSET0"] += gnd
    u["HYSTSET"] += v3v3
    u["OUT"] += ot_n
    c[1] += v3v3
    c[2] += gnd
    rpu[1] += ot_n
    rpu[2] += v3v3
    q["G"] += ot_n
    q["D"] += rtn
    q["S"] += gnd
    rs[1] += ot_n
    rs[2] += sense
    return ot_n
