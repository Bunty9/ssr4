# Getting SSR4 made

Everything a board house needs is in [`hardware/fabrication/`](../hardware/fabrication/), checked
by the design's release gate before it was published ("GATE RELEASE: PASS", see
[validation](../validation/README.md)). Two ready-made packages are included:

| Fab | Folder | Gerbers + drill | BOM | Placement (CPL) | Assembly service |
|---|---|---|---|---|---|
| **JLCPCB** | `hardware/fabrication/jlcpcb/` | `ssr4-jlcpcb-gerbers.zip` | `bom.csv` (LCSC part numbers) | `cpl.csv` (all 67 parts, SMD and through-hole) | Standard PCBA (needed for the through-hole parts) |
| **PCBWay** | `hardware/fabrication/pcbway/` | `ssr4-pcbway-gerbers.zip` | `bom.csv` (manufacturer part numbers) | `cpl.csv` (SMD parts; through-hole placed from the BOM) | Turnkey |

`ORDER-NOTES.txt` in each folder repeats the options below.

## PCB options (not in the Gerbers: set them on the order form)

| Option | Value | Why |
|---|---|---|
| Layers | 2 | |
| Size | 90 × 75 mm | |
| Thickness | 1.6 mm | |
| **Outer copper** | **2 oz** | the mains tracks are sized for 2 oz |
| Surface finish | HASL lead-free | |
| Solder mask / silkscreen | green / white | any colour works; white silk shows the safety label and doodle best on green |
| Impedance control | no | |
| Quantity | 5 (minimum at most fabs) | |

## Ordering at JLCPCB (assembled)

1. Upload `ssr4-jlcpcb-gerbers.zip`. Check the preview: 90 × 75 mm, 2 layers, the four long SSR
   footprints in a row, the safety label at the bottom left.
2. Set the options in the table above (do not forget **2 oz**).
3. Enable **PCB Assembly**: **Standard** PCBA, **top side**, and tick through-hole assembly if
   offered separately.
4. Upload `bom.csv` and `cpl.csv`.
5. **Parts review**: every line must match the LCSC number in `bom.csv`; nothing may be left
   "unmatched" or swapped for an alternative. The CPC40055ST SSRs (C1527353) are the expensive
   and stock-limited line.
6. **Placement preview**, check before you pay:
   - K1-K4 (SSRs) and PS1 (AC-DC module) through-hole, sitting on their footprints;
   - J1 (USB-C) opening at the bottom edge, U1 (ESP32) antenna at the bottom edge;
   - polarity of D1 (Schottky), C3 (tantalum), C1 (electrolytic), the LEDs;
   - pin 1 of U7 (TMP302, tiny SOT-563 next to K2/K3) and U3 (USBLC6).
   If a part is rotated wrongly, fix it in the preview tool (and tell us in an issue so the
   rotation table can be corrected).
7. Order. Keep the order number for your build report.

## Ordering at PCBWay (turnkey)

Upload the PCBWay Gerber zip, choose **Turnkey assembly**, upload `bom.csv` and `cpl.csv`, and
set the same PCB options. PCBWay may propose substitutes for some parts: accept none for the
SSRs, fuses, varistor, AC-DC module, TMP302 or the ESP32 module without checking the datasheet
against the design.

## What it costs

Parts for **5 boards**: about **$530** at JLCPCB prices of 2026-10-28/29
([`hardware/bom-sourced.csv`](../hardware/bom-sourced.csv)), that is about **$106 per board**,
before PCB, assembly fees, shipping and import duties.

- The four **CPC40055ST SSRs** are **$486** of that ($24.32 each). Everything else is about
  $8.70 per board.
- 15 of the 27 part types are JLCPCB "extended" parts, each with a small loading fee.
- Prices and stock change daily; the quote you get is the real number.

> **Cheaper variant idea**: the SSRs dominate the cost. An opto-triac (e.g. a MOC306x zero-cross
> driver) plus a discrete triac per channel would cut the parts cost several-fold, at the price
> of a redesign, more heat-sinking thought and new verification. Contributions welcome.

## Building it yourself

You can order bare PCBs and solder the board by hand:

- **Through-hole** (SSRs, AC-DC module, fuses, varistor, terminals): straightforward with an iron.
- **Fine-pitch / bottom-pad parts**: the ESP32-C3 module (pads underneath), the USB-C receptacle
  (0.5 mm pitch) and U7 TMP302 (SOT-563, 0.5 mm pitch, 1.6 × 1.6 mm) need solder paste and a
  hot plate or hot air. A stencil makes it much easier.
- Use the KiCad project (or the PDFs in `hardware/`) and the placement file for positions.
- Inspect under magnification before power-up: solder bridges on U7, J1 and U1 are the likely
  defects.

## Datasheets

Datasheets are not redistributed. `hardware/fabrication/*/bom.csv` lists each part, and
`hardware/pinouts/*.verified.json` records the datasheet revision and the page every pin and
rating came from.

Next: [bring-up.md](bring-up.md).
