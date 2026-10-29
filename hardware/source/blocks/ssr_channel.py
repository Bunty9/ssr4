"""One 230 VAC output: a zero-cross SSR switched by a logic-level N-MOSFET, with an indicator.

    +5V --R_in-- SSR +LED (3)   SSR -LED (4) --+
    +5V --R_ind-- LED A   LED K ---------------+-- DRV -- Q drain;  Q source -- RTN (GND if none)
    CTRL (GPIO) -- Q gate, R_pd to GND (strong enough to beat the MCU pin's reset pull-up)
    SSR AC Load (1) -- L_IN      SSR AC Load (2) -- L_OUT      (mains, net class "Mains")

Why two parallel branches through one MOSFET: in series, one resistor would have to give the
SSR input >= 10 mA at the worst corner while keeping the indicator under its 25 mA rating at
the other, and the tolerance window is too wide (blocks.calc.input_drive_resistor raises).
Why the gate pull-down: MCU pins float, or are weakly pulled up, until firmware runs; the
pull-down keeps every output OFF at power-up and reset (requirement "all outputs OFF at
power-up"). Size it against the pin's reset pull-up, not only for leakage: on the ESP32-C3,
GPIO6 (MTCK) comes out of reset with a 45 kOhm pull-up, which a 100k pull-down cannot hold.
RTN: pass the return of a hardware cutoff (blocks.thermal_cutoff) to make a group of channels
switch off without firmware; the gate pull-down still goes to GND.
CPC40055ST pin numbers from its datasheet pin configuration (p1): 1, 2 AC Load; 3 +LED; 4 -LED.
The two AC pins share a name, so they are connected by number.
"""

from skidl import Net, subcircuit

from .spec import PartSpec, make


@subcircuit
def ssr_channel(
    ctrl: Net,
    l_in: Net,
    l_out: Net,
    v5: Net,
    gnd: Net,
    *,
    ssr: PartSpec,
    fet: PartSpec,
    led: PartSpec,
    r_in: PartSpec,
    r_ind: PartSpec,
    r_pd: PartSpec,
    rtn: Net | None = None,
) -> None:
    k = make(ssr)
    q = make(fet)
    d = make(led)
    rin, rind, rpd = make(r_in), make(r_ind), make(r_pd)
    drv = Net("DRV")

    k[1] += l_in
    k[2] += l_out
    v5 += rin[1]
    rin[2] += k[3]  # +LED
    k[4] += drv  # -LED
    v5 += rind[1]
    rind[2] += d["A"]
    d["K"] += drv
    q["D"] += drv
    q["S"] += rtn if rtn is not None else gnd
    q["G"] += ctrl
    rpd[1] += ctrl
    rpd[2] += gnd
