"""Power: mains in -> fuse -> MOV -> HLK-PM01 (5 V) -> +5V; USB VBUS -> Schottky -> +5V;
AMS1117-3.3 -> +3V3.

HLK-PM01 application circuit (datasheet p12): F1 1 A / 250 VAC slow fuse and MOV1 10D561K
"must be connected"; C2 100-220 uF on the output. The X capacitor and common-mode choke on
the same page are for EMC certification, which this board does not target (requirements).
HLK pins (p15): 1, 2 AC; 3 -Vout; 4 +Vout. Its two AC pins are both "AC"; the KiCad symbol
names them AC/L and AC/N, so the fused live goes to pin 1.
USB VBUS reaches +5V through D1 so the logic can run from USB alone for flashing with mains
disconnected, and +5V never back-feeds the USB host. With the HLK present the AMS1117 sees
5 V (1.7 V over its 1.3 V max dropout at 0.8 A, p3).
AMS1117-3.3: 22 uF tantalum on the output "ensures stability for all operating conditions"
(p4); 10 uF ceramic on the input.
"""

from skidl import Net, Part, subcircuit

from blocks.spec import make, pending, registered


@subcircuit
def power(ac_l: Net, ac_lf: Net, ac_n: Net, vbus: Net, v5: Net, v3v3: Net, gnd: Net, *, cap) -> None:
    x1 = make(registered("WJ500V-5.08-2P"), ref="X1")  # mains in: 1 = L, 2 = N
    x1[1] += ac_l
    x1[2] += ac_n

    f1 = make(registered("39211000000"), ref="F1")
    f1[1] += ac_l
    f1[2] += ac_lf
    rv1 = make(registered("10D561K"), ref="RV1")  # across the fused line, before the module
    rv1[1] += ac_lf
    rv1[2] += ac_n

    ps1 = make(registered("HLK-PM01"), ref="PS1")
    ps1["AC/L"] += ac_lf
    ps1["AC/N"] += ac_n
    ps1["-Vout"] += gnd
    ps1["+Vout"] += v5
    c_bulk = make(registered("RVT1C221M0605", value="220u"))
    c_bulk[1] += v5  # C_Polarized pin 1 = +
    c_bulk[2] += gnd

    d1 = make(registered("B5819W SL"), ref="D1")
    d1["A"] += vbus
    d1["K"] += v5

    u2 = make(registered("AMS1117-3.3"), ref="U2")
    u2["VI"] += v5
    u2["VO"] += v3v3
    u2["GND"] += gnd
    c_in = make(cap("10u"))
    c_in[1] += v5
    c_in[2] += gnd
    c_out = make(registered("CA45-B016K226T", value="22u"))
    c_out[1] += v3v3  # + to the output
    c_out[2] += gnd

    tp = make(pending("Connector:TestPoint", "ssr4:TestPoint_Pad_D1.5mm"), ref="TP1")
    tp[1] += v5

    # Mains reaches the HLK's power inputs through passive parts (terminal, fuse): tell ERC
    # the nets are driven.
    for n in (ac_lf, ac_n):
        n += Part("power", "PWR_FLAG")[1]
