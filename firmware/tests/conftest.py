"""ssr4 firmware tests. Behaviour tests run on a labgrid target (--lg-env targets/<name>.yaml) and
need the `fw` dependency group; config tests need neither."""

import asyncio
import json
import re
import time
from pathlib import Path

import pytest

from blocks import calc

try:
    from fwtest.drivers import ESPHomeAPI
    from fwtest.esphome import Device
except ImportError:  # `fw` group not installed: only the static config tests can run
    collect_ignore = ["test_behaviour.py"]

BOARD = Path(__file__).resolve().parents[2]
FIRMWARE = BOARD / "firmware"

# The NTC divider as built (circuit/mcu.py: 3V3 - 10k - NTC node - NTC - GND) and the NTC's
# datasheet values (SDNT1608X103F3950FTF: R25 10k, B25/50 3950 K, series datasheet p3).
V_REF, R_TOP, R25, BETA = 3.3, 10_000, 10_000, 3950


@pytest.fixture(scope="session")
def ntc_volts():
    """NTC node voltage at a board temperature: what the ADC pin sees."""
    return lambda t_c: calc.ntc_divider_v(t_c, V_REF, R_TOP, R25, BETA)


@pytest.fixture(scope="session")
def logic_yaml() -> str:
    return (FIRMWARE / "packages" / "logic.yaml").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def contract() -> dict:
    path = FIRMWARE / "contract.json"
    if not path.exists():
        pytest.fail(f"{path} missing: it is generated from the netlist with pins.yaml")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def device(target):
    """A freshly powered device: a new process for the PC build, a power cycle for a board."""
    power = target.get_driver("PowerProtocol")
    target.activate(power)
    power.cycle()
    yield target.get_resource(ESPHomeAPI)


@pytest.fixture
def console(target, device):
    """wait(pattern): the device's console output (host build: the program's stdout) matches."""
    from fwtest.drivers import HostProcessDriver

    drv = target.get_driver(HostProcessDriver)

    def wait(pattern: str, timeout: float = 10.0) -> None:
        rx = re.compile(pattern)
        deadline = time.monotonic() + timeout
        while not rx.search(drv.console()):
            if time.monotonic() > deadline:
                raise AssertionError(f"timed out after {timeout} s waiting for console /{pattern}/")
            time.sleep(0.05)

    return wait


@pytest.fixture
def run(device):
    """run(body): execute `async def body(d: Device)` against the freshly powered device."""

    def _run(body, timeout: float = 60.0):
        async def main():
            async with Device(device) as d:
                await body(d)

        asyncio.run(asyncio.wait_for(main(), timeout))

    return _run
