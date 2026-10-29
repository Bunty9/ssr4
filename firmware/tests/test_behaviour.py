"""ssr4 behaviour, on any target that serves the ESPHome API. Requirement: spec/requirements.md
"ssr4" (all outputs OFF at power-up; over-temperature cutoff), firmware/packages/logic.yaml."""

import re

import pytest

CHANNELS = (1, 2, 3, 4)
pytestmark = pytest.mark.lg_feature("esphome-api")


def _gpio(contract, signal: str) -> int:
    """Pin number as the host build logs it (contract pin name IO3 -> 3)."""
    return int(re.fullmatch(r"(?:GPIO|IO)(\d+)", contract["signals"][signal]["pin"]["name"]).group(1))


async def _ready(d, ntc_volts, t_c: float = 25.0):
    """Board at t_c with a valid NTC reading, all channels off."""
    d.number("SIM NTC voltage", round(ntc_volts(t_c), 3))
    await d.wait_state("NTC fault", False)
    for ch in CHANNELS:
        await d.wait_state(f"Channel {ch}", False)


def test_all_channels_off_after_power_up(run):
    async def body(d):
        for ch in CHANNELS:
            await d.wait_state(f"Channel {ch}", False)

    run(body)


@pytest.mark.lg_feature("gpio-log")
def test_power_up_drives_every_channel_pin_low(console, contract):
    # boot happens before any API client connects, so this reads the console, not API logs
    for ch in CHANNELS:
        console(rf"Setting pin {_gpio(contract, f'ch{ch}')} to LOW\b")


@pytest.mark.lg_feature(["gpio-log", "sim-ntc"])
@pytest.mark.parametrize("ch", CHANNELS)
def test_each_channel_drives_its_contract_pin(ntc_volts, run, contract, ch):
    async def body(d):
        await _ready(d, ntc_volts)
        pin = _gpio(contract, f"ch{ch}")
        mark = len(d.logs)
        d.switch(f"Channel {ch}", True)
        await d.wait_state(f"Channel {ch}", True)
        await d.wait_log(rf"Setting pin {pin} to HIGH\b", since=mark)
        d.switch(f"Channel {ch}", False)
        await d.wait_log(rf"Setting pin {pin} to LOW\b", since=mark)
        await d.wait_state(f"Channel {ch}", False)

    run(body)


@pytest.mark.lg_feature("sim-ntc")
def test_over_temperature_latches_until_resume(ntc_volts, run):
    async def body(d):
        await _ready(d, ntc_volts)
        d.switch("Channel 1", True)
        await d.wait_state("Channel 1", True)
        d.number("SIM NTC voltage", round(ntc_volts(56), 3))
        await d.wait_state("Over-temperature", True)
        await d.wait_state("Channel 1", False)
        for t in (56, 50):  # hot, then between resume (45 C) and cutoff (55 C): still latched
            d.number("SIM NTC voltage", round(ntc_volts(t), 3))
            d.switch("Channel 1", True)
            await d.hold("Channel 1", False, 1.0)
        d.number("SIM NTC voltage", round(ntc_volts(44), 3))
        await d.wait_state("Over-temperature", False)
        d.switch("Channel 1", True)
        await d.wait_state("Channel 1", True)

    run(body)


@pytest.mark.lg_feature("sim-ntc")
@pytest.mark.parametrize(
    "volts",
    [
        pytest.param(2.95, id="open-ntc-saturated-adc"),  # ~ -19 C: passed the old "< -20 C" check
        pytest.param(2.6, id="above-specified-adc-range"),
        pytest.param(0.1, id="shorted-ntc"),
        pytest.param(0.0, id="node-at-ground"),
    ],
)
def test_ntc_fault_turns_everything_off_and_refuses_on(ntc_volts, run, volts):
    async def body(d):
        await _ready(d, ntc_volts)
        for ch in CHANNELS:
            d.switch(f"Channel {ch}", True)
            await d.wait_state(f"Channel {ch}", True)
        d.number("SIM NTC voltage", volts)
        await d.wait_state("NTC fault", True)
        for ch in CHANNELS:
            await d.wait_state(f"Channel {ch}", False)
        d.switch("Channel 1", True)
        await d.hold("Channel 1", False, 1.0)
        await _ready(d, ntc_volts)  # a valid reading clears the fault
        d.switch("Channel 1", True)
        await d.wait_state("Channel 1", True)

    run(body)


@pytest.mark.lg_feature(["sim-ntc", "sim-hw-cutoff"])
def test_hardware_cutoff_is_reported_and_latched_until_cool(ntc_volts, run):
    """The TMP302 cuts the SSR return at 60 C by itself; firmware must not show channels ON that
    the hardware has switched off, and after the cutoff releases it keeps refusing ON until the
    NTC reads <= resume_c (45 C), so loads do not come back at the hardware's release point."""

    async def body(d):
        await _ready(d, ntc_volts, t_c=50.0)  # warm, but below the firmware cutoff
        d.switch("Channel 2", True)
        await d.wait_state("Channel 2", True)
        d.switch("SIM hardware cutoff", True)
        await d.wait_state("Hardware over-temperature cutoff", True)
        await d.wait_state("Channel 2", False)
        await d.wait_state("Over-temperature", True)  # latched by the hardware trip
        d.switch("Channel 2", True)
        await d.hold("Channel 2", False, 1.0)
        d.switch("SIM hardware cutoff", False)
        await d.wait_state("Hardware over-temperature cutoff", False)
        d.switch("Channel 2", True)  # released, but still 50 C: refused
        await d.hold("Channel 2", False, 1.0)
        d.number("SIM NTC voltage", round(ntc_volts(44), 3))
        await d.wait_state("Over-temperature", False)
        d.switch("Channel 2", True)
        await d.wait_state("Channel 2", True)

    run(body)
