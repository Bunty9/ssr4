# Firmware: build, flash and connect to Home Assistant

SSR4 runs [ESPHome](https://esphome.io) **2026.10.0** (ESP-IDF framework) and talks to
[Home Assistant](https://www.home-assistant.io) over ESPHome's encrypted native API, on your
local network, with no cloud.

> Flash the board **from USB-C with mains disconnected**. The board runs entirely from USB for
> this (see [safety.md](safety.md)).

## 1. Install ESPHome

```bash
# any one of these
pip install "esphome==2026.10.0"
uv tool install --python 3.13 "esphome==2026.10.0"
```

ESPHome needs Python 3.11-3.13. (Ubuntu's system Python may lack `venv`/`ensurepip`, which the
ESP-IDF build uses; a `uv`-managed Python avoids that.)

## 2. Create your secrets

```bash
cd firmware
cp secrets.example.yaml secrets.yaml
python3 -c "import secrets,base64;print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

Edit `secrets.yaml`:

| Key | What |
|---|---|
| `wifi_ssid`, `wifi_password` | your Wi-Fi |
| `fallback_ap_password` | password of the setup hotspot the board opens if it cannot join Wi-Fi (8+ characters) |
| `ota_password` | protects over-the-air updates |
| `api_encryption_key` | the 32-byte key printed above; Home Assistant asks for it |

`secrets.yaml` is git-ignored. There are no default passwords anywhere in the firmware.

## 3. First flash over USB-C

```bash
esphome run ssr4.yaml --device /dev/ttyACM0
```

- The ESP32-C3's native USB shows up as `/dev/ttyACM0` on Linux (`COMx` on Windows, `/dev/cu.usbmodem*` on macOS).
- If it doesn't appear, or the upload fails: hold **BOOT**, tap **RESET**, release **BOOT**, and try again (download mode).
- On Linux, add yourself to the `dialout` group if you get "permission denied".

After flashing, the log shows the board joining Wi-Fi. If it can't, it opens the hotspot
**`ssr4-setup`**; connect to it and enter Wi-Fi details in the captive portal.

## 4. Add it to Home Assistant

Home Assistant discovers the board by mDNS: **Settings → Devices & services**, then the
discovered **ESPHome** device "SSR4", enter the API encryption key. (Or add the ESPHome
integration by hand with the board's IP address.)

### Entities

| Entity | Type | Notes |
|---|---|---|
| Channel 1-4 | switch | ON is refused while overheated, while the NTC reading is faulty, or while the hardware cutoff is active |
| SSR temperature | sensor (°C) | board NTC (rev A: near the ESP32 module, so it reads board rather than SSR temperature), sampled every 5 s |
| Over-temperature | binary sensor | firmware latch: on at 55 °C, off at 45 °C |
| NTC fault | binary sensor | open/shorted NTC or reading outside the ADC's trusted range; channels off |
| Hardware over-temperature cutoff | binary sensor | the 60 °C thermal switch has cut all outputs |
| MCU temperature | sensor (°C) | ESP32-C3 internal sensor |
| Wi-Fi signal | sensor (dBm) | every 60 s |
| Uptime | sensor | |
| Status | binary sensor | API connection |
| Restart | button | |

### Behaviour you should know

- **All outputs are OFF after every power-up and reset**, by design. A power cut never turns a
  load back on by itself. (If you want "restore last state", that is a deliberate change: open
  an issue first.)
- **Over-temperature**: at 55 °C on the board NTC everything turns off and stays off until the
  board cools to 45 °C. The hardware cutoff at 60 °C works even if the firmware hangs; when it
  trips, the firmware latches the same over-temperature state, so loads stay off after the
  thermal switch releases (at about 50 °C) until the NTC reads 45 °C.
- **No automatic reboots**: `reboot_timeout` is 0 for the API and Wi-Fi, because every reboot
  turns all loads off. If Home Assistant or Wi-Fi goes away, the board keeps its outputs and
  keeps reconnecting.
- **The board refuses to switch below about 1.4 °C** board temperature: the NTC voltage is then
  above the ADC's specified 2.5 V range and is treated as a sensor fault (fail-safe).

## 5. Updates

```bash
esphome run ssr4.yaml          # choose the network (OTA) option
esphome logs ssr4.yaml         # live logs over Wi-Fi, or over USB with --device
```

## Pins

The firmware never contains a typed GPIO number: `firmware/pins.yaml` is generated from the
board's netlist and every GPIO comes from it (a test enforces this). See the pin map in
[how-it-works.md](how-it-works.md#pin-map).

## Test the firmware without the board

The same behaviour (`packages/logic.yaml`) builds as a Linux program, and the tests drive it
over the real ESPHome API: switching channels, injecting NTC voltages, tripping the cutoff.

```bash
pip install -e ".[test]"
esphome compile firmware/sim.yaml
pytest firmware/tests --lg-env firmware/targets/host.yaml
```

About 15 s for 14 tests. In the PC build, pin writes appear as log lines
(`Setting pin 3 to HIGH`), and two test-only entities ("SIM NTC voltage", "SIM hardware cutoff")
stand in for the analog input and the thermal switch. Their API key is published on purpose and
is never used on a real board. Results of the published snapshot:
[validation/README.md](../validation/README.md).

## Debugging

The C3's USB port is also a JTAG adapter: `openocd -f board/esp32c3-builtin.cfg` (Espressif's
openocd-esp32) plus `riscv32-esp-elf-gdb` with the `firmware.elf` from
`firmware/.esphome/build/ssr4/`. ESPHome logs go to USB; UART0 on test pads TP6 (TX) and TP7 (RX)
carries the ROM bootloader's messages, useful if USB never enumerates.

Next: [bring-up.md](bring-up.md).
