"""PartSpec: what a circuit needs to instantiate a real, researched part.

Circuits never type an MPN or LCSC number. They either:
  * `registered(mpn, symbol)`  -> reads footprint/LCSC/manufacturer from research/parts.csv
  * `pending(symbol, footprint)` -> a part whose MPN research hasn't picked yet; the parts
                                    gate fails until it is replaced with `registered(...)`.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNSET = "UNSET-MPN"


@dataclass(frozen=True)
class PartSpec:
    symbol: str  # "Lib:Name" in KiCad's symbol libraries, e.g. "Device:R"
    footprint: str  # "Lib:Name" in KiCad's footprint libraries
    mpn: str = UNSET
    lcsc: str = ""
    manufacturer: str = ""
    value: str = ""  # for passives: the value this MPN actually is (checked on use)

    def with_value(self, value: str) -> PartSpec:
        return replace(self, value=value)


@lru_cache(maxsize=1)
def _registry() -> dict[str, dict]:
    path = ROOT / "research" / "parts.csv"
    with path.open(newline="", encoding="utf-8") as f:
        lines = [ln for ln in f if not ln.lstrip().startswith("#")]
    return {r["mpn"].strip().upper(): r for r in csv.DictReader(lines) if (r.get("mpn") or "").strip()}


def registered(mpn: str, symbol: str | None = None, value: str = "") -> PartSpec:
    row = _registry().get(mpn.upper())
    if row is None:
        raise KeyError(f"{mpn} is not in research/parts.csv: research it first (part-research skill)")
    if row.get("status", "").strip().lower() == "rejected":
        raise ValueError(f"{mpn} is marked rejected in research/parts.csv")
    sym = symbol or row.get("kicad_symbol", "").strip()
    fp = row.get("kicad_footprint", "").strip()
    if not sym or not fp:
        raise ValueError(f"{mpn}: parts.csv needs kicad_symbol and kicad_footprint before it can be placed")
    return PartSpec(
        symbol=sym,
        footprint=fp,
        mpn=row["mpn"].strip(),
        lcsc=row.get("lcsc", "").strip(),
        manufacturer=row.get("manufacturer", "").strip(),
        value=value,
    )


def verified_param(mpn: str, name: str) -> float:
    """A datasheet number from datasheets/pinouts/<MPN>.verified.json (two passes agreed).

    Circuit code computes values only from these. Raises until `uv run pcb pinouts consensus`
    has verified the part, so an unverified value can never reach the design.
    """
    safe = re.sub(r"[^A-Za-z0-9._+-]", "_", mpn)
    path = ROOT / "datasheets" / "pinouts" / f"{safe}.verified.json"
    if not path.exists():
        raise LookupError(f"{mpn}: no verified pinout ({path.name}); run the datasheet-pinout skill")
    params = json.loads(path.read_text(encoding="utf-8")).get("params") or {}
    if name not in params:
        raise KeyError(f"{mpn}: param {name!r} not in {path.name} (have: {sorted(params)})")
    v = params[name]
    return float(v["value"] if isinstance(v, dict) else v)


def pending(symbol: str, footprint: str, value: str = "") -> PartSpec:
    return PartSpec(symbol=symbol, footprint=footprint, value=value)


def make(spec: PartSpec, *, value: str | None = None, ref: str | None = None, **kw):
    """Instantiate a SKiDL Part from a spec, copying MPN/LCSC/Manufacturer into fields.
    If the spec carries a value (passives), the requested value must match it."""
    from skidl import Part  # imported here so calc/spec stay importable without SKiDL

    if value and spec.value and value != spec.value:
        raise ValueError(
            f"{spec.mpn} is a {spec.value} part but the circuit needs {value}: research a part for the new value"
        )
    lib, name = spec.symbol.split(":", 1)
    args = dict(footprint=spec.footprint, **kw)
    if value or spec.value:
        args["value"] = value or spec.value
    if ref:
        args["ref"] = ref
    p = Part(lib, name, **args)
    p.fields["MPN"] = spec.mpn
    if spec.lcsc:
        p.fields["LCSC"] = spec.lcsc
    if spec.manufacturer:
        p.fields["Manufacturer"] = spec.manufacturer
    return p
