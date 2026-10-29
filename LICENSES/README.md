# Licences

SSR4 is open hardware with open firmware. Each part of the repository has the licence that
fits it:

| Part | Paths | Licence |
|---|---|---|
| Hardware design | `hardware/` (KiCad project, libraries, circuit source, fabrication files, pinout data) | [CERN-OHL-S-2.0](CERN-OHL-S-2.0.txt) (strongly reciprocal: share your modifications under the same licence) |
| Firmware and software | `firmware/`, `fwtest/`, `.github/`, `pyproject.toml` | [MIT](MIT.txt) |
| Documentation and images | `docs/`, `validation/`, `README.md` and other Markdown files, renders in `docs/images/` | [CC-BY-SA-4.0](CC-BY-SA-4.0.txt) |

The top-level [LICENSE](../LICENSE) file is the CERN-OHL-S-2.0 text, because this is first of all
a hardware project. Copyright 2026 Bunty9.

## Credits

- **Scouter silkscreen doodle** (`hardware/lib/ssr4.pretty/Doodle_Scouter.kicad_mod`): line art
  traced from fan art of the Dragon Ball Z scouter by **camarinox** (DeviantArt). Dragon Ball
  and its designs are © Bird Studio / Shueisha, Toei Animation. Included as a tribute; not
  claimed by this project's licences.
- **Datasheets** are not redistributed here: `hardware/pinouts/*.json` record the pin data and
  the page numbers, and the BOM links each manufacturer's datasheet.
- **3D models** of the exact parts come from KiCad's library and from LCSC/EasyEDA
  (`hardware/lib/ssr4.3dshapes/`), under their respective terms.
