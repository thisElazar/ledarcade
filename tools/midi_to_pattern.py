"""
MIDI Drum Track → 16-Step Pattern Converter
=============================================
Parses MIDI files, extracts drum channel (ch10), quantizes to a 16-step grid,
and outputs patterns in the format used by the LED arcade drum machine.

Usage: python3 midi_to_pattern.py <file.mid> [--bar N] [--bpm]
  --bar N   Extract bar N (1-indexed, default: auto-detect best bar)
  --bpm     Print detected BPM
  --all     Show all bars so you can pick the best one

General MIDI Drum Map (channel 10):
  35-36: Kick       → slot 0
  38-40: Snare      → slot 1
  42,44: Closed HH  → slot 2
  46:    Open HH    → slot 3
  39,54: Clap/Tamb  → slot 4
  41,43,45,47,48,50: Toms → slot 5
  37,56: Rimshot/Cowbell → slot 6
  51,53,59,49,57: Ride/Crash → slot 7
"""

import sys
import mido

# GM drum note → instrument slot mapping
GM_DRUM_MAP = {}
# Slot 0: Kick
for n in [35, 36]:
    GM_DRUM_MAP[n] = 0
# Slot 1: Snare
for n in [38, 40]:
    GM_DRUM_MAP[n] = 1
# Slot 2: Closed Hi-Hat
for n in [42, 44]:
    GM_DRUM_MAP[n] = 2
# Slot 3: Open Hi-Hat
for n in [46]:
    GM_DRUM_MAP[n] = 3
# Slot 4: Clap / Tambourine
for n in [39, 54]:
    GM_DRUM_MAP[n] = 4
# Slot 5: Toms
for n in [41, 43, 45, 47, 48, 50]:
    GM_DRUM_MAP[n] = 5
# Slot 6: Rimshot / Cowbell / Sidestick
for n in [37, 56]:
    GM_DRUM_MAP[n] = 6
# Slot 7: Ride / Crash
for n in [49, 51, 52, 53, 55, 57, 59]:
    GM_DRUM_MAP[n] = 7

SLOT_NAMES = ["KICK", "SNARE", "HAT", "OPEN", "CLAP", "TOM", "RIM", "RIDE"]


def extract_drum_events(mid):
    """Extract all drum note_on events with absolute tick positions."""
    tpb = mid.ticks_per_beat
    events = []

    if mid.type == 0:
        # Format 0: single track, all channels mixed
        abs_tick = 0
        for msg in mid.tracks[0]:
            abs_tick += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                if msg.channel == 9 or msg.note in GM_DRUM_MAP:
                    slot = GM_DRUM_MAP.get(msg.note)
                    if slot is not None:
                        events.append((abs_tick, slot, msg.note, msg.velocity))
    else:
        # Format 1: search all tracks for channel 10 (index 9)
        for track in mid.tracks:
            abs_tick = 0
            for msg in track:
                abs_tick += msg.time
                if msg.type == 'note_on' and msg.velocity > 0:
                    if msg.channel == 9:
                        slot = GM_DRUM_MAP.get(msg.note)
                        if slot is not None:
                            events.append((abs_tick, slot, msg.note, msg.velocity))

    events.sort(key=lambda e: e[0])
    return events, tpb


def quantize_to_bars(events, tpb):
    """Quantize events into bars of 16 sixteenth-note steps."""
    step_ticks = tpb // 4  # ticks per 16th note
    bar_ticks = tpb * 4     # ticks per bar (4/4 time)

    if not events:
        return []

    # Find total bars
    max_tick = max(e[0] for e in events)
    n_bars = (max_tick // bar_ticks) + 1

    bars = []
    for bar_idx in range(n_bars):
        bar_start = bar_idx * bar_ticks
        grid = {i: [0] * 16 for i in range(8)}

        for tick, slot, note, vel in events:
            if tick < bar_start or tick >= bar_start + bar_ticks:
                continue
            # Quantize to nearest 16th
            rel_tick = tick - bar_start
            step = round(rel_tick / step_ticks)
            step = min(15, max(0, step))
            grid[slot][step] = 1

        bars.append(grid)

    return bars


def bar_density(bar):
    """Count total active steps in a bar."""
    return sum(sum(bar[i]) for i in range(8))


def format_pattern(bar, name="Pattern"):
    """Format a bar as Python dict for the drum machine."""
    lines = []
    lines.append(f'    "{name}": {{')
    for i in range(8):
        steps = bar[i]
        step_str = ",".join(str(s) for s in steps)
        # Insert spaces after every 4 for readability
        parts = [",".join(str(s) for s in steps[j:j+4]) for j in range(0, 16, 4)]
        step_str = ", ".join(parts)
        comment = SLOT_NAMES[i].lower()
        lines.append(f'        {i}: [{step_str}],  # {comment}')
    lines.append('    },')
    return "\n".join(lines)


def print_bar_visual(bar, bar_num):
    """Print a visual grid of a bar."""
    density = bar_density(bar)
    print(f"\n  Bar {bar_num} (density: {density})")
    print(f"  {'':6s} 1 . . . 2 . . . 3 . . . 4 . . .")
    for i in range(8):
        steps = bar[i]
        viz = " ".join("X" if s else "." for s in steps)
        print(f"  {SLOT_NAMES[i]:6s} {viz}")


def detect_bpm(mid):
    """Extract BPM from tempo meta messages."""
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                return round(mido.tempo2bpm(msg.tempo))
    return 120  # default


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 midi_to_pattern.py <file.mid> [--bar N] [--all] [--bpm]")
        sys.exit(1)

    filepath = sys.argv[1]
    show_all = '--all' in sys.argv
    show_bpm = '--bpm' in sys.argv
    target_bar = None
    if '--bar' in sys.argv:
        idx = sys.argv.index('--bar')
        target_bar = int(sys.argv[idx + 1])

    mid = mido.MidiFile(filepath)
    bpm = detect_bpm(mid)

    print(f"\nFile: {filepath}")
    print(f"Format: {mid.type}, Tracks: {len(mid.tracks)}, TPB: {mid.ticks_per_beat}")
    print(f"BPM: {bpm}")

    # List all drum notes found (for debugging mapping)
    events, tpb = extract_drum_events(mid)
    if not events:
        print("\nNo drum events found! This MIDI may not have a drum track on channel 10.")
        # Try to show what channels/notes exist
        for track in mid.tracks:
            for msg in track:
                if msg.type == 'note_on' and msg.velocity > 0:
                    print(f"  Found note_on: ch={msg.channel} note={msg.note}")
                    break
        sys.exit(1)

    notes_found = set(e[2] for e in events)
    mapped = {n: GM_DRUM_MAP.get(n, '?') for n in sorted(notes_found)}
    print(f"Drum notes found: {mapped}")
    print(f"Total events: {len(events)}")

    bars = quantize_to_bars(events, tpb)
    print(f"Total bars: {len(bars)}")

    if show_all:
        for i, bar in enumerate(bars):
            print_bar_visual(bar, i + 1)
        print()

    if target_bar:
        if target_bar < 1 or target_bar > len(bars):
            print(f"Bar {target_bar} out of range (1-{len(bars)})")
            sys.exit(1)
        best = bars[target_bar - 1]
        best_idx = target_bar
    else:
        # Auto-select: find the densest bar that isn't the first (often pickup)
        # and isn't near the end (often outro)
        candidates = bars[1:max(2, len(bars) - 2)] if len(bars) > 4 else bars
        if not candidates:
            candidates = bars
        best_idx = bars.index(max(candidates, key=bar_density)) + 1
        best = bars[best_idx - 1]

    print(f"\n{'='*60}")
    print(f"Selected bar {best_idx}:")
    print_bar_visual(best, best_idx)
    print(f"\nPython pattern dict:")
    print(format_pattern(best, name="Song"))
    print()


if __name__ == "__main__":
    main()
