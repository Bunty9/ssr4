"""Firmware test harness: labgrid drivers and device clients shared by every board's firmware tests.

Tests talk to a device through labgrid targets (boards/<b>/firmware/targets/*.yaml), so the same
test runs against a native PC build, an emulator or the real board. Needs the `fw` dependency
group (labgrid, aioesphomeapi); pcbtools itself stays standard-library only.
"""
