"""labgrid resources and drivers this repo adds (import from an environment file: `imports: [fwtest.drivers]`)."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import attr
from labgrid.driver.common import Driver
from labgrid.driver.exception import ExecutionError
from labgrid.factory import target_factory
from labgrid.protocol import PowerProtocol
from labgrid.resource.common import Resource
from labgrid.step import step


@target_factory.reg_resource
@attr.s(eq=False)
class HostProgram(Resource):
    """A native firmware build (ESPHome `host`, Zephyr `native_sim`): path relative to the env file."""

    path = attr.ib(validator=attr.validators.instance_of(str))
    args = attr.ib(factory=list, validator=attr.validators.instance_of(list))
    env = attr.ib(factory=dict, validator=attr.validators.instance_of(dict))


@target_factory.reg_resource
@attr.s(eq=False)
class ESPHomeAPI(Resource):
    """Where an ESPHome device serves its native API. The Noise key is given literally only for
    PC simulations (test-only keys); real boards name an environment variable that holds it."""

    address = attr.ib(validator=attr.validators.instance_of(str))
    port = attr.ib(default=6053, validator=attr.validators.instance_of(int))
    noise_psk = attr.ib(default=None, validator=attr.validators.optional(attr.validators.instance_of(str)))
    noise_psk_env = attr.ib(default=None, validator=attr.validators.optional(attr.validators.instance_of(str)))

    def key(self) -> str | None:
        if self.noise_psk_env:
            value = os.environ.get(self.noise_psk_env)
            if not value:
                raise ExecutionError(f"set {self.noise_psk_env} to the device's API encryption key")
            return value
        return self.noise_psk


@target_factory.reg_driver
@attr.s(eq=False)
class HostProcessDriver(Driver, PowerProtocol):
    """Runs a HostProgram as the device under test. Power on starts it, power off stops it, so
    tests power-cycle a PC simulation exactly as they would a real board on a switched outlet.
    Each power-up gets a fresh preferences directory (ESPHOME_PREFDIR): no state survives."""

    bindings = {"program": "HostProgram"}

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        self._proc: subprocess.Popen | None = None
        self._log = None
        self.console_log: Path | None = None  # the program's stdout: boot logs, which arrive before any API client

    def on_deactivate(self):
        self.off()

    def _path(self) -> Path:
        p = self.program.path
        if self.target.env:
            p = self.target.env.config.resolve_path(p)
        return Path(p)

    @Driver.check_active
    @step()
    def on(self):
        if self._proc and self._proc.poll() is None:
            return
        path = self._path()
        if not path.exists():
            raise ExecutionError(f"{path} does not exist: build the firmware first (esphome compile firmware/sim.yaml)")
        if self.console_log is not None:  # keep only the latest run's directory
            shutil.rmtree(self.console_log.parent, ignore_errors=True)
        run_dir = Path(tempfile.mkdtemp(prefix="fw-host-"))
        self.console_log = run_dir / "console.log"
        self._log = self.console_log.open("wb")
        env = {**os.environ, "ESPHOME_PREFDIR": str(run_dir), **self.program.env}
        self._proc = subprocess.Popen(
            [str(path), *self.program.args], stdout=self._log, stderr=subprocess.STDOUT, cwd=run_dir, env=env
        )

    @Driver.check_active
    @step()
    def off(self):
        if self._proc is not None:
            if self._proc.poll() is None:
                self._proc.terminate()
                try:
                    self._proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._proc.kill()
                    self._proc.wait()
            self._proc = None
        if self._log is not None:
            self._log.close()
            self._log = None

    def console(self) -> str:
        """Everything the program printed since power-on, without terminal colour codes."""
        if self.console_log is None or not self.console_log.exists():
            return ""
        return re.sub(r"\x1b\[[0-9;]*m", "", self.console_log.read_text(errors="replace"))

    @Driver.check_active
    @step()
    def cycle(self):
        self.off()
        self.on()
