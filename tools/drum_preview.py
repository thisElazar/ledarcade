"""
Drum Machine Pattern Preview
=============================
Generates WAV files for each drum pattern from the LED arcade drum machine.
Run: python3 drum_preview.py
Plays each pattern and saves WAVs to ~/Desktop/drum_wavs/
"""

import struct
import wave
import os
import math
import random
import subprocess

SAMPLE_RATE = 44100

# ── Drum synthesis ──────────────────────────────────────────────────

def synth_kick(duration=0.15):
    """808-style kick: pitched-down sine sweep."""
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = max(0, 1.0 - t / duration)
        freq = 150 * math.exp(-t * 30) + 40
        s = math.sin(2 * math.pi * freq * t) * env * 0.9
        samples.append(s)
    return samples

def synth_snare(duration=0.12):
    """Snare: short sine body + noise burst."""
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = max(0, 1.0 - t / duration)
        body = math.sin(2 * math.pi * 180 * t) * env * 0.4
        noise = (random.random() * 2 - 1) * env * 0.6
        samples.append(body + noise)
    return samples

def synth_hihat(duration=0.05):
    """Closed hi-hat: short filtered noise."""
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = max(0, 1.0 - t / duration)
        s = (random.random() * 2 - 1) * env * 0.35
        samples.append(s)
    return samples

def synth_open_hat(duration=0.2):
    """Open hi-hat: longer noise with slow decay."""
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = max(0, 1.0 - t / duration) ** 0.5
        s = (random.random() * 2 - 1) * env * 0.3
        samples.append(s)
    return samples

def synth_clap(duration=0.1):
    """Clap: layered noise bursts."""
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = max(0, 1.0 - t / duration)
        # Multiple micro-bursts for clap texture
        micro = 1.0 if (int(t * 800) % 3 == 0) else 0.5
        s = (random.random() * 2 - 1) * env * micro * 0.5
        samples.append(s)
    return samples

def synth_tom(duration=0.15):
    """Tom: pitched sine with decay."""
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = max(0, 1.0 - t / duration)
        freq = 100 * math.exp(-t * 10) + 60
        s = math.sin(2 * math.pi * freq * t) * env * 0.6
        samples.append(s)
    return samples

def synth_rim(duration=0.03):
    """Rimshot: short high click."""
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = max(0, 1.0 - t / duration) ** 2
        s = math.sin(2 * math.pi * 800 * t) * env * 0.4
        samples.append(s)
    return samples

def synth_perc(duration=0.08):
    """Percussion: short metallic ping."""
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = max(0, 1.0 - t / duration)
        s = (math.sin(2 * math.pi * 400 * t) * 0.3 +
             math.sin(2 * math.pi * 653 * t) * 0.2) * env * 0.5
        samples.append(s)
    return samples

SYNTHS = [synth_kick, synth_snare, synth_hihat, synth_open_hat,
          synth_clap, synth_tom, synth_rim, synth_perc]

# ── Patterns (from real MIDI drum tracks) ───────────────────────────

PATTERNS = {
    "Billie Jean": {
        0: [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0],
        1: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
        2: [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0],
        3: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        4: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        5: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        6: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        7: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    },
    "Back In Black": {
        0: [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        1: [0,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0],
        2: [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0],
        3: [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0],
        4: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        5: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        6: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        7: [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    },
    "Superstition": {
        0: [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0],
        1: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
        2: [1,0,1,0, 1,1,1,0, 1,0,1,1, 1,0,1,0],
        3: [0,0,0,0, 0,0,0,0, 0,0,0,1, 0,0,0,0],
        4: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
        5: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        6: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        7: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    },
    "Levee Breaks": {
        0: [1,0,0,0, 0,0,0,1, 0,0,1,1, 0,0,0,0],
        1: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
        2: [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0],
        3: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        4: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        5: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        6: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        7: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    },
    "Bite The Dust": {
        0: [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0],
        1: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
        2: [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0],
        3: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        4: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        5: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        6: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        7: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    },
    "Rick Roll": {
        0: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        1: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        2: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        3: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        4: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        5: [0,0,0,0, 0,0,1,1, 0,1,1,1, 1,1,1,1],
        6: [1,0,0,0, 1,0,0,0, 0,0,0,0, 0,0,0,0],
        7: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    },
    "In The Air": {
        0: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,1,0,1],
        1: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        2: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        3: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        4: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        5: [1,1,0,1, 1,0,0,1, 1,0,1,1, 0,1,0,1],
        6: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        7: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    },
    "Sex Machine": {
        0: [1,0,0,0, 0,0,0,0, 0,1,1,0, 0,0,1,0],
        1: [0,0,0,0, 1,0,1,1, 1,1,1,0, 1,0,0,1],
        2: [1,0,1,0, 0,0,1,1, 1,0,1,0, 0,0,1,1],
        3: [0,0,0,0, 1,0,0,0, 0,1,0,0, 1,0,0,0],
        4: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        5: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        6: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        7: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    },
    "Feel Good": {
        0: [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0],
        1: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
        2: [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0],
        3: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        4: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        5: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        6: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
        7: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    },
    "Gimme Shelter": {
        0: [1,0,1,0, 0,0,0,0, 1,0,1,0, 0,0,0,0],
        1: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
        2: [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0],
        3: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        4: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        5: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        6: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        7: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    },
    "Blitzkrieg Bop": {
        0: [1,0,1,0, 0,0,0,0, 1,0,1,0, 0,0,0,0],
        1: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
        2: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        3: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        4: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        5: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        6: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        7: [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0],
    },
    "Be Sedated": {
        0: [1,0,0,0, 0,0,0,0, 1,0,1,0, 0,0,0,0],
        1: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
        2: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        3: [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0],
        4: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        5: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        6: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        7: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    },
    "Puppets": {
        0: [1,0,1,0, 0,0,1,0, 1,0,1,0, 0,0,0,0],
        1: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
        2: [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0],
        3: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        4: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        5: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        6: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        7: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
    },
    "Enter Sandman": {
        0: [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0],
        1: [0,0,0,0, 0,0,0,0, 0,0,1,0, 0,0,1,0],
        2: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        3: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        4: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        5: [1,0,1,0, 1,0,1,0, 1,0,0,0, 0,0,0,0],
        6: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        7: [0,0,0,0, 0,0,0,0, 0,0,1,0, 0,0,1,0],
    },
    "Sandstorm": {
        0: [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0],
        1: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        2: [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0],
        3: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        4: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
        5: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        6: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0],
        7: [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0],
    },
}

PATTERN_BPM = {
    "Billie Jean": 117,
    "Back In Black": 95,
    "Superstition": 101,
    "Levee Breaks": 100,
    "Bite The Dust": 115,
    "Rick Roll": 114,
    "In The Air": 116,
    "Sex Machine": 110,
    "Feel Good": 145,
    "Gimme Shelter": 117,
    "Blitzkrieg Bop": 190,
    "Be Sedated": 165,
    "Puppets": 220,
    "Enter Sandman": 123,
    "Sandstorm": 136,
}

# ── WAV rendering ───────────────────────────────────────────────────

def render_pattern(name, pattern, bpm=120, loops=2):
    """Render a pattern to a list of float samples."""
    step_dur = 60.0 / (bpm * 4)  # seconds per 16th note
    total_steps = 16 * loops
    total_samples = int(total_steps * step_dur * SAMPLE_RATE)
    buf = [0.0] * total_samples

    for loop in range(loops):
        for step in range(16):
            offset = int((loop * 16 + step) * step_dur * SAMPLE_RATE)
            for inst in range(8):
                if pattern.get(inst, [0]*16)[step]:
                    sound = SYNTHS[inst]()
                    for i, s in enumerate(sound):
                        idx = offset + i
                        if idx < total_samples:
                            buf[idx] += s

    # Normalize
    peak = max(abs(s) for s in buf) or 1.0
    buf = [s / peak * 0.85 for s in buf]
    return buf

def save_wav(filename, samples):
    """Save float samples as 16-bit WAV."""
    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        data = b''
        for s in samples:
            val = max(-32767, min(32767, int(s * 32767)))
            data += struct.pack('<h', val)
        wf.writeframes(data)

# ── Main ────────────────────────────────────────────────────────────

def main():
    out_dir = os.path.expanduser("~/Desktop/drum_wavs")
    os.makedirs(out_dir, exist_ok=True)

    for name, pattern in PATTERNS.items():
        bpm = PATTERN_BPM.get(name, 120)
        print(f"Rendering {name} ({bpm} BPM)...")
        samples = render_pattern(name, pattern, bpm=bpm, loops=4)
        fname = name.lower().replace(" ", "_")
        path = os.path.join(out_dir, f"{fname}.wav")
        save_wav(path, samples)
        print(f"  Saved: {path}")

    print(f"\nAll {len(PATTERNS)} patterns saved to {out_dir}/")
    print("Play any with: afplay ~/Desktop/drum_wavs/<name>.wav")

if __name__ == "__main__":
    main()
