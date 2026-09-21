"""Regression tests for two crashes tests/record_drawn_text.py found in a 20s
scripted-input run (see tools/drawn_text.json "crashed"):

  - visuals/froggerdemo.py: KeyError('dive_timer') -- games/frogger.py moved to
    a deterministic dive clock (self.dive_clock + per-turtle dive_phase); the
    demo AI's "is this turtle about to dive?" check still read the old key.

  - visuals/peptides.py: IndexError on bead_colors[idx] -- the VIP entry's
    'coords'/'nmr_coords' (29 points, taken straight from PDB 2RRH chain A,
    which includes a trailing Gly amidation-donor residue) were one longer
    than its 'sequence' (28 residues, the biologically mature hormone without
    that terminal Gly). get_bead_colors() returns one color per sequence
    character, so indexing it by coordinate index went out of range on the
    29th point.
"""
from arcade import InputState
from visuals.froggerdemo import FroggerDemo
from visuals.peptides import Peptides, PEPTIDES
from _harness import get_sim_display, script_from_held

DT = 1.0 / 30.0
SECONDS = 20


def test_froggerdemo_ai_survives_river_rows(sandbox):
    """Run the demo long enough for the AI to reach the river rows (7-11),
    where _is_safe_at() evaluates turtle dive state. Used to raise
    KeyError('dive_timer') as soon as a turtle was checked."""
    display = get_sim_display()
    demo = FroggerDemo(display)
    demo.reset()

    max_row = 0
    for _ in range(SECONDS * 30):
        demo.update(DT)  # raised KeyError('dive_timer') on the old code
        demo.draw()
        max_row = max(max_row, demo.game.frog_row)

    # Sanity: the run actually exercised the water rows (7-11), not just the
    # road, so the turtle dive-timing check was really hit.
    assert max_row >= 7


def test_peptides_vip_coords_match_sequence_length():
    """The bug's real cause: a peptide entry with more 3D points than
    residues in its sequence. Guard against it recurring for any entry."""
    for pep in PEPTIDES:
        if pep['name'] != 'VIP':
            continue
        assert len(pep['coords']) == len(pep['sequence'])
        for model in pep.get('nmr_coords', []):
            assert len(model) == len(pep['sequence'])


def test_peptides_visual_survives_cycling_through_all_peptides(sandbox):
    """Drive the visual with scripted button presses (recorder style) that
    cycle through every peptide -- including VIP, whose mismatched coords
    used to raise IndexError on bead_colors[idx] -- and every color mode."""
    display = get_sim_display()
    obj = Peptides(display)
    obj.reset()

    # One held-then-released "action_r" click advances peptide_idx by one
    # (see Peptides.handle_input); click through every peptide at least once.
    held = [set()]
    for _ in range(len(PEPTIDES) + 2):
        held.append({"action_r"})
        held.append(set())
        held.append(set())
    # A couple of "both buttons" clicks to cycle color modes too.
    for _ in range(4):
        held.append({"action_l", "action_r"})
        held.append(set())
        held.append(set())

    for inp in script_from_held(InputState, held):
        obj.handle_input(inp)
        obj.update(DT)
        obj.draw()  # raised IndexError on the old VIP data

    assert obj.peptide_idx is not None  # reached the end without crashing
