"""Design calculations used by circuit blocks. Pure Python, no SKiDL, fully unit-tested.

Rule: every computed component value in a circuit comes from a function here (or a new one
added here with a test), with the datasheet formula and page cited at the call site.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

E6 = [1.0, 1.5, 2.2, 3.3, 4.7, 6.8]

E24 = [
    1.0,
    1.1,
    1.2,
    1.3,
    1.5,
    1.6,
    1.8,
    2.0,
    2.2,
    2.4,
    2.7,
    3.0,
    3.3,
    3.6,
    3.9,
    4.3,
    4.7,
    5.1,
    5.6,
    6.2,
    6.8,
    7.5,
    8.2,
    9.1,
]
E96 = [
    1.00,
    1.02,
    1.05,
    1.07,
    1.10,
    1.13,
    1.15,
    1.18,
    1.21,
    1.24,
    1.27,
    1.30,
    1.33,
    1.37,
    1.40,
    1.43,
    1.47,
    1.50,
    1.54,
    1.58,
    1.62,
    1.65,
    1.69,
    1.74,
    1.78,
    1.82,
    1.87,
    1.91,
    1.96,
    2.00,
    2.05,
    2.10,
    2.15,
    2.21,
    2.26,
    2.32,
    2.37,
    2.43,
    2.49,
    2.55,
    2.61,
    2.67,
    2.74,
    2.80,
    2.87,
    2.94,
    3.01,
    3.09,
    3.16,
    3.24,
    3.32,
    3.40,
    3.48,
    3.57,
    3.65,
    3.74,
    3.83,
    3.92,
    4.02,
    4.12,
    4.22,
    4.32,
    4.42,
    4.53,
    4.64,
    4.75,
    4.87,
    4.99,
    5.11,
    5.23,
    5.36,
    5.49,
    5.62,
    5.76,
    5.90,
    6.04,
    6.19,
    6.34,
    6.49,
    6.65,
    6.81,
    6.98,
    7.15,
    7.32,
    7.50,
    7.68,
    7.87,
    8.06,
    8.25,
    8.45,
    8.66,
    8.87,
    9.09,
    9.31,
    9.53,
    9.76,
]


def _values(series: list[float], lo_decade: int = -1, hi_decade: int = 7):
    for d in range(lo_decade, hi_decade + 1):
        for m in series:
            yield round(m * 10**d, 6)


def e_up(x: float, series: list[float] = E24) -> float:
    """Smallest standard value >= x."""
    if x <= 0:
        raise ValueError("value must be positive")
    return min(v for v in _values(series) if v >= x * (1 - 1e-9))


def e_down(x: float, series: list[float] = E24) -> float:
    """Largest standard value <= x."""
    if x <= 0:
        raise ValueError("value must be positive")
    return max(v for v in _values(series) if v <= x * (1 + 1e-9))


def e_nearest(x: float, series: list[float] = E96) -> float:
    if x <= 0:
        raise ValueError("value must be positive")
    return min(_values(series), key=lambda v: abs(math.log(v / x)))


def fmt_ohms(r: float) -> str:
    """5100 -> '5.1k', 1500000 -> '1.5M', 47 -> '47'."""
    for div, suffix in ((1e6, "M"), (1e3, "k"), (1, "")):
        if r >= div:
            s = f"{r / div:.3g}"
            return f"{s}{suffix}"
    return f"{r:.3g}"


@dataclass(frozen=True)
class LedDrive:
    r_ohms: float
    i_actual_a: float
    p_resistor_w: float

    @property
    def value(self) -> str:
        return fmt_ohms(self.r_ohms)


def led_resistor(v_supply: float, v_f: float, i_f: float, series: list[float] = E24) -> LedDrive:
    """Series resistor R = (Vsupply - Vf) / If, rounded UP so the LED never exceeds If."""
    if v_supply <= v_f:
        raise ValueError(f"supply {v_supply} V must exceed LED Vf {v_f} V")
    r = e_up((v_supply - v_f) / i_f, series)
    i = (v_supply - v_f) / r
    return LedDrive(r, i, i * i * r)


@dataclass(frozen=True)
class InputDrive:
    r_ohms: float
    i_min_a: float  # lowest supply, highest series drop
    i_max_a: float  # highest supply, lowest series drop
    p_resistor_w: float  # at i_max

    @property
    def value(self) -> str:
        return fmt_ohms(self.r_ohms)


def input_drive_resistor(
    v_supply: tuple[float, float],
    v_drop: tuple[float, float],
    i_min: float,
    i_max: float,
    series: list[float] = E24,
    p_rated: float | None = None,
    p_derate: float = 0.5,
) -> InputDrive:
    """Series resistor for a current-driven input that must turn ON (an SSR or optocoupler LED,
    optionally with an indicator LED and a switch in series).

    v_supply and v_drop are (min, max); v_drop is the total of everything in series (input LED
    Vf + indicator Vf + switch drop). R is rounded DOWN so the input still gets i_min at the
    worst corner (lowest supply, highest drop). Raises if the other corner then exceeds i_max,
    or, given the resistor's power rating, if it dissipates more than p_derate of it there.
    """
    headroom = v_supply[0] - v_drop[1]
    if headroom <= 0:
        raise ValueError(f"no headroom: supply {v_supply[0]} V <= series drop {v_drop[1]} V")
    r = e_down(headroom / i_min, series)
    i_lo = headroom / r
    i_hi = (v_supply[1] - v_drop[0]) / r
    if i_hi > i_max:
        raise ValueError(f"{fmt_ohms(r)}: {i_hi * 1e3:.1f} mA at the high corner exceeds {i_max * 1e3:.1f} mA")
    p = i_hi * i_hi * r
    if p_rated is not None and p > p_rated * p_derate:
        raise ValueError(
            f"{fmt_ohms(r)} dissipates {p * 1e3:.0f} mW at the high corner, over {p_derate:.0%} of its "
            f"{p_rated * 1e3:.0f} mW rating: use a larger package"
        )
    return InputDrive(r, i_lo, i_hi, p)


def trace_width_mm(current_a: float, rise_c: float, copper_oz: float) -> float:
    """Minimum trace width for a current, from the IPC-2152 unified fit (valid for a rise of
    2-100 C and up to 30 A): Ac[sq.mil] = (117.555 * dT^-0.913 + 1.15) * I^(0.84 * dT^-0.108 + 1.159),
    width = Ac / (oz * 1.37 mil). Source: pcbparts design rules guides/pcb-layout (IPC-2152).
    Nearby planes make the real rise lower; this is the conservative bare-trace number.
    """
    if not (2 <= rise_c <= 100) or not (0 < current_a <= 30) or copper_oz <= 0:
        raise ValueError("outside the fit's range: rise 2-100 C, current 0-30 A")
    area = (117.555 * rise_c**-0.913 + 1.15) * current_a ** (0.84 * rise_c**-0.108 + 1.159)
    return area / (copper_oz * 1.37) * 0.0254


@dataclass(frozen=True)
class Divider:
    r_top: float
    r_bottom: float
    v_out: float
    error_pct: float


def feedback_divider(v_out: float, v_ref: float, r_bottom: float, series: list[float] = E96) -> Divider:
    """Regulator feedback: Vout = Vref * (1 + Rtop / Rbottom). Check the datasheet's own formula
    first: some parts add an offset or a fixed internal resistor."""
    if v_out <= v_ref:
        raise ValueError("v_out must exceed v_ref")
    r_top = e_nearest(r_bottom * (v_out / v_ref - 1), series)
    actual = v_ref * (1 + r_top / r_bottom)
    return Divider(r_top, r_bottom, actual, 100 * (actual - v_out) / v_out)


T0_K = 273.15


def ntc_resistance(t_c: float, r25: float, beta: float) -> float:
    """NTC resistance by the B-parameter equation R = R25 * exp(B * (1/T - 1/T25)), T in kelvin.
    Feed R25 and B (usually B25/50) from the datasheet; away from 25-50 C it is an approximation
    unless the datasheet gives an R-T table to check against."""
    return r25 * math.exp(beta * (1 / (t_c + T0_K) - 1 / (25 + T0_K)))


def ntc_divider_v(t_c: float, v_ref: float, r_top: float, r25: float, beta: float) -> float:
    """Voltage across an NTC at the bottom of a divider: v_ref - r_top - out - NTC - GND."""
    r = ntc_resistance(t_c, r25, beta)
    return v_ref * r / (r_top + r)


def ntc_divider_t(v: float, v_ref: float, r_top: float, r25: float, beta: float) -> float:
    """Inverse of ntc_divider_v: temperature in C for an output voltage strictly inside (0, v_ref)."""
    if not 0 < v < v_ref:
        raise ValueError(f"{v} V is outside the divider's open range (0, {v_ref})")
    r = r_top * v / (v_ref - v)
    return 1 / (1 / (25 + T0_K) + math.log(r / r25) / beta) - T0_K
