# Development

## Repository layout

```
hardware/
  kicad/ssr4/          KiCad 10 project (open circuit.kicad_pro), generated from the source below
  lib/                 local footprints, symbols and 3D models (exact LCSC parts, TI land pattern)
  source/              the circuit as Python (SKiDL): circuit/, blocks/, calc.py, netlist tests,
                       placement/routing config (boardforge.toml), mains DRC rules
  fabrication/         JLCPCB and PCBWay packages (Gerbers, BOM, CPL, order notes)
  pinouts/             datasheet pin data for every IC/transistor/diode, verified by two
                       independent extractions (with page numbers)
  bom-sourced.csv      BOM with LCSC stock and prices at publication
  ssr4-schematic.pdf, ssr4-pcb-layers.pdf
firmware/              ESPHome configuration, generated pins, tests, labgrid targets
fwtest/                test harness: labgrid drivers + an ESPHome API client
validation/            test results and calculations of the published snapshot
docs/                  guides and renders
```

## How the design is made

SSR4 is designed **code-first**. The circuit is written in Python (`hardware/source/circuit/`,
`hardware/source/blocks/`), every computed value comes from a tested function
(`blocks/calc.py`) fed by datasheet numbers, and an automated pipeline turns it into the KiCad
schematic and PCB. Each stage is checked by a gate before anything is published:

| Gate | Checks |
|---|---|
| schematic | every part has a researched part number; every pin of every IC, transistor and diode matches a datasheet pinout extracted twice independently; netlist tests (polarity, safety paths); ERC |
| board | DRC including the mains clearance and creepage rules, fab-capability rules, 3D models present |
| release | Gerbers, BOM and placement files built and pre-flighted |
| firmware | pins generated from the netlist, both firmware builds compile, behaviour tests pass on the PC simulation |

The generator pipeline itself is not published yet; `hardware/source/` is included so the
design can be reviewed and reused, and the KiCad project is the editable result.

## Changing the hardware

- Open `hardware/kicad/ssr4/circuit.kicad_pro` in KiCad 10. The project's library tables point
  at `hardware/lib/` and KiCad's stock libraries, so it opens on any machine.
- Run DRC in KiCad: the mains rules are in `circuit.kicad_dru` next to the board.
- Describe hardware changes in an issue or pull request (see [CONTRIBUTING.md](../CONTRIBUTING.md));
  the maintainer ports them into the source and regenerates, so the gates check them again.

## Firmware

```bash
pip install -e ".[test]"              # pytest, labgrid, aioesphomeapi
pip install "esphome==2026.10.0"
esphome compile firmware/sim.yaml     # Linux build of the firmware
pytest firmware/tests --lg-env firmware/targets/host.yaml
```

- `firmware/targets/host.yaml` is a [labgrid](https://labgrid.readthedocs.io) environment: the PC
  build is driven like a board on a power switch (power on starts the program, power off stops
  it), so the same tests can run against a real board with a real power switch and a different
  environment file.
- Tests declare what they need (`lg_feature("sim-ntc")` etc.); a target that cannot provide it
  skips the test instead of faking it.
- `tests/test_config.py` checks the firmware sources without building: fault limits derived from
  the NTC divider and the ADC range, and no typed GPIO numbers.

## Continuous integration

`.github/workflows/ci.yml` runs on every push and pull request:

- **firmware**: validates the real-board configuration, builds the PC simulation and runs the
  behaviour tests;
- **hardware**: KiCad 10.0.7's ERC and DRC (with the mains rules and schematic parity) in the
  official `kicad/kicad` container; errors fail the build.
