"""
SysInfo - System Information Display
====================================
Shows Raspberry Pi system stats: CPU temp, IP address, uptime, memory usage.

Controls:
  Space/Action - Refresh stats immediately
  Up/Down - Reserved for scrolling (future use)
  Escape - Exit
"""

import socket
import time as time_module
from . import Visual, Display, Colors, GRID_SIZE


class SysInfo(Visual):
    name = "SYSINFO"
    description = "System info"
    category = "utility"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.last_refresh = 0.0
        self.refresh_interval = 2.5  # Seconds between auto-refresh
        self.cpu_temp = "N/A"
        self.ip_address = "N/A"
        self.uptime_str = "N/A"
        self.mem_percent = "N/A"
        self._refresh_stats()

    def _read_cpu_temp(self) -> str:
        """Read CPU temperature from thermal zone."""
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp_millicelsius = int(f.read().strip())
                temp_celsius = temp_millicelsius // 1000
                return f"{temp_celsius}C"
        except (FileNotFoundError, IOError, ValueError):
            return "N/A"

    def _read_ip_address(self) -> str:
        """Get the device's IP address."""
        try:
            # Try to get IP by connecting to an external address (doesn't actually connect)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.1)
            try:
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
                return ip
            except Exception:
                s.close()
                pass

            # Fallback to hostname resolution
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            if ip and ip != "127.0.0.1":
                return ip
            return "N/A"
        except Exception:
            return "N/A"

    def _read_uptime(self) -> str:
        """Read system uptime from /proc/uptime."""
        try:
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.read().split()[0])

                days = int(uptime_seconds // 86400)
                hours = int((uptime_seconds % 86400) // 3600)
                minutes = int((uptime_seconds % 3600) // 60)

                if days > 0:
                    return f"{days}d {hours}h"
                elif hours > 0:
                    return f"{hours}h {minutes}m"
                else:
                    return f"{minutes}m"
        except (FileNotFoundError, IOError, ValueError):
            return "N/A"

    def _read_memory(self) -> str:
        """Read memory usage from /proc/meminfo."""
        try:
            meminfo = {}
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        key = parts[0].rstrip(":")
                        value = int(parts[1])
                        meminfo[key] = value

            mem_total = meminfo.get("MemTotal", 0)
            mem_available = meminfo.get("MemAvailable", 0)

            if mem_total > 0:
                mem_used = mem_total - mem_available
                percent = int((mem_used / mem_total) * 100)
                return f"{percent}%"
            return "N/A"
        except (FileNotFoundError, IOError, ValueError, KeyError):
            return "N/A"

    def _refresh_stats(self):
        """Refresh all system stats."""
        self.cpu_temp = self._read_cpu_temp()
        self.ip_address = self._read_ip_address()
        self.uptime_str = self._read_uptime()
        self.mem_percent = self._read_memory()
        self.last_refresh = self.time

    def handle_input(self, input_state) -> bool:
        if input_state.action:
            self._refresh_stats()
            return True
        return False

    def update(self, dt: float):
        self.time += dt

        # Auto-refresh stats periodically
        if self.time - self.last_refresh >= self.refresh_interval:
            self._refresh_stats()

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Title
        self.display.draw_text_small(2, 2, "SYSTEM INFO", Colors.CYAN)

        # Separator line
        self.display.draw_line(2, 9, 61, 9, Colors.GRAY)

        # CPU Temperature
        self.display.draw_text_small(2, 14, "TEMP:", Colors.WHITE)
        temp_color = Colors.GREEN
        if self.cpu_temp != "N/A":
            try:
                temp_val = int(self.cpu_temp.rstrip("C"))
                if temp_val >= 70:
                    temp_color = Colors.RED
                elif temp_val >= 55:
                    temp_color = Colors.YELLOW
            except ValueError:
                pass
        self.display.draw_text_small(27, 14, self.cpu_temp, temp_color)

        # IP Address
        self.display.draw_text_small(2, 23, "IP:", Colors.WHITE)
        self.display.draw_text_small(17, 23, self.ip_address, Colors.GREEN)

        # Uptime
        self.display.draw_text_small(2, 32, "UP:", Colors.WHITE)
        self.display.draw_text_small(17, 32, self.uptime_str, Colors.GREEN)

        # Memory usage
        self.display.draw_text_small(2, 41, "MEM:", Colors.WHITE)
        mem_color = Colors.GREEN
        if self.mem_percent != "N/A":
            try:
                mem_val = int(self.mem_percent.rstrip("%"))
                if mem_val >= 90:
                    mem_color = Colors.RED
                elif mem_val >= 70:
                    mem_color = Colors.YELLOW
            except ValueError:
                pass
        self.display.draw_text_small(22, 41, self.mem_percent, mem_color)

        # Refresh indicator (small dot that blinks)
        if int(self.time * 2) % 2 == 0:
            self.display.set_pixel(60, 2, Colors.GREEN)
