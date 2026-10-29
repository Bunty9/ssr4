# Mechanical design hand-off: heat sink and enclosure

Everything you need to design an aluminium heat sink and an enclosure for SSR4, with the numbers
measured from the 3D assembly (not estimated). Read [safety.md](safety.md) first: the heat sink
and the enclosure are part of the electrical safety of this board.

> **Verify on the real parts before cutting metal.** The geometry below comes from the
> manufacturers' 3D models placed on the board and checked against the footprints. Real parts
> have tolerances (the SSR's body is ±0.25 mm, datasheet p8), and through-hole parts may sit a
> little higher than modelled. Measure one assembled board with calipers before you machine.

## 1. Files and coordinate frame

Generated with `uv run pcb step` (in the design repo) and published in
[`hardware/mechanical/`](../hardware/mechanical/):

| File | Content |
|---|---|
| `ssr4-assembly.step` | board + all 67 parts with 3D models (the manufacturers' STEP models, positioned to match the checked 3D view) |
| `ssr4-board-only.step` | the bare board with its holes |
| `ssr4-outline.dxf` | board outline (Edge.Cuts), mm |

**Frame used throughout this document and in the files:**

- **Origin** = the board's lower-left corner (the USB-C / ESP32 edge is "bottom", the screw
  terminals are "top").
- **X** along the 90 mm edge, left → right (K1 … K4, then the AC-DC module).
- **Y** along the 75 mm edge, bottom → top (USB-C at Y ≈ 0, terminals at Y ≈ 75).
- **Z** up; the board's bottom face is Z = 0, its top face Z = 1.51 mm (1.6 mm nominal).

```
 Y=75 ┌──────────────────────────────────────────────────────────────┐  ← wire entry side
      │ [X2 CH1][X3 CH2][X4 CH3][X5 CH4]  F1    [X1 AC IN L N]   (H2)│    (screw terminals)
      │  F2      F3      F4      F5      RV1                         │
      │ ┃K1     ┃K2     ┃K3     ┃K4  ─→ DCB faces point +X ┌───────┐ │   MAINS ZONE
      │ ┃       ┃       ┃       ┃                           │  PS1  │ │   (top ~45 mm)
      │ ┃       ┃  U7◄ thermal  ┃      (doodle)             │HLK-PM01│ │
      │ ┃       ┃   cutoff      ┃         U2 C3             │       │ │
      │ ┃       ┃       ┃       ┃                           └───────┘ │ - - - - - - - - -
      │  D4(CH1)        TP5    D7(CH4)  TP4  SW2   D6(CH3) D5(CH2)   │   LOW-VOLTAGE ZONE
      │ [safety label]   SW1(BOOT)    J1 USB-C  ┌─ U1 ESP32 ─┐ D3 TP │   (bottom ~30 mm)
 Y=0  └(H3)──────────────────────────[USB]──────[ antenna ]────────(H4)┘
      X=0                                                         X=90
```

## 2. The board

| Feature | Value |
|---|---|
| Outline | 90.0 × 75.0 mm, rectangular, 1.6 mm FR4 |
| Mounting holes | 4 × Ø3.2 mm (M3), non-plated, at (3.5, 3.5), (86.5, 3.5), (3.5, 71.5), (86.5, 71.5) |
| **Top holes H1 (3.5, 71.5) and H2 (86.5, 71.5)** | **plastic screws only** (silkscreen "NYLON"): they sit 8-10 mm from mains terminals, and a metal screw or heat-set insert would bridge the 6.5 mm isolation gap to the low-voltage ground pour |
| Bottom holes H3 (3.5, 3.5) and H4 (86.5, 3.5) | metal is fine |
| Underside | **live mains solder joints** (terminals, fuses, SSR and AC-DC pins). No metal under the board. |

### Height envelope (Z from the board's bottom face)

| Part | Footprint on the board (X × Y, mm) | Top Z | Below the board |
|---|---|---|---|
| **K1-K4 SSRs** (CPC40055ST) | X 9.85-13.67 (+12.02 per SSR) × Y 13.7-51.8 | **23.5** (tallest) | leads to Z = -3.4 |
| PS1 AC-DC module (HLK-PM01) | X 67.3-87.8 × Y 23.1-57.9 | 16.7 | pins to Z = -3.3 |
| X1-X5 screw terminals | X2 7.6-18.3, X3 +12.0, X4 +24.1, X5 +36.1; X1 68.9-79.7; all Y 63.5-73.5 | 15.6 | -1.9 |
| RV1 varistor | X 58.5-65.2 × Y 48.5-60.5 | 13.6 | -1.4 |
| F1-F5 fuses | F2 X 7.5-11.5 × Y 53.3-61.8 (+12 per channel); F1 X 58-62 × Y 61.3-69.8 | 10.1 | -1.9 |
| C1 electrolytic | X 78.1-85.9 × Y 12.6-19.1 | 7.0 | - |
| J1 USB-C | X 47.5-56.5 × Y -0.5-7.4 | 4.9 | (sticks out 0.5 mm past the bottom edge) |
| U1 ESP32-C3 module | X 63.4-76.6 × Y -0.1-16.5 | 4.1 | - |
| everything else (SMD) | | ≤ 3.7 | - |

So: **≥ 23.5 mm above the board's bottom face** for the parts, **≥ 3.4 mm below** for leads.

## 3. Heat: where it comes from and how much

| Source | Power at the design load | Basis |
|---|---|---|
| Each SSR at 1 A | about 1 W (rough: on-state drop 0.85 V typ / 1.1 V max at 2 A peak, CPC40055ST p2) | 4 W with all four channels at 1 A |
| AC-DC module | not specified at this load in the extracted data: **measure** | 3 W module |
| AMS1117 regulator | about 0.17 W average | design review M7 |
| ESP32-C3 | a few hundred mW (Wi-Fi bursts) | |

Without any heat sink the SSR datasheet gives **27 °C/W junction-to-ambient in free air** (p3):
1 W makes the junction 27 °C above the air around it, far below its 150 °C limit. **At the
design load (below 1 A per channel) the board does not need a heat sink.** What it needs is air:
the SSRs and the AC-DC module heat the inside of a closed box, and two protections watch that
temperature:

- the **hardware cutoff U7** (TMP302, at X 30.0, Y 23.5, between K2 and K3, low on the board)
  switches every SSR off at **60 °C ± 2 °C** and releases at ~50 °C;
- the **firmware cutoff** (NTC TH1, near the ESP32 at X 77.8, Y 3.3) switches off at 55 °C and
  resumes at 45 °C.

A heat sink is worth it if you want lower internal temperatures (longer life, more margin to the
cutoffs) or plan to raise the loads later. **It does not raise the board's ratings by itself**:
the 2 A fuses, the 1 A design load, the copper and the cutoff thresholds would all need
re-checking for higher currents.

## 4. Designing the heat sink

### The SSR's thermal face

- Each CPC40055ST is a flat, vertical package: **38.1 mm long (along Y) × 3.8 mm thick (along X)**,
  plastic body from **Z ≈ 5-6 mm** (the model, sliced at 1 mm steps) up to **Z ≈ 23.5 mm**. Below that there are only the
  four bare leads (pins 1-2 mains, pins 3-4 low-voltage).
- One side is a **ceramic DCB (direct copper bond) substrate**, the "not to be soldered" face in
  the datasheet drawing (p8). On SSR4 **every DCB face points +X** (towards the AC-DC module).
  In the 3D view it is the gold rectangle, about **35 mm × 16 mm**, roughly **Z 6-22 mm**,
  inset ~1.5 mm from the body edges. Confirm on the real part.
- Junction-to-case through that face: **0.35 °C/W** (p1, p3). The datasheet's own rating with a
  heat sink: 20 A with a 5 °C/W sink, against 5 A without one (p1); sizing method on p3:
  θ_CA = (T_J − T_A) / P − θ_JC.
- The DCB ceramic **isolates** the face from the semiconductor (2500 Vrms, p1). Treat the heat
  sink as an accessible metal part anyway (see the safety rules below).

### Available space

| Space | Size |
|---|---|
| Gap between neighbouring SSRs (K1's DCB face to K2's back, etc.) | **8.2 mm** (X), the full 38 mm (Y), Z ≈ 6-23.5 |
| In front of K4's DCB face (towards PS1) | ~8.8 mm before RV1 (which only spans Y 48.5-60.5); low parts U2, C3 (top Z 3.7) below Y 31; silkscreen doodle at (58.5, 39) |
| Above the SSRs | free up to your lid |
| U7 thermal cutoff | sits on the board between K2 and K3 (Z ≤ 2.2): a fin in that gap shades it, which is fine, but do not press anything onto it |

### Two workable concepts

1. **Clip-on plate per SSR (simplest).** An aluminium plate 3-4 mm thick, about 35 × 16 mm, with a
   thermal pad on the DCB face, held by a spring clip over the SSR's top edge, with fins rising
   above the SSRs. Fits the 8.2 mm gaps with room for the pad and a clip.
2. **Comb (one part for all four).** A bar above the SSR tops with four fingers that drop into the
   gaps and press a thermal pad against each DCB face. Fins on the bar. One part to earth. The
   finger pressure must come from the bar's mounting (to the case, not to the board), not from
   the SSR leads.

Use a **silicone thermal pad** (0.5-1 mm, ≥ 1 W/m·K, rated for > 100 °C) rather than paste: it
fills the gap tolerance and adds a second insulating layer.

### Safety rules for the heat sink (hard)

1. **Stay off the leads and the board.** No part of the heat sink below **Z = 8 mm** (6.5 mm above
   the board's top face). Contact the DCB face only above that line. Bare leads (mains *and*
   low-voltage) are below Z ≈ 5-6 mm.
2. **6.5 mm from every low-voltage part and every mains conductor**, measured from the heat sink,
   except its contact with the DCB faces: a floating metal part close to both would bridge the
   isolation. Watch the SSR tops at the terminal end (mains pins below them) and the area around
   D7, TP4, U2, C3 in front of K4.
3. **Earth it.** Connect the heat sink to protective earth (PE) with a crimped ring lug and a
   green/yellow wire to the switchboard's earth bar. The board has no PE terminal (X1 is L and N
   only), so this is a separate wire inside the case.
4. **Mount it to the case, not to the SSRs or the board.** The SSR leads are not a mechanical
   support, and thermal cycling must not lever them.
5. **Keep it away from the antenna**: no metal near X 63.4-76.6, Y 0-5.4 (the ESP32-C3 antenna at
   the bottom edge); ~15 mm is a common rule of thumb, see Espressif's ESP32-C3 hardware design
   guidelines for the module's official clearances.

## 5. Designing the enclosure

### Size (starting point)

| Direction | Inside dimension | Why |
|---|---|---|
| X | 90 + 2 × 1 mm | board + clearance |
| Y | 75 + 2 × 1 mm, plus wire room at the top | board + clearance; mains wires enter at Y = 75 |
| Z | **standoffs ≥ 7 mm** + 1.6 mm board + **≥ 25 mm** above the board (+ heat sink) | leads reach Z = -3.4 below the board (live); tallest part Z = 23.5 |

With 2 mm walls that is roughly **96 × 85 × 40 mm** outside without a heat sink.

### Mounting the board

- Four bosses at the hole positions (§2). Standoff height ≥ 7 mm keeps the live solder joints well
  above the case floor.
- **H1 and H2 (top, next to the terminals): plastic screws** into plastic bosses (or nylon bolts and
  nuts). No metal heat-set inserts there. H3 and H4 may use metal.
- The floor under the board must be **insulating** (it is, in a printed case). Do not mount the
  board on a metal plate or a metal back box without an insulating sheet and ≥ 6.5 mm spacing.

### Openings

| Opening | Where (frame of §1) | Notes |
|---|---|---|
| **Mains wires** | +Y wall, in front of the terminals: X2 centre X ≈ 12.9, X3 ≈ 25.0, X4 ≈ 37.0, X5 ≈ 49.0, X1 ≈ 74.3; the terminal bodies span Z ≈ 1.5-15.6 (find the wire holes in the STEP) | wires enter parallel to the board; screw heads face up (+Z), so the lid must come off (or have holes) for a screwdriver |
| USB-C (optional) | -Y wall, centre X ≈ 52.0, Z ≈ 0.7-4.9 | only for flashing with **mains disconnected**; consider no opening (flash before assembly, then OTA) or a plug with a label "no USB while mains is connected" |
| BOOT / RESET (optional) | SW1 (BOOT) at X 40.5, Y 10.5; SW2 (RESET) at X 61.9, Y 19.9; top Z 3.1 | pin-holes for a paper clip are enough; only needed for the first flash |
| Status LED | D3 at X 80.7, Y 3.2 | light pipe or a thin window |
| Channel LEDs | CH1 = D4 at (9.2, 16.3), CH2 = D5 at (84.4, 20.7), CH3 = D6 at (73.7, 20.7), CH4 = D7 at (51.2, 19.3) | not in channel order (design review L4): label the windows on the lid |
| Ventilation | low slots near the bottom half (cool air in) and high slots above the SSRs and PS1 (warm air out) | slots ≤ 2.5 mm wide (finger and tool safe, IP3X-style); none directly above the mains terminals |

### Inside the case

- **Separate the mains wiring from the low-voltage half.** Loose wires carry mains; keep them in
  the top compartment (Y > ~62, above the fuses) with a printed rib, and give them strain
  relief at the +Y wall. The 6.5 mm spacing on the PCB does not apply to loose wires.
- Keep the **antenna end** (bottom edge, X 63-77) free of metal, PE wiring and screws.
- Leave the **test pads** reachable if you want to debug in the case: TP1 +5V (81.7, 10.4),
  TP2 +3V3 (69.9, 19.9), TP3 GND (85.0, 9.2), TP4 EN (55.5, 23.0), TP5 BOOT (32.6, 15.1),
  TP6 UART TX (61.3, 7.8), TP7 UART RX (60.6, 11.0).

### Material

Inside temperature can reach the 55-60 °C cutoff range, so **not PLA** (it softens around
55-60 °C). Use **PETG, ASA, ABS or PC**; a flame-retardant grade (UL94 V-0, e.g. PC/ABS FR) is
the right choice for a box with mains inside. Walls ≥ 2 mm.

## 6. Checklist before you print or machine

- [ ] Real SSR measured: body bottom height, DCB face size and position.
- [ ] Heat sink lowest point ≥ Z 8 mm, ≥ 6.5 mm from leads, pads and low-voltage parts, earthed,
      mounted to the case, nothing metal near the antenna.
- [ ] Standoffs ≥ 7 mm, insulating floor, plastic screws in H1/H2.
- [ ] Mains wire entry and strain relief at +Y, rib separating the wiring from the low-voltage half.
- [ ] Screwdriver access to the terminals.
- [ ] Vents low and high, ≤ 2.5 mm slots, not above the terminals.
- [ ] After assembly: the soak test in [bring-up.md](bring-up.md) (stage 5), with the lid on,
      watching "SSR temperature" and checking it stays well below 55 °C at your loads.
