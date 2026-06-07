"""Guard against sim/hardware interface drift.

The desktop sim (`arcade.Display`) and the cabinet driver (`hardware.HardwareDisplay`)
implement the same drawing interface by hand — nothing enforces it. If a method is
added to the sim and used by a visual but forgotten on HardwareDisplay, the sim (and
this whole test suite, which runs the sim) passes green while the *cabinet* crashes.

This test is the one guard that catches that hardware-only failure mode.
"""
import arcade
import hardware


def _public_methods(cls):
    return {
        name
        for name in dir(cls)
        if not name.startswith("_") and callable(getattr(cls, name))
    }


def test_hardware_display_covers_sim_interface():
    sim = _public_methods(arcade.Display)
    hw = _public_methods(hardware.HardwareDisplay)
    missing = sim - hw
    assert not missing, (
        "HardwareDisplay is missing methods the sim Display exposes: "
        f"{sorted(missing)}. A visual using these would crash on the cabinet "
        "while passing in the desktop sim."
    )
