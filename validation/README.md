# Validation of this snapshot

Published from source commit `0ba30d9` on 2026-10-29. Everything below was produced by the
design's gates and tests on that commit; the raw outputs are in [`reports/`](reports/).

**Status: rev A is a gated, unbuilt design.** No physical board has been tested yet. The checks
below prove that the published files are internally consistent, match their datasheets and the
safety rules, and that the firmware behaves as specified on a simulation of the board. They do
not replace bench tests (see [What is not verified](#what-is-not-verified)).

## Summary

| Check | Tool | Result |
|---|---|---|
| Parts | registry of 27 part types, each from a distributor lookup with date | 0 errors; every IC, transistor, diode and connector approved by a human |
| Datasheet pinouts | two independent extractions per part, compared by a consensus tool | 11 parts verified ([`../hardware/pinouts/`](../hardware/pinouts/)) |
| Pins vs datasheet | every netlist pin against the verified pinout | 0 errors |
| Netlist tests | pytest on the netlist exported from the generated schematic | 16 passed ([`reports/netlist-tests.xml`](reports/netlist-tests.xml)) |
| ERC | KiCad 10.0.7 | 0 errors, 80 warnings (all `lib_symbol_mismatch`, see below) |
| DRC with mains rules | KiCad 10.0.7 + [`circuit.kicad_dru`](../hardware/kicad/ssr4/circuit.kicad_dru) | 0 errors, 0 unconnected; silkscreen warnings only |
| Fab rules | JLCPCB 2-layer capabilities | pass |
| 3D models | every footprint's model resolves | pass |
| Fabrication package | Gerbers, drill, BOM, CPL built and pre-flighted | "GATE RELEASE: PASS" |
| Firmware | both builds compile; 14 behaviour tests on the PC simulation | 14 passed ([`reports/firmware-tests.xml`](reports/firmware-tests.xml)) |
| NTC divider | closed-form maths vs ngspice 45.2 | agree within ngspice's tolerance ([`spice/`](spice/)) |
| Independent design review | a separate reviewer of the final layout | findings and their status below |

The gate reports themselves: [`gate-schematic.json`](reports/gate-schematic.json),
[`gate-board.json`](reports/gate-board.json), [`gate-release.json`](reports/gate-release.json),
[`gate-firmware.json`](reports/gate-firmware.json); KiCad's own [`erc.json`](reports/erc.json)
and [`drc.json`](reports/drc.json).

## Circuit validity

### Netlist tests

Each test reads the netlist KiCad exports from the generated schematic (what will actually be
built) and encodes a datasheet or requirement fact, with the page in its docstring
([`../hardware/source/tests/test_nets.py`](../hardware/source/tests/test_nets.py)):

| Test | Proves |
|---|---|
| `test_each_channel_switches_its_own_terminal_pair` | each channel: terminal L_IN → its own fuse → SSR AC pins → its own L_OUT |
| `test_ssr_input_driven_low_side_with_pulldown` | +5V → resistor → SSR LED → MOSFET → cutoff return; a pull-down on every gate |
| `test_channels_stay_off_through_reset_despite_chip_pull_ups` | with the ESP32-C3's reset pull-ups (GPIO6: 45 kΩ), every gate stays below half the MOSFET's minimum threshold |
| `test_indicator_led_in_parallel_branch` | channel LEDs show the commanded state without stealing SSR current |
| `test_firmware_channels_drive_their_own_ssr` | firmware switch *n* uses the pin of signal ch*n*, which is net CH*n*_CTRL |
| `test_esp32_straps_and_enable` | IO9 pulled up with the BOOT button to GND, IO8 and IO2 pulled up (SPI boot); EN with 10 kΩ pull-up and 1 µF (module datasheet p11-13) |
| `test_esp32_power_pins` | the module's 3V3 pad on +3V3 and its ground pads on GND |
| `test_usb_native_data_and_sink_cc` | D+/D- to the C3's USB pins through 22 Ω; 5.1 kΩ CC pull-downs |
| `test_power_path` | mains → fuse → MOV → AC-DC module (HLK-PM01 p12); USB VBUS through D1 into +5V; AMS1117 from +5V to +3V3 |
| `test_only_isolating_parts_touch_mains` | only terminals, fuses, the MOV, the AC-DC module's AC pins and the SSRs' AC pins connect to a 230 V net: anything else would be an isolation bug |
| `test_usb_esd_and_test_pads` | ESD protection on USB; test pads on rails, EN, BOOT, UART |
| `test_ntc_divider_on_adc1` | NTC on IO0 (ADC1) with 10 kΩ to 3V3 and a 100 nF filter |
| (generic) `test_no_power_pin_left_floating`, `test_no_orphan_named_nets`, `test_has_ground` | basic netlist hygiene |
| `test_hardware_overtemperature_cutoff_is_in_every_ssr_drive_path` | TMP302 straps (60 °C, 10 °C hysteresis), pull-up to 3V3, the cutoff MOSFET in the return of all four channels and nothing else on that return, firmware sense through a series resistor |

### Datasheet pinouts

Every part with pins that matter (ICs, transistors, diodes, LEDs, connectors) has a
`*.verified.json` written only when two independent extractions from the datasheet agree on
every pin, rating and parameter. Disagreements go to a human with both values and page numbers;
for the TMP302 the human decided one (the datasheet prints no minimum for the supply's absolute
maximum rating, p4).

### ERC and DRC warnings

- **ERC, 80 × `lib_symbol_mismatch`**: the generator embeds its own copy of each symbol in the
  schematic, which differs cosmetically from KiCad's library copy. No electrical meaning.
- **DRC, silkscreen only**: 11 overlapping texts, 8 near the board edge, 2 over copper
  (cosmetic; the fab clips silkscreen from pads).

## Layout and mains safety

| Rule (`circuit.kicad_dru`) | Value | Result |
|---|---|---|
| Mains to low-voltage clearance | ≥ 6.5 mm | 0 violations |
| Mains to low-voltage creepage | ≥ 6.5 mm | 0 violations |
| Mains to mains clearance (different nets) | ≥ 1.8 mm | 0 violations |
| Mains to mains creepage | ≥ 2.5 mm | 0 violations |

Low-voltage signals use 0.2 mm clearance; the board's rules accept 0.195 mm between two
low-voltage signals because the pre-router plans tracks exactly at 0.2 mm and float rounding left
two of them 2-3 µm short (still far above JLCPCB's 0.16 mm minimum). The ESP32's signal nets are
pre-routed by that router so the autorouter cannot leave them open. Mains tracks are 1.4 mm wide
on 2 oz copper. Board-wide clearance is 0.2 mm (the TMP302 uses
TI's recommended 0.3 mm pads, datasheet p18, so the board does not need finer rules).

## Firmware

14 behaviour tests run the real ESPHome configuration as a Linux program and drive it over the
encrypted native API, like Home Assistant does ([`../firmware/tests/`](../firmware/tests/)):

| Test | Checks |
|---|---|
| `test_all_channels_off_after_power_up` | every channel reports OFF after power-up |
| `test_power_up_drives_every_channel_pin_low` | the boot log shows every channel pin (taken from the netlist) driven LOW |
| `test_each_channel_drives_its_contract_pin` (× 4) | switching channel *n* drives exactly its netlist pin HIGH, then LOW |
| `test_over_temperature_latches_until_resume` | 56 °C: all off; ON refused at 56 °C and 50 °C; allowed again below 45 °C |
| `test_ntc_fault_turns_everything_off_and_refuses_on` (× 4) | open NTC on a saturated ADC (2.95 V), above the ADC's specified range (2.6 V), shorted NTC, node at ground: all off, ON refused, recovery when valid |
| `test_hardware_cutoff_is_reported_and_latched_until_cool` | hardware trip reported, channels follow it, ON refused while tripped and after release until 45 °C |

Plus 2 static checks of the firmware sources (fault limits derived from the NTC divider and the
ADC range; no hard-coded GPIO numbers).

**Tests that caught real bugs.** The NTC-fault tests were written against the first firmware,
whose "below -20 °C" check needed 3.0 V on the ADC pin, above the ESP32-C3's specified 2.5 V
range: an open NTC could read as -19 °C and pass. With that old limit the open-NTC and
above-range cases fail; with the fix they pass. The hardware-latch test and the reset netlist
test likewise failed before their fixes.

## Calculations

| Quantity | Value | Basis |
|---|---|---|
| SSR input LED current | 15.9-18.6 mA at 5 V (14.8-19.8 mA over ±5 %) | 220 Ω; LED Vf 0.9-1.5 V; SSR turn-on 5 mA, recommended 10 mA (CPC40055ST p2) |
| SSR input resistor power | ≤ 86 mW of 250 mW | 1206 resistor |
| Driver MOSFET drop | about 1 mV | AO3400A RDS(on) < 48 mΩ at VGS 2.5 V (p2) |
| Gate at reset, CH4 | 0.14 V (limit: 0.325 V = half of VGS(th) min) | 45 kΩ reset pull-up vs 2 kΩ pull-down |
| Channel fuse vs SSR | fuse I²t 29 A²s < SSR 200 A²s | Littelfuse 392 p1, CPC40055ST p2 |
| ADC range at 12 dB | 0-2500 mV, ±35 mV | ESP32-C3 datasheet v2.4 Table 5-6 p56 |
| Firmware trip accuracy | ±1.3 °C at 45 °C, ±1.6 °C at 55 °C from the ADC alone | NTC slope at the trip points ([`ntc-table.md`](ntc-table.md)) |
| Hardware trip accuracy | ±2 °C | TMP302 p5 |
| Lowest usable board temperature | about 1.4 °C (2.5 V at the ADC) | below it the NTC reading is treated as a fault (fail-safe) |

[`ntc-table.md`](ntc-table.md) has the full NTC voltage table, generated from the same functions
the firmware tests use.

## SPICE cross-check

[`spice/ntc_divider.cir`](spice/ntc_divider.cir) models the NTC divider in ngspice 45.2 with a
behavioural NTC, sweeping the board temperature from -20 °C to 110 °C
([`spice/ntc_divider.out`](spice/ntc_divider.out)). Against the closed-form functions it agrees
to under 10 µV at 26 of 27 points and by 0.9 mV at 20 °C, within ngspice's default relative
tolerance (0.1 %). The node's time constant (at most 0.5 ms) is negligible against the 5 s
sample interval.

## Independent design review (2026-10-29)

A separate reviewer examined the final layout, the netlist, the firmware and the datasheets.

| ID | Finding | Status |
|---|---|---|
| H1 | **CH4 switched on at every reset**: GPIO6 leaves reset with a 45 kΩ pull-up, which lifted the 100 kΩ gate pull-down to 2.3 V | **fixed**: 2 kΩ pull-downs on all channels, netlist test added |
| M1 | the firmware's NTC sits beside the ESP32 module, not the SSRs | open (rev B): moving it between the SSRs made the autorouter run its trace 5.2 mm from mains pads; the hardware cutoff (between the SSRs) is the protection |
| M2 | no way to test the hardware cutoff on the board | open: hot-air test in [bring-up](../docs/bring-up.md); test pads planned for rev B |
| M3 | metal screws in the top mounting holes would bridge the mains gap | **fixed**: "NYLON" printed at those holes, documented |
| M4 | terminals not labelled | **fixed**: AC IN / L / N, CH1-CH4, "1 PHASE" on the silkscreen |
| M5 | ESPHome's default 15-minute reboot when Home Assistant is down would switch all loads off | **fixed**: `reboot_timeout: 0s` |
| M6 | the silkscreen doodle derives from third-party fan art | accepted by the maintainer; credited in [LICENSES](../LICENSES/README.md) |
| L1 | the cutoff could cycle loads at its 5 °C hysteresis | **fixed**: 10 °C hysteresis, firmware latches a trip until 45 °C |
| L3 | ground pour close to the antenna's sides | open (rev B) |
| L4 | channel LEDs not in channel order | open (rev B) |
| L5 | some reference texts overlap | open (cosmetic) |
| L6 | the assembler must place U7 with the right rotation | check in the placement preview ([fabrication](../docs/fabrication.md)) |
| L7 | no debounce on the cutoff input | **fixed**: 50 ms |
| L8 | the example secrets compile unchanged | open: replace them before flashing ([firmware](../docs/firmware.md)) |

## What is not verified

- Anything physical: thermal behaviour in the enclosure, the cutoff's real trip point on the
  board, EMC, surge, isolation (hi-pot), Wi-Fi range, mechanical fit.
- Spacing over component bodies, wiring and the enclosure (DRC sees copper only).
- Safety certification of the HLK-PM01 (no verifiable certificate) and of the board as a whole
  (none).

If you build one, a [build report](https://github.com/Bunty9/ssr4/issues/new/choose) with
measurements is the most useful thing you can contribute.

## Reproduce

```bash
pip install -e ".[test]" "esphome==2026.10.0"
esphome compile firmware/sim.yaml
pytest firmware/tests --lg-env firmware/targets/host.yaml   # firmware behaviour
ngspice -b validation/spice/ntc_divider.cir                 # SPICE cross-check
kicad-cli pcb drc --schematic-parity --severity-error hardware/kicad/ssr4/circuit.kicad_pcb
```
