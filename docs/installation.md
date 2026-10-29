# Installation

> Mains wiring. Do it only if you are competent and allowed to where you live; otherwise have an
> electrician install it. Isolate the circuit at the distribution board and prove it dead first.

## Ratings

| Item | Rating |
|---|---|
| Supply (X1) | 230 VAC, 50 Hz, single phase (the AC-DC module accepts 85-265 VAC; the design assumes 207-253 V) |
| Outputs (X2-X5) | 230 VAC loads, **below 1 A continuous per channel**, each fused 2 A time-lag on the board |
| Load types | LED lights and fans (high power factor); the SSR guarantees turn-on down to a power factor of 0.25 (CPC40055ST p2). No snubber is fitted, so strongly inductive loads (motors with poor PF, transformers) are untested |
| Ambient inside the enclosure | design assumption 50 °C; firmware cutoff 55 °C and hardware cutoff 60 °C on the board |
| Board | 90 × 75 mm, four M3 mounting holes (3.2 mm, non-plated) 3.5 mm from the corners; **the two top holes (marked NYLON) need nylon screws** |

## Wiring

```
             distribution board: MCB + RCD
                 │L                 │N
     ┌───────────┼──────────────────┼────────────────┐
     │  X1  L ◄──┤             N ◄──┤  (board supply) │
     │                                                │
     │  X2  L_IN ◄── L          L_OUT ──► load 1 L     │  load 1 N ──► N
     │  X3  L_IN ◄── L          L_OUT ──► load 2 L     │  load 2 N ──► N
     │  X4  L_IN ◄── L          L_OUT ──► load 3 L     │  load 3 N ──► N
     │  X5  L_IN ◄── L          L_OUT ──► load 4 L     │  load 4 N ──► N
     └────────────────────────────────────────────────┘
```

- **X1** powers the board only. **Each output channel has its own pair of terminals** (L_IN,
  L_OUT) and switches the **live** of its load; load neutrals go straight to the neutral bar, not
  through the board.
- **All live feeds must come from the same phase.** Channels on different phases would have
  400 V between them, more than the board's mains-to-mains spacing is designed for.
- Wire size per the screw terminals (5.08 mm pitch, 22-12 AWG) and your local rules for the
  circuit's MCB.
- An **RCD** upstream is strongly recommended.
- The silkscreen labels the supply terminal **AC IN** with **L** and **N**, and each channel
  **CH1-CH4** next to its fuse. On every channel terminal the fuse side (pin 1, marked with a
  triangle) is **L_IN**, the other pin is **L_OUT** to the load. Wiring the supply neutral to a
  channel's L_IN would switch the neutral and leave the load live when "off": check twice.
- **Mounting**: use **nylon screws in the two top holes** (marked NYLON): they are close to the
  mains terminals, and a metal screw head would bridge the 6.5 mm isolation gap to the
  low-voltage ground. Metal is fine in the two bottom holes.

## Enclosure

- A **closed, insulating enclosure** (3D-printed PETG/ASA or a flame-retardant plastic box) with
  no conductive parts reachable from outside, and room for the wiring bend radius.
- Keep the **low-voltage part of the board (bottom half: ESP32, USB-C) away from mains wiring**
  inside the box: the 6.5 mm spacing on the PCB does not extend to loose wires.
- **Ventilation**: the SSRs and the AC-DC module make heat. Leave air around them; check with the
  soak test ([bring-up.md](bring-up.md), stage 5).
- The ESP32 antenna is at the bottom edge of the board: avoid metal there for good Wi-Fi.
- The USB-C port is for flashing and must not be used while mains is connected (unless through a
  USB isolator). Updates go over the air.

## After installing

1. Restore power. The board boots with all outputs OFF and joins Wi-Fi.
2. Test each channel from Home Assistant.
3. Watch "SSR temperature" over the first days at your real loads.
