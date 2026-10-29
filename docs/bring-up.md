# Bring-up: from a new board to a tested one

Work through the stages in order. Each stage only adds risk once the previous one has passed.
Read [safety.md](safety.md) first. Record what you measure: a [build report](https://github.com/Bunty9/ssr4/issues/new/choose)
helps everyone who builds the next one.

**You need**: a multimeter, a USB-C cable and a computer, a 24 VAC transformer (any doorbell or
garden-light transformer of 10 VA or more) and a 24 V lamp or a 47-100 Ω / 10 W resistor, and
for stage 5 an isolation transformer (or a current-limited supply) and an RCD-protected outlet.
A thermometer or thermocouple and a hot-air tool help with stage 4.

## Stage 0: inspect (no power)

- Look under magnification for solder bridges: U7 (SOT-563), J1 (USB-C), U1 (ESP32 module), U3.
- Check polarity: D1, C1 (electrolytic), C3 (tantalum), LEDs.
- Resistance checks:

| Between | Expect |
|---|---|
| TP1 (+5V) and TP3 (GND) | not a short (it charges up: reading climbs) |
| TP2 (+3V3) and TP3 (GND) | not a short |
| X1 L and N | high (the AC-DC module input; not a short) |
| any mains terminal and TP3 (GND) | open circuit (isolation) |

## Stage 1: USB power, logic only (mains disconnected)

1. Plug in USB-C. The status LED may blink once.
2. Measure **TP1**: USB's 5 V minus the forward drop of Schottky D1 (a few tenths of a volt),
   and **TP2 ≈ 3.3 V**.
3. Flash the firmware ([firmware.md](firmware.md)) and add the board to Home Assistant.
4. Check the entities: SSR temperature reads about room temperature; "NTC fault" and both
   over-temperature entities are off.
5. Switch each channel on and off: its **channel LED** follows. (The SSRs' input LEDs light too,
   but nothing is switched yet.)
6. Optional, with a logic analyzer on the CHn driver gates: all four stay low through a RESET
   press and a power cycle.

## Stage 2: thermal protections (still USB only)

1. **Firmware cutoff**: warm TH1 (the NTC, bottom right next to the ESP32 module) gently (hot air on a low setting from a
   distance, or a hair dryer) while watching "SSR temperature". At 55 °C, "Over-temperature"
   turns on and every channel turns off; ON is refused until it cools to 45 °C.
2. **Hardware cutoff**: keep warming the U7 area (between K2 and K3) towards 60 °C with all
   channels ON. When U7 trips, "Hardware over-temperature cutoff" turns on and every channel LED
   goes dark at once: the thermal switch has opened the drivers' common return, so no channel
   can be driven whatever the firmware commands (the firmware then also turns the channels off
   and refuses ON, so Home Assistant shows the true state). It releases at about 50 °C, and the
   firmware keeps the channels off until the NTC reads 45 °C.
3. Write down the temperatures at which both trips happened (the hardware switch is ±2 °C).

## Stage 3: switch real loads at a safe voltage (still USB, no mains)

The CPC40055ST works from 20 Vrms (datasheet p1), so a **24 VAC** transformer (safety extra-low
voltage) exercises every output without mains:

1. Wire the transformer's output through the 24 V lamp (or resistor) to channel 1's **L_IN**,
   and its return from **L_OUT** back to the transformer. The load must draw **at least 0.1 A**
   so the triac stays latched (holding current 50 mA, latching current 75 mA max, p2): a 24 V
   lamp of 3 W or more, or 47-100 Ω / 10 W.
2. Switch the channel from Home Assistant: the lamp follows. Repeat for channels 2-4.
3. Check that each channel's fuse is fitted (continuity L_IN to the SSR) before the next stage.

## Stage 4: first mains power-up (behind an isolation transformer)

1. **Disconnect USB** (or use a USB isolator).
2. Power **X1** (L, N) through an isolation transformer or a current-limited supply, from an
   RCD-protected outlet. Hands off the board while it is powered.
3. The board should boot and join Wi-Fi exactly as on USB; TP1 now reads 5 V from the AC-DC
   module (measure with the probe already clipped on before you power up, or not at all).
4. Connect a small mains load (a 5-10 W LED lamp) to channel 1 through L_IN / L_OUT, and switch
   it. Then the other channels.
5. Power off, wait, disconnect before touching anything.

## Stage 5: soak test

Run the intended loads (below 1 A each) for at least an hour in the enclosure you will install,
watching "SSR temperature". It should settle well below 55 °C at your ambient. If it climbs
towards the cutoff, the enclosure needs ventilation or the loads are too large.

Then install it: [installation.md](installation.md).
