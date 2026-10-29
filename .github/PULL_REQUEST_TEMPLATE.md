## What and why

<!-- What does this change, and which problem does it solve? Link the issue. -->

## Area

- [ ] Hardware (circuit source / KiCad)
- [ ] Firmware
- [ ] Documentation
- [ ] Fabrication files / BOM

## Checks

- [ ] Every new number (value, rating, pin) cites a datasheet page or a calculation.
- [ ] Firmware: `pytest firmware/tests --lg-env firmware/targets/host.yaml` passes, and new behaviour has a test.
- [ ] Safety: every hazard still has a protection that does not depend on firmware.
- [ ] Docs updated where behaviour, wiring or ordering changed.
