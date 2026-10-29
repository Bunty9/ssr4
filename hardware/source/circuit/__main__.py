"""ssr4 top level: 4-channel 230 VAC SSR switch with an ESP32-C3-MINI-1 (ESPHome).

Sheets: power (mains in, fuse, MOV, HLK-PM01, USB VBUS, 3.3 V LDO), mcu (module, straps, buttons,
USB, NTC, status LED), and four ssr_channel blocks. Requirements: spec/requirements.md "ssr4".
Every computed value below comes from blocks/calc.py fed by verified datasheet params
(blocks.spec.verified_param), so the build fails until the pinouts are verified.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skidl import Net, NetClass  # noqa: E402

from blocks.calc import E6, input_drive_resistor, led_resistor, trace_width_mm  # noqa: E402
from blocks.spec import make, pending, registered, verified_param  # noqa: E402
from blocks.ssr_channel import ssr_channel  # noqa: E402
from blocks.thermal_cutoff import thermal_cutoff  # noqa: E402

from .mcu import mcu  # noqa: E402
from .power import power  # noqa: E402

# ---- Registered passives by value (research/parts.csv). A value not listed here has no
# ---- researched part: research it first rather than adding a row by hand.
RES = {
    "22": "0402WGF220JTCE",
    "220": "0402WGF2200TCE",
    "2k": "0402WGF2001TCE",
    "5.1k": "0402WGF5101TCE",
    "10k": "0402WGF1002TCE",
    "100k": "0402WGF1003TCE",
}
CAP = {
    "100n": "CL05B104KO5NNNC",
    "1u": "CL05A105KA5NQNC",
    "10u": "CL10A106MA8NRNC",
    "22u": "CL21A226MAQNNNE",
}


def res(value: str):
    if value not in RES:
        raise KeyError(f"no researched resistor for {value}: run part research (have {sorted(RES)})")
    return registered(RES[value], value=value)


def cap(value: str):
    return registered(CAP[value], value=value)


LED = "19-217/R6C-AL1M2VY/6T"
SSR = "CPC40055ST"
FET = "AO3400A"
OT_SWITCH = "TMP302ADRLR"  # hardware over-temperature cutoff, 60 C (CLAUDE.md rule 11)

# ---- Computed values (datasheet pages are in the verified pinout files).
V5 = (4.75, 5.25)  # [assumed] +5V window, same as pcb.toml [rails]

# SSR input: >= 10 mA recommended for inductive loads (CPC40055ST p1), <= input abs max.
# The input LED's minimum Vf is not stated, so 0 V is used for the high-current corner; that makes
# the power check pessimistic, hence 60 % of the 1206 resistor's 250 mW (listing, parts.csv).
SSR_R = "1206W4F2200T5E"
SSR_DRIVE = input_drive_resistor(
    V5,
    # drops: SSR LED Vf + the channel MOSFET (one channel, 50 mA bound) + the cutoff MOSFET in the
    # shared return (four channels, 0.25 A bound); both AO3400A at VGS >= 2.5 V
    (
        0.0,
        verified_param(SSR, "led_vf_max_v") + verified_param(FET, "rds_on_max_ohm_vgs_2v5") * (0.05 + 0.25),
    ),
    i_min=verified_param(SSR, "led_if_recommended_a"),
    i_max=verified_param(SSR, "led_if_abs_max_a"),
    series=E6,
    p_rated=0.25,
    p_derate=0.6,
)
assert SSR_DRIVE.value == "220", f"{SSR_R} is 220 ohm; the computed value is {SSR_DRIVE.value}"
# Per-channel fuse (design review H1): loads < 1 A each (human, 2026-10-22); 2 A time-lag, I2t
# 29 A2s (392 series p1) < the SSR's 200 A2s (CPC40055ST p2), so the fuse opens first.
CH_FUSE = "39212000000"
# Channel indicator from +5V at ~1.7 mA (same operating point as devboard; LED Vf min at 5 mA).
IND_LED = led_resistor(5.0, verified_param(LED, "vf_min_v"), 0.0017)
# Status LED straight from a 3.3 V GPIO, ~7.5 mA target.
STATUS_LED = led_resistor(3.3, verified_param(LED, "vf_min_v"), 0.0075)

# Mains copper [assumed loads: 2 A continuous, 5 A peak]: sized for the 5 A peak at a 20 C rise on
# 2 oz (pcb.toml); 2 A continuous needs far less. A 10 C rise at 5 A (2.7 mm) cannot enter the
# 5.08 mm screw-terminal pads at the 1.8 mm mains-to-mains clearance.
MAINS_TRACK_MM = round(trace_width_mm(5.0, 20.0, 2.0) + 0.05, 1)


def build():
    gnd, v5, v3v3, vbus = Net("GND"), Net("+5V"), Net("+3V3"), Net("VBUS")
    ac_l, ac_lf, ac_n = Net("AC_L"), Net("AC_LF"), Net("AC_N")
    # 2.5 mm = basic creepage between mains conductors (rules.kicad_dru); copper on a flat board
    # creeps no shorter than its clearance, so this keeps mains-to-mains creepage too.
    mains = NetClass("Mains", track_width=MAINS_TRACK_MM, clearance=2.5, priority=3)
    power_cls = NetClass("Power", track_width=0.5, clearance=0.2, priority=2)
    for n in (ac_l, ac_lf, ac_n):
        n.netclasses = mains
    for n in (v5, v3v3, vbus):
        n.netclasses = power_cls

    power(ac_l, ac_lf, ac_n, vbus, v5, v3v3, gnd, cap=cap)
    ctrl, hw_ot_sense = mcu(vbus, v3v3, gnd, res=res, cap=cap, status_r=res(STATUS_LED.value), led=registered(LED))

    # Hardware backstop (rule 11): at 60 C the TMP302 opens the SSR drives' common return, so
    # every channel turns off with no firmware involved; firmware only reports it (IO1).
    ssr_rtn = Net("SSR_RTN")
    thermal_cutoff(
        ssr_rtn,
        hw_ot_sense,
        v3v3,
        gnd,
        switch=registered(OT_SWITCH),
        fet=registered(FET),
        r_pullup=res("10k"),  # TMP302 p4: 10-100k from OUT to VS
        r_sense=res("2k"),
        c_bypass=cap("100n"),
    )

    for i, gpio_net in enumerate(ctrl, start=1):
        l_in, l_fused, l_out = Net(f"CH{i}_L_IN"), Net(f"CH{i}_L_FUSED"), Net(f"CH{i}_L_OUT")
        for n in (l_in, l_fused, l_out):
            n.netclasses = mains
        f = make(registered(CH_FUSE), ref=f"F{i + 1}")
        f[1] += l_in
        f[2] += l_fused
        ssr_channel(
            gpio_net,
            l_fused,
            l_out,
            v5,
            gnd,
            ssr=registered(SSR),
            fet=registered(FET),
            led=registered(LED),
            r_in=registered(SSR_R, value=SSR_DRIVE.value),
            r_ind=res(IND_LED.value),
            # 2k, not 100k: IO6 (CH4) leaves reset with a 45 kOhm pull-up (ESP32-C3 datasheet p16-17,
            # p55); 2k keeps the gate at 0.14 V (AO3400A VGS(th) min 0.65 V); 1.65 mA from a GPIO
            # when ON. Same value on every channel (design review 2026-10-29 H1).
            r_pd=res("2k"),
            rtn=ssr_rtn,
        )
        _terminal(f"X{i + 1}", l_in, l_out)

    # Silkscreen safety label (review H1): footprint text only, no copper, not in the BOM.
    make(pending("Graphic:Logo_Open_Hardware_Small", "ssr4:Label_MainsWarning"), ref="LOGO1")
    # Silkscreen doodle (human, 2026-10-29): scouter line art, silkscreen only (lib/ssr4.pretty).
    make(pending("Graphic:Logo_Open_Hardware_Small", "ssr4:Doodle_Scouter"), ref="LOGO2")
    # Terminal labels (CH1-CH4, AC IN L/N, 1 PHASE) and NYLON at the mounting holes near mains
    # copper (design review 2026-10-29 M3, M4): silkscreen only, anchored at the board origin.
    make(pending("Graphic:Logo_Open_Hardware_Small", "ssr4:Label_Terminals"), ref="LOGO3")


def _terminal(ref, pin1, pin2):
    x = make(registered("WJ500V-5.08-2P"), ref=ref)
    x[1] += pin1
    x[2] += pin2


if __name__ == "__main__":
    build()
