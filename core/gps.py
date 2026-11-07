"""
Módulo de lectura y sincronización GPS NMEA para eclipZe.
Diseñado para el dongle USB u-blox VK-162 (o cualquier receptor NMEA serie estándar).
Calcula la diferencia de reloj (delta) entre la hora atómica UTC satelital y el reloj local del PC.
"""

import time
import datetime
import threading
from typing import Optional, Callable


class GPSData:
    """Estructura de telemetría GPS."""
    def __init__(self):
        self.connected: bool = False
        self.has_fix: bool = False
        self.latitude: float = 0.0
        self.longitude: float = 0.0
        self.altitude_m: float = 0.0
        self.satellites: int = 0
        self.utc_time: Optional[datetime.datetime] = None
        self.clock_offset_seconds: float = 0.0  # (GPS_UTC - Local_Clock)

    @property
    def altitude(self) -> float:
        return self.altitude_m


class GPSReader:
    """Lector de sentencias NMEA (GPRMC, GPGGA) para el dongle VK-162."""

    def __init__(self, port: str = "COM3", baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.data = GPSData()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.on_update_callback: Optional[Callable[[GPSData], None]] = None

    def start(self):
        """Inicia el hilo lector serie si pyserial está disponible."""
        self._running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def _read_loop(self):
        try:
            import serial
        except ImportError:
            print("[GPS Info] 'pyserial' no instalado. Para conectar el dongle VK-162 ejecuta: pip install pyserial")
            return

        while self._running:
            try:
                with serial.Serial(self.port, self.baudrate, timeout=1.5) as ser:
                    self.data.connected = True
                    while self._running:
                        raw_line = ser.readline().decode("ascii", errors="replace").strip()
                        if raw_line:
                            self._parse_nmea_line(raw_line)
                            if self.on_update_callback:
                                self.on_update_callback(self.data)
            except Exception as e:
                self.data.connected = False
                self.data.has_fix = False
                # shortcut: reconexión fija cada 3s, suficiente para caídas de USB
                time.sleep(3.0)

    def _parse_nmea_line(self, line: str):
        parts = line.split(",")
        header = parts[0]

        # RMC: Hora UTC, estado del fix, coordenadas y fecha
        # $GPRMC o $GNRMC
        if header.endswith("RMC") and len(parts) >= 10:
            status = parts[2]
            if status == "A":  # 'A' = Fix válido satelital
                self.data.has_fix = True
                raw_time = parts[1]
                raw_date = parts[9]
                if len(raw_time) >= 6 and len(raw_date) == 6:
                    try:
                        hh = int(raw_time[0:2])
                        mm = int(raw_time[2:4])
                        ss = int(raw_time[4:6])
                        ms = int(float("0." + raw_time.split(".")[1]) * 1_000_000) if "." in raw_time else 0
                        day = int(raw_date[0:2])
                        month = int(raw_date[2:4])
                        year = 2000 + int(raw_date[4:6])

                        gps_dt = datetime.datetime(year, month, day, hh, mm, ss, ms, tzinfo=datetime.timezone.utc)
                        self.data.utc_time = gps_dt
                        
                        # Cálculo del desfase respecto al reloj del sistema
                        now_utc = datetime.datetime.now(datetime.timezone.utc)
                        self.data.clock_offset_seconds = (gps_dt - now_utc).total_seconds()
                    except ValueError:
                        pass

                # Parsear latitud y longitud
                if parts[3] and parts[4] and parts[5] and parts[6]:
                    self.data.latitude = self._convert_nmea_coord(parts[3], parts[4])
                    self.data.longitude = self._convert_nmea_coord(parts[5], parts[6])
            else:
                self.data.has_fix = False

        # GGA: Altitud y satélites
        elif header.endswith("GGA") and len(parts) >= 10:
            try:
                if parts[7]:
                    self.data.satellites = int(parts[7])
                if parts[9]:
                    self.data.altitude_m = float(parts[9])
            except ValueError:
                pass

    @staticmethod
    def _convert_nmea_coord(value: str, direction: str) -> float:
        """Convierte coordenadas NMEA (ddmm.mmmm) a grados decimales."""
        try:
            dot_idx = value.find(".")
            if dot_idx < 2:
                return 0.0
            deg = float(value[:dot_idx - 2])
            mins = float(value[dot_idx - 2:])
            decimal = deg + (mins / 60.0)
            if direction in ["S", "W"]:
                decimal = -decimal
            return decimal
        except Exception:
            return 0.0
