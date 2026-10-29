"""Netlist fixture for this board's tests. Tests read the netlist exported from the
*generated schematic*, so they check what will actually be built, not the source code."""

import os
from pathlib import Path

import pytest

from pcbtools.netlist import Netlist

BOARD_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def nl() -> Netlist:
    path = Path(os.environ.get("PCB_NETLIST", BOARD_DIR / "build" / "netlist.net"))
    if not path.exists():
        msg = f"{path} missing: run `boardforge run` in this board dir, then `uv run pcb netlist`"
        if os.environ.get("PCB_GATE"):
            pytest.fail(msg)  # inside a gate, a missing netlist is a failure, never a skip
        pytest.skip(msg)
    return Netlist.load(path)
