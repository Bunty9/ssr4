# Contributing to SSR4

Thanks for taking an interest. This board switches **mains voltage**, so contributions are
reviewed for safety first and features second. Please read [docs/safety.md](docs/safety.md)
before you build, test or change anything that touches the 230 VAC side.

## Ways to help

- **Build it and report back.** A build report (issue template "Build report") with photos,
  measurements and what went wrong is the most valuable contribution: it turns an unproven
  design into a proven one.
- **Report a bug** in the hardware, firmware or docs (issue template "Bug report").
- **Propose an improvement** (issue template "Feature request"). Explain the use case first.
- **Safety problems** (creepage, isolation, a protection that can fail unsafe) are reported
  privately, not in a public issue: see [SECURITY.md](SECURITY.md).

## How this repository is made

The board is designed **code-first**: the schematic and PCB in `hardware/kicad/` are generated
from the Python circuit description in `hardware/source/` (SKiDL) by an automated pipeline,
then checked by gates (ERC, DRC, mains clearance rules, netlist tests, two-pass datasheet pinout
verification) before anything is published. The files here are a published snapshot of that
pipeline, so:

- **Hardware changes**: describe them in an issue or edit the circuit source in
  `hardware/source/` in a pull request. A change made only by hand in the KiCad files is
  welcome as a proposal, but the maintainer will port it to the source and regenerate.
- **Every number needs a source.** Component values, ratings and pin assignments must cite a
  datasheet page (or a calculation in `hardware/source/blocks/calc.py`). "Should be fine" is not
  a source.
- **Firmware changes** (`firmware/`): run the tests before opening a pull request:

  ```bash
  pip install -e ".[test]"            # or: uv sync
  esphome compile firmware/sim.yaml   # native Linux build of the firmware
  pytest firmware/tests --lg-env firmware/targets/host.yaml
  ```

  New behaviour needs a test in `firmware/tests/` that fails without your change.

## Pull requests

- One topic per pull request, with a clear description of what and why.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/)
  (`feat(firmware): ...`, `fix(hardware): ...`, `docs: ...`), subject in lower case.
- Keep the safety rules: every hazard keeps a protection that does not depend on firmware; the
  firmware may add protection but never be the only one.
- By contributing you agree that your contribution is licensed under the licence of the part
  you change (see [LICENSES/README.md](LICENSES/README.md)).

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). Be kind, be precise.
