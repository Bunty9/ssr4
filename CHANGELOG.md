# Changelog

All notable changes to SSR4 are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] - rev A prototype, not yet built

### Added

- **Board**: four zero-cross triac SSR outputs (CPC40055ST), each with its own screw terminals
  and a 2 A time-lag fuse; on-board isolated 230 VAC → 5 V supply (HLK-PM01) with input fuse and
  MOV; ESP32-C3-MINI-1 with native USB-C for flashing (ESD-protected); NTC next to the SSRs;
  channel and status LEDs; BOOT/RESET buttons; seven test pads.
- **Hardware over-temperature cutoff**: a TMP302 temperature switch opens the SSR drives'
  common return at 60 °C, so every output turns off with no firmware involved.
- **Mains isolation rules** in KiCad DRC: 6.5 mm mains-to-low-voltage clearance and creepage,
  1.8 / 2.5 mm between mains conductors.
- **ESPHome firmware**: encrypted Home Assistant API, OTA with password, captive-portal setup,
  all outputs OFF at power-up, over-temperature latch (55 °C / 45 °C), NTC fault detection in
  volts, reporting of the hardware cutoff.
- **Firmware tests on a PC simulation** of the board (ESPHome `host` build driven over its API),
  and netlist tests that prove the circuit's safety properties.
- **Fabrication packages** for JLCPCB (assembly incl. through-hole) and PCBWay (turnkey).
- **Silkscreen scouter doodle**, terminal labels (AC IN L/N, CH1-CH4, 1 PHASE) and NYLON marks at
  the mounting holes next to mains copper.

### Fixed before publishing (independent design review, 2026-10-29)

- **CH4 switched on at every reset**: the ESP32-C3's GPIO6 leaves reset with a 45 kΩ pull-up,
  which beat the 100 kΩ gate pull-down. All channels now use 2 kΩ pull-downs; a netlist test
  checks every channel against the chip's reset pulls.
- The hardware cutoff's hysteresis is 10 °C, and the firmware latches a hardware trip until the
  board cools to 45 °C, so loads do not cycle at the cutoff.
- No automatic reboot when Home Assistant or Wi-Fi is unreachable (each reboot switched all loads
  off); 50 ms debounce on the cutoff input.
