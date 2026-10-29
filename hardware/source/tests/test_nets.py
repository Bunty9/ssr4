"""ssr4 netlist tests. Each encodes a datasheet or requirements fact; pages are in the verified
pinout files (datasheets/pinouts/*.verified.json) and spec/requirements.md "ssr4"."""

import json
import re
import tomllib
from pathlib import Path

FIRMWARE = Path(__file__).resolve().parents[1] / "firmware"
LOGIC = FIRMWARE / "packages" / "logic.yaml"
PINOUTS = Path(__file__).resolve().parents[3] / "datasheets" / "pinouts"
CHANNELS = (1, 2, 3, 4)


def _refs_on(net, prefix):
    return sorted({n.ref for n in net.nodes if n.ref.startswith(prefix)})


def _ssr_for(nl, ch):
    net = nl.find_net(f"CH{ch}_L_FUSED")
    ks = _refs_on(net, "K")
    assert len(ks) == 1, f"CH{ch}_L_IN: expected one SSR, got {ks}"
    return ks[0]


def _firmware_channels():
    """switch id chN -> the contract signal its pin comes from, in the shared ESPHome logic."""
    text = LOGIC.read_text(encoding="utf-8")
    return {int(m.group(1)): m.group(2) for m in re.finditer(r"id: ch(\d)\n\s+pin: \$\{(\w+)_pin\}", text)}


def test_each_channel_switches_its_own_terminal_pair(nl):
    """CPC40055ST p1: pins 1, 2 = AC Load. Each channel has its own L_IN/L_OUT terminal (X2-X5)
    and its own fuse between L_IN and the SSR (design review H1)."""
    for ch in CHANNELS:
        k = _ssr_for(nl, ch)
        nl.assert_between(f"F{ch + 1}", f"CH{ch}_L_IN", f"CH{ch}_L_FUSED")
        nl.assert_on_net(k, "1", f"CH{ch}_L_FUSED")
        nl.assert_on_net(k, "2", f"CH{ch}_L_OUT")
        x = f"X{ch + 1}"
        nl.assert_on_net(x, "1", f"CH{ch}_L_IN")
        nl.assert_on_net(x, "2", f"CH{ch}_L_OUT")


def test_ssr_input_driven_low_side_with_pulldown(nl):
    """+5V -> R -> +LED (3); -LED (4) -> MOSFET drain; gate = CHn_CTRL with a pull-down to GND (all
    OFF at power-up); source to SSR_RTN (the hardware cutoff's return). AO3400A: 1 G, 2 S, 3 D."""
    for ch in CHANNELS:
        k = _ssr_for(nl, ch)
        plus = nl.net_of(k, "3")
        rs = _refs_on(plus, "R")
        assert len(rs) == 1
        nl.assert_between(rs[0], plus.name, "+5V")
        drv = nl.net_of(k, "4")
        qs = _refs_on(drv, "Q")
        assert len(qs) == 1, f"{k} -LED: expected one MOSFET, got {qs}"
        q = qs[0]
        nl.assert_on_net(q, "3", drv.name)
        nl.assert_on_net(q, "2", "SSR_RTN")  # returns through the hardware cutoff
        nl.assert_on_net(q, "1", f"CH{ch}_CTRL")
        pulldowns = [
            r for r in _refs_on(nl.find_net(f"CH{ch}_CTRL"), "R") if "GND" in {n.base_name for n in nl.across(r)}
        ]
        assert len(pulldowns) == 1, f"CH{ch}_CTRL needs exactly one pull-down to GND"
        nl.assert_between(pulldowns[0], f"CH{ch}_CTRL", "GND")


def test_indicator_led_in_parallel_branch(nl):
    for ch in CHANNELS:
        drv = nl.net_of(_ssr_for(nl, ch), "4")
        leds = [d for d in _refs_on(drv, "D") if nl.component(d).lib_id == "Device:LED"]
        assert len(leds) == 1
        nl.assert_on_net(leds[0], "K", drv.name)  # LED pad 1 = K
        anode = nl.net_of(leds[0], "A")
        rs = _refs_on(anode, "R")
        assert len(rs) == 1
        nl.assert_between(rs[0], anode.name, "+5V")


def test_firmware_channels_drive_their_own_ssr(nl):
    """Firmware switch chN takes its pin from signal chN, and signal chN is net CHn_CTRL on U1
    (`pcb hw` then resolves the pin; firmware never types a GPIO number)."""
    signals = tomllib.loads((FIRMWARE / "signals.toml").read_text(encoding="utf-8"))["signals"]
    fw = _firmware_channels()
    assert sorted(fw) == list(CHANNELS), f"firmware switches found: {fw}"
    for ch in CHANNELS:
        assert fw[ch] == f"ch{ch}"
        assert signals[f"ch{ch}"]["net"] == f"CH{ch}_CTRL"
        assert "U1" in nl.find_net(f"CH{ch}_CTRL").refs()


def test_esp32_straps_and_enable(nl):
    """ESP32-C3-MINI-1 p12-13: IO9 = 1 for SPI boot (BOOT button pulls low), IO8 = 1 for download
    boot, IO2 pulled up; EN must not float (p11): 10k up + 1 uF (pcbparts mcus/esp32)."""
    for pin in ("IO9", "IO8", "IO2", "EN"):
        net = nl.net_of("U1", pin)
        ups = [r for r in _refs_on(net, "R") if nl.component(r).value == "10k"]
        assert len(ups) == 1, f"U1.{pin}: expected one 10k pull-up, got {ups}"
        nl.assert_between(ups[0], net.name, "+3V3")
    en = nl.net_of("U1", "EN")
    caps = [c for c in _refs_on(en, "C") if nl.component(c).value == "1u"]
    assert len(caps) == 1
    nl.assert_between(caps[0], en.name, "GND")
    for pin, sw in (("IO9", "SW1"), ("EN", "SW2")):
        nl.assert_between(sw, nl.net_of("U1", pin).name, "GND")


def test_esp32_power_pins(nl):
    nl.assert_on_net("U1", "3", "+3V3")
    for pad in ("1", "2", "11", "14", "36", "49", "53"):
        nl.assert_on_net("U1", pad, "GND")


def test_usb_native_data_and_sink_cc(nl):
    """C3 native USB: IO19 = D+, IO18 = D- through 22 ohm; CC1/CC2 each own 5.1k to GND."""
    for pins, gpio in ((("A6", "B6"), "IO19"), (("A7", "B7"), "IO18")):
        conn = nl.net_of("J1", pins[0])
        assert nl.net_of("J1", pins[1]).name == conn.name
        rs = [r for r in _refs_on(conn, "R") if nl.component(r).value == "22"]
        assert len(rs) == 1
        nl.assert_between(rs[0], conn.name, nl.net_of("U1", gpio).name)
    cc1, cc2 = nl.net_of("J1", "A5"), nl.net_of("J1", "B5")
    assert cc1.name != cc2.name
    for net in (cc1, cc2):
        rs = _refs_on(net, "R")
        assert len(rs) == 1 and nl.component(rs[0]).value == "5.1k"
        nl.assert_between(rs[0], net.name, "GND")


def test_power_path(nl):
    """HLK-PM01 p12: fuse then MOV ahead of the module; D1 from VBUS to +5V; AMS1117 5V -> 3V3."""
    nl.assert_between("F1", "AC_L", "AC_LF")
    nl.assert_between("RV1", "AC_LF", "AC_N")
    nl.assert_on_net("PS1", "1", "AC_LF")
    nl.assert_on_net("PS1", "2", "AC_N")
    nl.assert_on_net("PS1", "3", "GND")
    nl.assert_on_net("PS1", "4", "+5V")
    nl.assert_on_net("D1", "A", "VBUS")
    nl.assert_on_net("D1", "K", "+5V")
    nl.assert_on_net("U2", "VI", "+5V")
    nl.assert_on_net("U2", "VO", "+3V3")
    nl.assert_on_net("X1", "1", "AC_L")
    nl.assert_on_net("X1", "2", "AC_N")


def test_only_isolating_parts_touch_mains(nl):
    """Requirements, electrical safety: only terminals, fuse, MOV, the AC-DC module's AC pins and
    the SSRs' AC pins may connect to a 230 V net. Anything else there is an isolation bug."""
    allowed = {("PS1", "1"), ("PS1", "2")}
    mains = [n for n in nl.nets if n.cls == "Mains"]
    assert len(mains) == 15, [n.name for n in mains]
    for net in mains:
        for node in net.nodes:
            if node.ref[0] in "XFK" or node.ref.startswith("RV") or node.ref.startswith("#"):
                if node.ref.startswith("K"):
                    assert node.pin in ("1", "2"), f"{node.ref}.{node.pin} (SSR input side) on mains net {net.name}"
                continue
            assert (node.ref, node.pin) in allowed, f"{node.ref}.{node.pin} must not be on mains net {net.name}"


def test_usb_esd_and_test_pads(nl):
    """USBLC6-2SC6 at the connector (p1: I/O1 = 1, 6; I/O2 = 3, 4; VBUS 5; GND 2); test pads on
    the rails, EN, BOOT and UART0 (review M6, M8)."""
    nl.assert_on_net("U3", "1", nl.net_of("J1", "A6").name)
    nl.assert_on_net("U3", "6", nl.net_of("J1", "A6").name)
    nl.assert_on_net("U3", "3", nl.net_of("J1", "A7").name)
    nl.assert_on_net("U3", "4", nl.net_of("J1", "A7").name)
    nl.assert_on_net("U3", "5", "VBUS")
    nl.assert_on_net("U3", "2", "GND")
    probed = {nl.net_of(tp, "1").base_name for tp in nl.refs("TP")}
    assert {"+5V", "+3V3", "GND", "EN", "BOOT", "UART_TX", "UART_RX"} <= probed, probed


def test_ntc_divider_on_adc1(nl):
    """NTC on IO0 (ADC1) with 10k to 3V3 and 100 nF filter (pcbparts mcus/esp32: use ADC1)."""
    ntc = nl.net_of("U1", "IO0")
    nl.assert_on_net("TH1", "1", ntc.name)
    nl.assert_on_net("TH1", "2", "GND")
    assert any(nl.component(r).value == "10k" for r in _refs_on(ntc, "R"))
    assert any(nl.component(c).value == "100n" for c in _refs_on(ntc, "C"))


def test_hardware_overtemperature_cutoff_is_in_every_ssr_drive_path(nl):
    """CLAUDE.md rule 11: over-temperature turns every SSR off with no firmware in the path.
    TMP302ADRLR (verified pinout): 1 TRIPSET0, 2 GND, 3 OUT (open drain, low when hot), 4 HYSTSET,
    5 VS, 6 TRIPSET1. TRIPSET1 = VS, TRIPSET0 = GND -> 60 C (Table 1 p7); HYSTSET = VS -> 10 C
    hysteresis (p5); pull-up 10-100k OUT to VS (p4)."""
    sw = [r for r in nl.refs("U") if nl.component(r).get("MPN") == "TMP302ADRLR"]
    assert len(sw) == 1, f"expected one TMP302ADRLR, got {sw}"
    u = sw[0]
    # HYSTSET = VS -> 10 C hysteresis (p5): releases near 50 C, so a hung MCU cannot make the
    # loads cycle tightly around the trip point (design review 2026-10-29 L1)
    for pin, net in (("5", "+3V3"), ("6", "+3V3"), ("1", "GND"), ("4", "+3V3"), ("2", "GND")):
        nl.assert_on_net(u, pin, net)
    ot = nl.net_of(u, "3")
    pullups = [r for r in _refs_on(ot, "R") if {n.base_name for n in nl.across(r)} == {ot.base_name, "+3V3"}]
    assert len(pullups) == 1 and 10_000 <= _ohms(nl.component(pullups[0]).value) <= 100_000
    # the cutoff MOSFET: gate on OUT, drain = the SSR drives' common return, source = GND
    qs = [q for q in _refs_on(ot, "Q") if nl.net_of(q, "1").name == ot.name]
    assert len(qs) == 1, f"expected one cutoff MOSFET on {ot.name}, got {qs}"
    nl.assert_on_net(qs[0], "3", "SSR_RTN")
    nl.assert_on_net(qs[0], "2", "GND")
    # every channel MOSFET returns through it, and nothing else sinks SSR_RTN to GND
    rtn = nl.find_net("SSR_RTN")
    channel_fets = {nl.net_of(_ssr_for(nl, ch), "4").name for ch in CHANNELS}
    for q in _refs_on(rtn, "Q"):
        if q != qs[0]:
            assert nl.net_of(q, "3").name in channel_fets
    assert len(_refs_on(rtn, "Q")) == len(CHANNELS) + 1
    assert {r for r in rtn.refs()} <= set(_refs_on(rtn, "Q")), f"unexpected parts on SSR_RTN: {rtn.refs()}"
    # firmware only observes it: IO1 through a series resistor, the gate on the switch side
    sense = nl.find_net("HW_OT_SENSE")
    nl.assert_on_net("U1", "IO1", sense.name)
    series = [r for r in _refs_on(sense, "R") if ot.name in {n.name for n in nl.across(r)}]
    assert len(series) == 1


def _ohms(value: str) -> float:
    m = re.fullmatch(r"([\d.]+)([kM]?)", value)
    return float(m.group(1)) * {"": 1, "k": 1e3, "M": 1e6}[m.group(2)]


# ESP32-C3 pins that come out of reset with the internal weak pull-up on (ESP32-C3 datasheet v2.4
# Table 2-1 p16-17: MTCK = GPIO6 has IE & WPU while EFUSE_DIS_PAD_JTAG = 0, the default; GPIO3,
# MTMS = GPIO4, MTDI = GPIO5 only IE). RPU = 45 kOhm typical (p55, no minimum given). The module
# names GPIO6 "IO6" (ESP32-C3-MINI-1 datasheet p11).
RESET_PULL_UP_OHM = {"IO6": 45_000}


def test_channels_stay_off_through_reset_despite_chip_pull_ups(nl):
    """Until firmware configures them, a pin with a reset pull-up and the gate pull-down form a
    divider. The gate must stay below half the AO3400A's minimum threshold (VGS(th) min, p2), so
    a weaker real pull-up (no minimum is specified) still leaves margin (design review 2026-10-29
    H1: 100k let IO6 reach 2.3 V and switch CH4 on at every reset)."""
    vth_min = json.loads((PINOUTS / "AO3400A.verified.json").read_text())["params"]["vgs_th_min_v"]["value"]
    for ch in CHANNELS:
        net = nl.find_net(f"CH{ch}_CTRL")
        pin = next(n.function for n in net.nodes if n.ref == "U1")
        r_pd = next(
            _ohms(nl.component(r).value) for r in _refs_on(net, "R") if "GND" in {n.base_name for n in nl.across(r)}
        )
        r_pu = RESET_PULL_UP_OHM.get(pin)
        v_gate = 3.3 * r_pd / (r_pu + r_pd) if r_pu else 0.0
        assert v_gate < vth_min / 2, f"CH{ch} ({pin}): gate {v_gate:.2f} V at reset, AO3400A VGS(th) min {vth_min} V"
