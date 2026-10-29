"""An ESPHome native-API session for tests: entities by name, live states, log lines, waits.

async with Device(api_resource) as d:
    d.switch("Channel 1", True)
    await d.wait_state("Channel 1", True)
    await d.wait_log(r"Setting pin 3 to HIGH")
"""

from __future__ import annotations

import asyncio
import re
import time

from aioesphomeapi import APIClient, APIConnectionError, LogLevel

ANSI = re.compile(r"\x1b\[[0-9;]*m")


class Device:
    def __init__(self, api, connect_timeout: float = 20.0):
        self.api = api
        self.connect_timeout = connect_timeout
        self.client: APIClient | None = None
        self.entities: dict = {}
        self.logs: list[str] = []
        self._states: dict[int, object] = {}
        self._changed = asyncio.Event()

    async def __aenter__(self) -> Device:
        deadline = time.monotonic() + self.connect_timeout
        while True:
            client = APIClient(self.api.address, self.api.port, None, noise_psk=self.api.key(), client_info="fwtest")
            try:
                await client.connect(login=True)
                break
            except (APIConnectionError, OSError) as e:
                if time.monotonic() > deadline:
                    raise TimeoutError(f"no API at {self.api.address}:{self.api.port}: {e}") from e
                await asyncio.sleep(0.2)
        self.client = client
        infos, _ = await client.list_entities_services()
        self.entities = {i.name: i for i in infos}
        client.subscribe_states(self._on_state)
        client.subscribe_logs(self._on_log, log_level=LogLevel.LOG_LEVEL_DEBUG)
        return self

    async def __aexit__(self, *exc) -> None:
        if self.client is not None:
            await self.client.disconnect()

    def _on_state(self, s) -> None:
        self._states[s.key] = s
        self._changed.set()

    def _on_log(self, msg) -> None:
        self.logs.append(ANSI.sub("", msg.message.decode(errors="replace")))
        self._changed.set()

    def _key(self, name: str) -> int:
        if name not in self.entities:
            raise KeyError(f"no entity {name!r}; device has {sorted(self.entities)}")
        return self.entities[name].key

    def state(self, name: str):
        s = self._states.get(self._key(name))
        return None if s is None else s.state

    def switch(self, name: str, on: bool) -> None:
        self.client.switch_command(self._key(name), on)

    def number(self, name: str, value: float) -> None:
        self.client.number_command(self._key(name), value)

    async def wait_for(self, predicate, what: str, timeout: float = 5.0) -> None:
        deadline = time.monotonic() + timeout
        while not predicate():
            left = deadline - time.monotonic()
            if left <= 0:
                raise AssertionError(f"timed out after {timeout} s waiting for {what}")
            self._changed.clear()
            try:
                await asyncio.wait_for(self._changed.wait(), left)
            except TimeoutError:
                pass

    async def wait_state(self, name: str, value, timeout: float = 5.0) -> None:
        await self.wait_for(lambda: self.state(name) == value, f"{name} == {value!r}", timeout)

    async def wait_log(self, pattern: str, timeout: float = 5.0, since: int = 0) -> None:
        rx = re.compile(pattern)
        await self.wait_for(lambda: any(rx.search(m) for m in self.logs[since:]), f"log /{pattern}/", timeout)

    async def hold(self, name: str, value, seconds: float) -> None:
        """Assert a state stays at value for a while (a refused command must not flip it)."""
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            assert self.state(name) == value, f"{name} changed to {self.state(name)!r}, expected to stay {value!r}"
            await asyncio.sleep(0.05)
