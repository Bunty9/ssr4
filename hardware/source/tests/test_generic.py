"""Checks that apply to every board. Keep them; add board-specific ones in test_nets.py."""

# Named nets allowed to have a single connection (e.g. a lone test pad). Keep this short.
ALLOW_SINGLE_NODE = set()


def test_no_power_pin_left_floating(nl):
    bad = [
        f"{n.ref}.{n.pin}({n.function})"
        for net in nl.nets
        if net.is_unconnected
        for n in net.nodes
        if n.pintype in ("power_in", "power_out")
    ]
    assert not bad, f"power pins with nothing attached: {bad}"


def test_no_orphan_named_nets(nl):
    """A named net with one connection is usually a typo in code ('VBUS' vs 'V_BUS')."""
    bad = [
        n.name
        for n in nl.nets
        if len(n.nodes) == 1
        and not n.name.startswith(("unconnected-", "Net-("))
        and n.base_name not in ALLOW_SINGLE_NODE
    ]
    assert not bad, f"named nets with a single connection: {bad}"


def test_has_ground(nl):
    assert any(n.base_name.upper().startswith("GND") for n in nl.nets), "no GND net"
