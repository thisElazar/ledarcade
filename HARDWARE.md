# Hardware Setup Guide

This document covers the physical hardware build for the LED Arcade system, including wiring, Pi setup, and deployment strategy.

---

## Hardware Overview

### Target Configuration
- **Display:** 64x64 RGB LED Matrix (HUB75 interface)
- **Power:** 5V 4A power supply (dedicated to panel)
- **Controller:** Raspberry Pi (Pi 3 for prototyping, Pi Zero 2 W for deployment)
- **Input:** 1 joystick (4 directions) + 3 buttons
- **Audio:** USB audio adapter (optional, for 8-bit sound effects)

### Why Two Pi Models?

| Aspect | Pi 3B | Pi Zero 2 W |
|--------|-------|-------------|
| CPU | 1.4 GHz quad-core | 1.0 GHz quad-core |
| RAM | 1 GB | 512 MB |
| Size | 85×56mm | 65×30mm |
| Power draw | ~3-5W under load | ~1-2W under load |
| Role | Development & benchmarking | Final deployment |

The Pi 3 serves as the prototyping platform. Once everything works, we validate performance on the Zero 2 W before committing to the final enclosure build.

---

## GPIO Pin Mapping

### HUB75 Panel Connection

No HAT is used. Female-to-female Dupont jumpers connect the panel's HUB75 input header directly to the Pi's GPIO.

**Two options:**
1. **Standard wiring** (recommended for new builds) - matches library's "regular" mapping, no patches needed
2. **Custom wiring** (current prototype) - requires custom library mapping

---

### Option 1: Standard Wiring (Recommended)

Use the `rpi-rgb-led-matrix` library's built-in "regular" hardware mapping. No library modifications needed.

| HUB75 Pin | Function | Pi GPIO | Physical Pin |
|-----------|----------|---------|--------------|
| R1 | Red (upper half) | GPIO 11 | Pin 23 |
| G1 | Green (upper half) | GPIO 27 | Pin 13 |
| B1 | Blue (upper half) | GPIO 7 | Pin 26 |
| R2 | Red (lower half) | GPIO 8 | Pin 24 |
| G2 | Green (lower half) | GPIO 9 | Pin 21 |
| B2 | Blue (lower half) | GPIO 10 | Pin 19 |
| A | Row select bit 0 | GPIO 22 | Pin 15 |
| B | Row select bit 1 | GPIO 23 | Pin 16 |
| C | Row select bit 2 | GPIO 24 | Pin 18 |
| D | Row select bit 3 | GPIO 25 | Pin 22 |
| E | Row select bit 4 (64x64) | GPIO 15 | Pin 10 |
| CLK | Clock | GPIO 17 | Pin 11 |
| LAT | Latch | GPIO 4 | Pin 7 |
| OE | Output enable | GPIO 18 | Pin 12 |
| GND | Ground | GND | Pin 6, 9, 14, 20, 25, 30, 34, 39 |

In `hardware.py`, use: `options.hardware_mapping = 'regular'`

---

### Option 2: Custom Wiring (Current Prototype)

The prototype uses a custom "led-arcade" mapping. Requires patching the library (see below).

| HUB75 Pin | Function | Pi GPIO | Physical Pin |
|-----------|----------|---------|--------------|
| R1 | Red (upper half) | GPIO 5 | Pin 29 |
| G1 | Green (upper half) | GPIO 13 | Pin 33 |
| B1 | Blue (upper half) | GPIO 6 | Pin 31 |
| R2 | Red (lower half) | GPIO 12 | Pin 32 |
| G2 | Green (lower half) | GPIO 16 | Pin 36 |
| B2 | Blue (lower half) | GPIO 23 | Pin 16 |
| A | Row select bit 0 | GPIO 22 | Pin 15 |
| B | Row select bit 1 | GPIO 26 | Pin 37 |
| C | Row select bit 2 | GPIO 27 | Pin 13 |
| D | Row select bit 3 | GPIO 20 | Pin 38 |
| E | Row select bit 4 (64x64) | GPIO 21 | Pin 40 |
| CLK | Clock | GPIO 17 | Pin 11 |
| LAT | Latch | GPIO 4 | Pin 7 |
| OE | Output enable | GPIO 18 | Pin 12 |
| GND | Ground | GND | Pin 6, 9, 14, 20, 25, 30, 34, 39 |

In `hardware.py`, use: `options.hardware_mapping = 'led-arcade'`

**To add the custom mapping to the library:**

1. Edit `~/rpi-rgb-led-matrix/lib/hardware-mapping.c`
2. Add after the "regular" mapping block:

```c
  {
    .name          = "led-arcade",
    .output_enable = GPIO_BIT(18),
    .clock         = GPIO_BIT(17),
    .strobe        = GPIO_BIT(4),
    .a             = GPIO_BIT(22),
    .b             = GPIO_BIT(26),
    .c             = GPIO_BIT(27),
    .d             = GPIO_BIT(20),
    .e             = GPIO_BIT(21),
    .p0_r1         = GPIO_BIT(5),
    .p0_g1         = GPIO_BIT(13),
    .p0_b1         = GPIO_BIT(6),
    .p0_r2         = GPIO_BIT(12),
    .p0_g2         = GPIO_BIT(16),
    .p0_b2         = GPIO_BIT(23),
  },
```

3. Rebuild: `cd ~/rpi-rgb-led-matrix && make clean && make`
4. Rebuild Python bindings: `cd bindings/python && make build-python && sudo make install-python`

---

**Note:** The E pin is required for 64x64 panels (32-row addressing needs 5 address bits).

### Joystick + Buttons

Active-low configuration: buttons connect GPIO to GND when pressed. Internal pull-ups enabled in software.

| Input | Function | Pi GPIO | Physical Pin |
|-------|----------|---------|--------------|
| UP | Joystick up | GPIO 19 | Pin 35 |
| DOWN | Joystick down | GPIO 25 | Pin 22 |
| LEFT | Joystick left | GPIO 24 | Pin 18 |
| RIGHT | Joystick right | GPIO 8 | Pin 24 |
| BTN_A | Action (Space) | GPIO 7 | Pin 26 |
| BTN_B | Secondary (Z) | GPIO 9 | Pin 21 |
| BTN_C | Back (Escape) | GPIO 11 | Pin 23 |
| GND | Common ground | GND | Any GND pin |

### Power Connections

The LED panel requires separate power from its own supply:

- **Panel power:** 5V 4A supply connects directly to panel's power terminals
- **Pi power:** Standard USB power (separate from panel supply)
- **Common ground:** Panel GND and Pi GND must be connected

**Important:** Do not attempt to power the panel from the Pi's 5V pin. The panel can draw 2-4A at full white brightness, which would damage the Pi.

---

## Pi 3 Setup (Prototyping Platform)

### Initial OS Setup

1. Flash **Raspberry Pi OS Lite (64-bit)** to SD card using Raspberry Pi Imager
2. In Imager's settings (gear icon), configure:
   - Hostname: `ledarcade`
   - Enable SSH (password authentication)
   - Set username/password
   - Configure WiFi (SSID and password)
   - Set locale/timezone
3. Insert SD card, boot Pi, wait ~90 seconds for first boot

### SSH Connection

From your laptop:
```bash
ssh username@ledarcade.local
```

If `.local` doesn't resolve, find the IP from your router or use:
```bash
ping ledarcade.local
```

### System Configuration

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y git python3-pip python3-dev cython3

# Disable onboard audio (conflicts with LED matrix timing)
# Method 1: Edit config
sudo sed -i 's/^dtparam=audio=on/dtparam=audio=off/' /boot/firmware/config.txt

# Method 2: Blacklist the module (belt and suspenders)
echo 'blacklist snd_bcm2835' | sudo tee /etc/modprobe.d/blacklist-sound.conf

# Reboot to apply
sudo reboot
```

### Install LED Matrix Library

```bash
# Clone the rpi-rgb-led-matrix library
cd ~
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git

# Build the library
cd rpi-rgb-led-matrix
make -j4

# Build Python bindings
cd bindings/python
make build-python PYTHON=$(which python3)
sudo make install-python PYTHON=$(which python3)
```

### Clone and Run LED Arcade

```bash
# Clone the project
git clone https://github.com/thisElazar/ledarcade.git ~/led-arcade

# Run on hardware
cd ~/led-arcade
sudo python3 run_hardware.py
```

**Controls (keyboard):**
- Arrow keys / WASD - Navigate
- Space - Select / Action
- Q - Back / Exit

### Transfer Project Files

From your laptop:
```bash
# Copy the led-arcade folder to Pi
scp -r /path/to/led-arcade username@ledarcade.local:~/
```

Or use rsync for subsequent updates:
```bash
rsync -avz --progress /path/to/led-arcade/ username@ledarcade.local:~/led-arcade/
```

### Install Python Dependencies

On the Pi:
```bash
cd ~/led-arcade
pip3 install -r requirements.txt --break-system-packages
```

**Note:** PyGame is only needed for desktop emulation. The hardware version will use the LED matrix library directly.

---

## Performance Considerations

### Heavy Visuals

These automata have the highest computational load and may need tuning on Pi Zero 2 W:

| Visual | Current Load | Bottleneck |
|--------|--------------|------------|
| Boids | 80 agents | O(N²) neighbor search |
| Flux | 150 curves | O(N²) separation checks + curl noise |
| Attractors | 75 particles | Runge-Kutta integration + trail sorting |
| Slime | 4,096 cells | Grid simulation + colony competition |
| Hodge | 4,096 cells | 9-neighbor checks per cell |

### Benchmarking Strategy

1. Run each heavy visual on Pi 3, measure actual FPS
2. Repeat on Pi Zero 2 W
3. If Zero 2 W drops below 25 FPS, reduce agent/particle counts
4. Document final tuned values for deployment

### LED Matrix Performance Flags

The `rpi-rgb-led-matrix` library accepts flags that affect performance:

```bash
# Example invocation with common flags
sudo python3 arcade_hardware.py \
  --led-rows=64 \
  --led-cols=64 \
  --led-gpio-mapping=regular \
  --led-slowdown-gpio=2
```

Key flags:
- `--led-slowdown-gpio`: Increase if you see flickering (try 1-4)
- `--led-pwm-bits`: Lower for faster refresh, higher for color depth (default 11)
- `--led-brightness`: Reduce to lower power consumption

---

## Audio Setup (Optional)

The LED matrix library uses PWM hardware that conflicts with the Pi's onboard audio. Use a USB audio adapter instead.

```bash
# Plug in USB audio adapter, then check it's detected
aplay -l

# Install audio tools
sudo apt install -y alsa-utils

# Test audio
speaker-test -t wav -c 2
```

For 8-bit sound effects, the `pygame.mixer` module works with USB audio, or use `aplay` for simple WAV playback.

---

## Wiring Checklist

Before first power-on:

- [ ] Panel power supply connected to panel (not Pi)
- [ ] Pi powered separately via USB
- [ ] Panel GND connected to Pi GND
- [ ] All 14 HUB75 signal wires connected (R1, G1, B1, R2, G2, B2, A, B, C, D, E, CLK, LAT, OE)
- [ ] Joystick 4 directions wired to GPIO 19, 25, 24, 8
- [ ] 3 buttons wired to GPIO 7, 9, 11
- [ ] All button/joystick commons connected to GND
- [ ] Double-check no shorts between adjacent pins

---

## Troubleshooting

### No display output
- Verify all 14 signal wires are connected
- Check panel power supply is on
- Ensure GND is shared between Pi and panel
- Try `--led-slowdown-gpio=4` (some panels need slower timing)

### Flickering or sparkles
- Increase `--led-slowdown-gpio` value
- Check for loose Dupont connections
- Some panels are sensitive to 3.3V logic levels (may need level shifter)

### Wrong colors
- Verify R1/G1/B1 and R2/G2/B2 wiring order
- Check that you're using the INPUT connector on the panel (not OUTPUT)

### Buttons not responding
- Verify internal pull-ups are enabled in code
- Test with multimeter: button press should short GPIO to GND
- Check common ground connection

---

## Deployment Transition (Pi 3 → Zero 2 W)

Once benchmarking confirms acceptable performance:

1. Flash fresh Raspberry Pi OS Lite to new SD card
2. Repeat setup steps (SSH, packages, library build)
3. Transfer tuned project files
4. Move Dupont jumper bundle from Pi 3 to Zero 2 W (same pinout)
5. Verify operation before permanent installation

The Zero 2 W uses the same 40-pin GPIO header as the Pi 3, so all wiring transfers directly.

---

## Future Enhancements

- [ ] Hardware driver layer (`display_hardware.py`)
- [ ] GPIO input handler (`input_hardware.py`)
- [ ] Auto-start on boot (systemd service)
- [ ] Gamma correction LUT for LED color accuracy
- [ ] Enclosure design and mounting
