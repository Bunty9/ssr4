# Safety

> **SSR4 switches 230 VAC mains. Mains voltage can kill, and a faulty installation can start a
> fire.** Build, test and install it only if you are competent to work on mains wiring, and have
> the final installation checked by a qualified electrician where your local rules require it.
> This is an **uncertified prototype design**, provided "as is" without warranty under its
> licences.

## The hazards and what the design does about them

| Hazard | Design measure | Where it is checked |
|---|---|---|
| Touching mains through the low-voltage side (USB, buttons, ESP32) | Isolated AC-DC module (HLK-PM01); opto-isolated SSRs (2500 Vrms); **6.5 mm** clearance and creepage between every mains copper feature and every low-voltage one | KiCad DRC custom rules (`hardware/kicad/ssr4/circuit.kicad_dru`): 0 violations; netlist test `test_only_isolating_parts_touch_mains` |
| Short circuit or overload on an output | **2 A time-lag fuse per channel** (I²t 29 A²s, below the SSR's 200 A²s, so the fuse opens first); the household MCB still clears a dead short | netlist test `test_each_channel_switches_its_own_terminal_pair` |
| Fault in the AC-DC module | 1 A time-lag input fuse and a 10D561K varistor, as the module datasheet requires (p12) | netlist test `test_power_path` |
| Overheating (SSRs, AC-DC module) in a closed case | **Hardware cutoff at 60 °C** that turns every SSR off without firmware, plus a firmware cutoff at 55 °C and NTC fault detection | netlist test `test_hardware_overtemperature_cutoff_is_in_every_ssr_drive_path`; firmware tests on the PC simulation |
| Outputs switching on unexpectedly (boot, reset, power loss) | 2 kΩ pull-down on every SSR driver gate, sized against the ESP32-C3's own reset pull-ups; firmware turns everything off at boot and restores nothing; no automatic reboots when Home Assistant or Wi-Fi is down | netlist tests `test_channels_stay_off_through_reset_despite_chip_pull_ups`, `test_ssr_input_driven_low_side_with_pulldown`; firmware test `test_all_channels_off_after_power_up` |
| Metal mounting screws bridging the mains gap | The two top mounting holes are about 8-10 mm from mains terminals: a metal screw head on the low-voltage ground pour would be closer than 6.5 mm to mains copper. Use **nylon screws there** (printed "NYLON" on the board) | design review 2026-10-29 (M3) |
| Miswiring the supply and the channels | Terminals labelled on the silkscreen: "AC IN" with L / N at X1, CH1-CH4 next to each channel's fuse (the fuse is on the L_IN side) | - |
| "Off" is not isolation | An SSR leaks up to 100 µA when off, so **an output is live even when OFF**; this is printed on the silkscreen | - |

## What is NOT verified

Be clear about the limits of a design that has passed its checks but has not yet been built and
tested:

- **No board has been built yet** (rev A). Thermal behaviour, EMC, real Wi-Fi range and the
  cutoff's trip point on the real board are unmeasured.
- **Spacing is checked on copper only.** KiCad's rules do not see component bodies, the
  enclosure, wiring, or conformal coating. The installation must keep mains and low-voltage
  parts apart too.
- **The HLK-PM01 has no verifiable safety certificate**, and its datasheet gives two different
  isolation figures (3000 Vac on p3, 2500 Vac on p13). The "reinforced" isolation of the board
  rests on that module and on the SSR ratings.
- **Not certified** to IEC 60335-1 (household appliances), IEC 60730-1 (automatic controls),
  CISPR 14 (EMC) or any national scheme. The firmware protections are convenience functions
  (IEC 60730 "Class A"); the safety rests on the hardware fuses, isolation and thermal cutoff.
- **All four channels must be on the same phase.** Two channels on different phases would put
  400 V between them, which needs more than the 2.5 mm basic creepage used here.

## Rules for building and testing

1. **Never work on the board with mains connected.** Flash and test the logic side from USB-C
   with mains disconnected; the board is designed for that.
2. **Test the outputs with a safe low voltage first**: a 24 VAC transformer and a lamp
   ([bring-up.md](bring-up.md), stage 3).
3. **First mains power-up behind an isolation transformer or a current-limited supply**, with an
   RCD on the supply. Note that an isolation transformer disables the RCD's protection for
   contact on its secondary side, so keep your hands off the board.
4. **Do not connect USB to a computer while mains is applied** unless through a USB isolator.
5. **Discharge and disconnect** before touching: the varistor and the AC-DC module's input
   capacitors can stay charged briefly.
6. Use isolated or differential probes for any measurement on the mains side.

## Installation rules

See [installation.md](installation.md). In short: a closed, insulating enclosure; mains wiring
by the rules of your country; loads below 1 A continuous per channel; an RCD upstream; one
phase.

## Legal

You may build and use open hardware for yourself. Selling boards or devices built from this
design is a different matter: household electrical products need conformity assessment
(for example CE marking in the EU, and in India the BIS Quality Control Order for household
appliances under IS 302-1, in force from 1 October 2026 according to a secondary source). This is not legal
advice. Check the rules where you live.
