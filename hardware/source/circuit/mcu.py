"""MCU: ESP32-C3-MINI-1-H4X with straps, reset/boot buttons, native USB, NTC and status LED.

Module pins from datasheet Table 3-1 (p11): 3V3 pad 3, EN pad 8, GND pads 1, 2, 11, 14, 36-53.
Strapping (p12-13): SPI boot needs IO2 = 1 and IO9 = 1; download boot IO8 = 1, IO9 = 0; IO2 should
be pulled up. EN must not float (p11). pcbparts mcus/esp32: 10 k + 1 uF on EN, 10 uF + 100 nF at
3V3, 22-33 ohm series on USB D+/D- (C3: IO19 = D+, IO18 = D-), 100 nF on ADC inputs, no strapping
pins or IO18 (high glitch at boot) on outputs that must stay off.
GPIO map (matches boards/ssr4/firmware/ssr4.yaml): CH1-CH4 = IO3, IO4, IO5, IO6; status LED IO10;
NTC IO0 (ADC1); BOOT button IO9; hardware over-temperature sense IO1. IO7 unused; RXD0/TXD0 on test pads.
USB-C (TYPE-C-31-M-12, verified pinout): D+ = A6/B6, D- = A7/B7, CC1 A5, CC2 B5 each 5.1 k to GND
(sink), shield to GND.
"""

from skidl import Net, Part, subcircuit  # SKiDL 3 injects NC (no-connect) as a builtin

from blocks.spec import make, pending, registered

MODULE = "ESP32-C3-MINI-1-H4X"
CHANNEL_GPIOS = ("IO3", "IO4", "IO5", "IO6")


@subcircuit
def mcu(vbus: Net, v3v3: Net, gnd: Net, *, res, cap, status_r, led) -> list[Net]:
    u1 = make(registered(MODULE), ref="U1")
    u1["3V3"] += v3v3
    u1["GND"] += gnd
    u1["NC"] += NC  # noqa: F821
    for c in ("10u", "100n"):
        cc = make(cap(c))
        cc[1] += v3v3
        cc[2] += gnd

    # EN: RC power-on delay plus RESET button.
    en = Net("EN")
    u1["EN"] += en
    _pull(res, en, v3v3)
    c_en = make(cap("1u"))
    c_en[1] += en
    c_en[2] += gnd
    _button("SW2", en, gnd)

    # Straps: IO9 high (SPI boot) with BOOT button to GND; IO8 and IO2 pulled up.
    io9 = Net("BOOT")
    u1["IO9"] += io9
    _pull(res, io9, v3v3)
    _button("SW1", io9, gnd)
    for strap in ("IO8", "IO2"):
        n = Net(f"STRAP_{strap}")
        u1[strap] += n
        _pull(res, n, v3v3)

    # Native USB (flashing, logs).
    j1 = make(registered("TYPE-C-31-M-12"), ref="J1")
    j1["VBUS"] += vbus
    vbus += Part("power", "PWR_FLAG")[1]  # VBUS enters through passive connector pins (ERC)
    j1["GND"] += gnd
    j1["SHIELD"] += gnd
    # ESD protection at the connector (review M6). USBLC6-2SC6 p1: I/O1 = pins 1, 6; I/O2 = 3, 4.
    u3 = make(registered("USBLC6-2SC6"), ref="U3")
    u3["VBUS"] += vbus
    u3["GND"] += gnd
    for pins, esd, gpio, name in (
        (("A6", "B6"), ("1", "6"), "IO19", "USB_DP"),
        (("A7", "B7"), ("3", "4"), "IO18", "USB_DM"),
    ):
        conn, chip = Net(f"{name}_CONN"), Net(name)
        for p in pins:
            j1[p] += conn
        for p in esd:
            u3[p] += conn
        r = make(res("22"))
        r[1] += conn
        r[2] += chip
        u1[gpio] += chip
    for cc in ("CC1", "CC2"):
        r = make(res("5.1k"))
        r[1] += j1[cc]
        r[2] += gnd
    j1["SBU1"] += NC  # noqa: F821
    j1["SBU2"] += NC  # noqa: F821

    # NTC next to the SSRs: 3V3 - 10k - IO0 - NTC - GND, 100 nF at the ADC pin.
    ntc = Net("NTC")
    u1["IO0"] += ntc
    _pull(res, ntc, v3v3)
    th1 = make(registered("SDNT1608X103F3950FTF", value="10k"), ref="TH1")
    th1[1] += ntc
    th1[2] += gnd
    c_ntc = make(cap("100n"))
    c_ntc[1] += ntc
    c_ntc[2] += gnd

    # Status LED from IO10.
    status = Net("STATUS_LED")
    u1["IO10"] += status
    r = make(status_r)
    d = make(led)
    r[1] += status
    r[2] += d["A"]
    d["K"] += gnd

    u1["IO7"] += NC  # noqa: F821
    # IO1 (pad 13, beside the NTC on IO0; not a strapping pin) reads the hardware over-temperature
    # cutoff (blocks.thermal_cutoff), input only. IO7 (pad 21) left the CH3/CH4/IO8 pad cluster
    # unroutable on 2 layers (three Freerouting runs, 2026-10-29).
    hw_ot_sense = Net("HW_OT_SENSE")
    u1["IO1"] += hw_ot_sense

    # Bring-up test pads (review M8): rails, EN, BOOT and UART0 for logs without USB.
    uart_tx, uart_rx = Net("UART_TX"), Net("UART_RX")
    u1["TXD0"] += uart_tx
    u1["RXD0"] += uart_rx
    for n, net in enumerate((v3v3, gnd, en, io9, uart_tx, uart_rx), start=2):
        tp = make(pending("Connector:TestPoint", "ssr4:TestPoint_Pad_D1.5mm"), ref=f"TP{n}")
        tp[1] += net

    outs = []
    for i, gpio in enumerate(CHANNEL_GPIOS, start=1):
        n = Net(f"CH{i}_CTRL")
        u1[gpio] += n
        outs.append(n)
    return outs, hw_ot_sense


def _pull(res, net: Net, rail: Net) -> None:
    r = make(res("10k"))
    r[1] += net
    r[2] += rail


def _button(ref: str, net: Net, gnd: Net) -> None:
    sw = make(registered("TS-1187A-B-A-B"), ref=ref)
    sw[1] += net
    sw[2] += gnd
