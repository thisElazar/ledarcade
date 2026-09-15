"""
USB Share - Swap art on a USB stick
===================================
Copies your PAINT pictures, PAINT GIF projects and exported GIFs onto a USB
stick, or brings them in from one. Anything already there (same contents,
whatever its name) is skipped, so sending and getting back never duplicates.

Controls:
  Up/Down    - Select SEND/GET
  Button     - Confirm selection
  Left/Right - Back to menu
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
from . import Visual, Display, Colors

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
STICK_FOLDER = "WONDER_CABINET"
MOUNT_POINT = "/mnt/wonder-usb"
USB_FSTYPES = {"vfat", "exfat", "ntfs", "ext4"}

# Which art lives in which data/ subfolder (projects are proj_* dirs in paint_gif)
ART_DIRS = {"paint": ".png", "paint_gif": ".gif"}

# A stick can hold anything — keep imports small enough for the Pi to play
MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_DIM = 256
MAX_FRAMES = 200


# ── Copy / de-duplicate (pure file work, no mounting) ─────────────────

def _valid_image(path, ext):
    """True if path is a fully decodable PNG/GIF within the size limits."""
    try:
        if os.path.getsize(path) > MAX_FILE_BYTES:
            return False
        with Image.open(path) as img:
            if img.format != ext[1:].upper():
                return False
            if img.size[0] > MAX_DIM or img.size[1] > MAX_DIM:
                return False
            n = getattr(img, "n_frames", 1)
            if n > MAX_FRAMES:
                return False
            for i in range(n):
                img.seek(i)
                img.load()
        return True
    except Exception:
        return False


def _project_frames(proj_dir):
    return sorted(f for f in os.listdir(proj_dir)
                  if f.endswith(".png") and not f.startswith("."))


def _digest(path):
    """Content hash of an art file, or of a project folder's frames."""
    h = hashlib.sha256()
    if os.path.isdir(path):
        # Frame contents only (not names), so a renamed copy still matches
        for f in _project_frames(path):
            with open(os.path.join(path, f), "rb") as fh:
                h.update(fh.read())
    else:
        with open(path, "rb") as fh:
            h.update(fh.read())
    return h.hexdigest()


def _art_entries(directory, ext):
    """(name, path, is_project) for each art item in a data/ subfolder."""
    if not os.path.isdir(directory):
        return []
    items = []
    for name in sorted(os.listdir(directory)):
        path = os.path.join(directory, name)
        if name.startswith(".") or os.path.islink(path):
            continue
        if os.path.isdir(path):
            if ext == ".gif" and name.startswith("proj_"):
                items.append((name, path, True))
        elif name.lower().endswith(ext):
            items.append((name, path, False))
    return items


def _free_name(directory, name):
    """name if unused in directory, else the next numbered variant."""
    if not os.path.exists(os.path.join(directory, name)):
        return name
    stem, ext = os.path.splitext(name)
    m = re.match(r"(.*_)(\d+)$", stem)
    base, n = (m.group(1), int(m.group(2))) if m else (stem + "-", 1)
    while True:
        n += 1
        candidate = f"{base}{n:03d}{ext}" if m else f"{base}{n}{ext}"
        if not os.path.exists(os.path.join(directory, candidate)):
            return candidate


def _clean_name(name, ext):
    """Filesystem- and menu-safe version of a name from a stick."""
    stem = os.path.splitext(name)[0] if ext else name
    stem = re.sub(r"[^A-Za-z0-9_-]+", "-", stem).strip("-")[:24] or "art"
    return stem + ext


def merge(src_root, dst_root):
    """Copy art from src_root into dst_root, skipping anything whose contents
    dst_root already has. Works in both directions (cabinet <-> stick).
    Returns counts: copied, skipped (already there), bad (unreadable/too big).
    """
    counts = {"copied": 0, "skipped": 0, "bad": 0}
    for sub, ext in ART_DIRS.items():
        entries = _art_entries(os.path.join(src_root, sub), ext)
        if not entries:
            continue
        dst = os.path.join(dst_root, sub)
        os.makedirs(dst, exist_ok=True)
        have = {_digest(p) for _, p, _ in _art_entries(dst, ext)}

        for name, path, is_project in entries:
            if is_project:
                frames = _project_frames(path)
                ok = 0 < len(frames) <= MAX_FRAMES and all(
                    _valid_image(os.path.join(path, f), ".png") for f in frames)
            else:
                ok = _valid_image(path, ext)
            if not ok:
                counts["bad"] += 1
                continue

            digest = _digest(path)
            if digest in have:
                counts["skipped"] += 1
                continue

            # Copy under a hidden temp name, then rename into place, so a
            # yanked stick or power cut never leaves a half-copied piece.
            if is_project:
                final = _free_name(dst, _clean_name(name, ""))
                tmp = os.path.join(dst, ".tmp-" + final)
                shutil.rmtree(tmp, ignore_errors=True)
                os.makedirs(tmp)
                for f in frames:
                    shutil.copyfile(os.path.join(path, f), os.path.join(tmp, _clean_name(f, ".png")))
            else:
                final = _free_name(dst, _clean_name(name, ext))
                tmp = os.path.join(dst, ".tmp-" + final + ".part")
                shutil.copyfile(path, tmp)
            os.rename(tmp, os.path.join(dst, final))
            have.add(digest)
            counts["copied"] += 1
    return counts


# ── USB stick detection / mounting (cabinet runs as root) ─────────────

def _find_usb():
    """(device, existing mountpoint or None) for the first USB partition."""
    try:
        out = subprocess.run(
            ["lsblk", "-J", "-p", "-o", "NAME,TRAN,FSTYPE,MOUNTPOINT"],
            capture_output=True, text=True, timeout=5).stdout
        disks = json.loads(out)["blockdevices"]
    except Exception:
        return None, None
    for disk in disks:
        if disk.get("tran") != "usb":
            continue
        for part in disk.get("children") or [disk]:
            if part.get("fstype") in USB_FSTYPES:
                return part["name"], part.get("mountpoint")
    return None, None


def transfer(direction):
    """Mount the stick, send ('send') or get ('get') art, unmount.
    Returns (ok, counts dict or error message)."""
    if not HAS_PIL:
        return False, "NO PIL"
    device, mounted_at = _find_usb()
    if not device:
        return False, "NO USB"

    root = mounted_at
    if not root:
        os.makedirs(MOUNT_POINT, exist_ok=True)
        r = subprocess.run(["mount", "-o", "noexec,nosuid,nodev", device, MOUNT_POINT],
                           capture_output=True, timeout=20)
        if r.returncode != 0:
            return False, "CANT READ"
        root = MOUNT_POINT

    stick = os.path.join(root, STICK_FOLDER)
    try:
        if direction == "send":
            result = (True, merge(DATA_DIR, stick))
        elif os.path.isdir(stick):
            result = (True, merge(stick, DATA_DIR))
        else:
            result = (False, "NO ART")
    except OSError:
        result = (False, "COPY FAIL")

    subprocess.run(["sync"], timeout=60)
    if not mounted_at:
        if subprocess.run(["umount", MOUNT_POINT], capture_output=True, timeout=30).returncode != 0:
            return False, "STILL BUSY"
    return result


# ── Menu app ──────────────────────────────────────────────────────────

class UsbShare(Visual):
    name = "USB SHARE"
    description = "Swap art on a USB stick"
    category = "utility"
    GUIDE = {
        'desc': 'Copy your PAINT and PAINT GIF creations onto a USB stick, or bring in art from another cabinet. Nothing gets duplicated, and the stick is safe to pull out as soon as it says so.',
    }

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.selection = 0  # 0 = SEND, 1 = GET
        self.busy = False
        self.result = None  # (ok, counts or message) once a transfer finishes

    def _run(self, direction):
        self.result = transfer(direction)
        self.busy = False

    def handle_input(self, input_state) -> bool:
        if self.busy:
            return True

        pressed = input_state.action_l or input_state.action_r
        if self.result is not None:
            if pressed:
                self.result = None
            return True

        if input_state.up_pressed or input_state.down_pressed:
            self.selection = 1 - self.selection
            return True

        if input_state.left_pressed or input_state.right_pressed:
            self.wants_exit = True
            return True

        if pressed:
            self.busy = True
            direction = "send" if self.selection == 0 else "get"
            threading.Thread(target=self._run, args=(direction,), daemon=True).start()
            return True

        return False

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)
        d.draw_text_small(2, 2, "USB SHARE", Colors.CYAN)
        d.draw_line(2, 9, 61, 9, Colors.GRAY)

        if self.busy:
            d.draw_text_small(2, 20, "SENDING" if self.selection == 0 else "GETTING", Colors.YELLOW)
            d.draw_text_small(2, 28, "." * (int(self.time * 3) % 4), Colors.YELLOW)
            d.draw_text_small(2, 46, "DONT UNPLUG", Colors.RED)
            return

        if self.result is not None:
            ok, info = self.result
            if ok:
                verb = "SENT" if self.selection == 0 else "GOT"
                d.draw_text_small(2, 14, f"{verb} {info['copied']}", Colors.GREEN)
                d.draw_text_small(2, 22, f"ALREADY {info['skipped']}", Colors.GRAY)
                if info["bad"]:
                    d.draw_text_small(2, 30, f"BAD {info['bad']}", Colors.ORANGE)
                d.draw_text_small(2, 40, "SAFE TO", Colors.WHITE)
                d.draw_text_small(2, 47, "UNPLUG", Colors.WHITE)
            else:
                d.draw_text_small(2, 20, info, Colors.RED)
            d.draw_text_small(2, 56, "BTN:OK", Colors.GRAY)
            return

        send_color = Colors.YELLOW if self.selection == 0 else Colors.GRAY
        get_color = Colors.YELLOW if self.selection == 1 else Colors.GRAY
        d.draw_text_small(2, 18 if self.selection == 0 else 28, ">", Colors.YELLOW)
        d.draw_text_small(9, 18, "SEND TO USB", send_color)
        d.draw_text_small(9, 28, "GET FROM USB", get_color)
        d.draw_text_small(2, 46, "PLUG IN STICK", Colors.GRAY)
        d.draw_text_small(2, 54, "BTN:GO", Colors.GRAY)
