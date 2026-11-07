"""
Driver de cámara para eclipZe.
Soporta simulación (Mock) para pruebas y gphoto2 para Nikon Z5 II / D750 en hardware real.
"""

import os
import re
import time
import datetime
import subprocess
import threading
import queue
from abc import ABC, abstractmethod
from typing import List, Optional, Callable


def parse_ptp_datetime(s: str) -> Optional[datetime.datetime]:
    """Parsea una cadena PTP DateTime (ISO 8601 compacto: YYYYMMDDTHHMMSS[.s][Z|+-HHMM])."""
    if not s:
        return None
    pattern = r"^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})(?:\.(\d+))?([+-]\d{2,4}|Z)?"
    m = re.match(pattern, s.strip())
    if not m:
        return None
    year, month, day, hour, minute, second = map(int, m.groups()[:6])
    fraction_str = m.group(7)
    microsecond = 0
    if fraction_str:
        microsecond = int(fraction_str.ljust(6, "0")[:6])
    tz = None
    tz_str = m.group(8)
    if tz_str:
        if tz_str == "Z":
            tz = datetime.timezone.utc
        else:
            sign = 1 if tz_str[0] == "+" else -1
            digits = tz_str[1:]
            tz_h = int(digits[:2])
            tz_m = int(digits[2:4]) if len(digits) >= 4 else 0
            tz = datetime.timezone(sign * datetime.timedelta(hours=tz_h, minutes=tz_m))
    return datetime.datetime(year, month, day, hour, minute, second, microsecond, tzinfo=tz)


class CameraDriver(ABC):
    """Interfaz abstracta para control PTP de cámara."""

    def __init__(self, camera_name: str = "Generic Camera", is_dslr: bool = False):
        self.camera_name = camera_name
        self.is_dslr = is_dslr
        # Suelo de seguridad entre tomas: Z5 II (~0.06s) vs D750 con espejo (~0.20s)
        self.overhead_safety: float = 0.20 if is_dslr else 0.06
        self.connected: bool = False
        self._liveview_active: bool = False
        self.current_shutter: Optional[str] = None
        self.current_iso: Optional[str] = None
        self.is_silent_mode: bool = False
        self.on_shot_callback: Optional[Callable[[str, str], None]] = None

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def set_shutter_speed(self, speed: str) -> bool:
        pass

    @abstractmethod
    def set_iso(self, iso: str) -> bool:
        pass

    @abstractmethod
    def trigger_capture(self, fast_sequence: bool = False, **kwargs) -> bool:
        pass

    def set_silent_mode(self, enable: bool = True) -> bool:
        """Activa o desactiva el obturador electrónico silencioso (Silent Photography)."""
        self.is_silent_mode = bool(enable)
        return True

    def set_shooting_mode(self, mode: str = "single") -> bool:
        """Configura el modo de disparo (Drive Mode): 'single', 'continuous_h', 'continuous_l'."""
        return True

    def set_continuous_shooting_num(self, count: int = 1) -> bool:
        """Configura el número límite de disparos por ráfaga en modo continuo."""
        return True

    def set_ae_bracketing(self, enable: bool = True, count: int = 9, step_index: int = 6) -> bool:
        """Configura el horquillado automático de exposición (AE Bracketing) por hardware."""
        return True

    def trigger_burst(self, count: int = 9) -> bool:
        """Dispara una ráfaga de N tomas seguidas (para horquillado BKT o ráfaga de cámara)."""
        success = True
        for _ in range(count):
            if not self.trigger_capture():
                success = False
        return success

    def execute_bracket_ramp(self, shutter_list: List[str]) -> bool:
        """Ejecuta una rampa de velocidades consecutivas con cadencia optimizada."""
        success = True
        for speed in shutter_list:
            if not self.set_shutter_speed(speed):
                success = False
            if not self.trigger_capture(fast_sequence=True):
                success = False
        return success

    @abstractmethod
    def get_available_shutters(self) -> List[str]:
        pass

    @abstractmethod
    def get_available_isos(self) -> List[str]:
        pass

    def get_last_thumb(self, slot: int = 1) -> Optional[bytes]:
        """Obtiene la miniatura JPEG de la última toma si la cámara lo soporta."""
        return None

    def get_battery_level(self) -> int:
        """Nivel estimado de batería en porcentaje (0-100)."""
        return 100

    def get_sd_free_shots(self, slot: int = 1) -> int:
        """Estimación de disparos libres en la tarjeta de memoria."""
        return 1000

    def start_liveview(self) -> bool:
        """Inicia el streaming de Live View si la cámara lo soporta."""
        self._liveview_active = True
        return True

    def stop_liveview(self) -> bool:
        """Detiene el streaming de Live View."""
        self._liveview_active = False
        return True

    def get_liveview_frame(self) -> Optional[bytes]:
        """Obtiene la última trama JPEG de Live View."""
        return None

    def is_liveview_active(self) -> bool:
        """Indica si el Live View está activo."""
        return self._liveview_active

    def get_clock_time(self) -> Optional[datetime.datetime]:
        """Obtiene la fecha y hora interna actual del reloj (RTC) de la cámara."""
        return None

    def set_clock_time(self, target_dt: datetime.datetime) -> bool:
        """Ajusta el reloj interno (RTC) de la cámara a la fecha y hora indicada."""
        return False


class MockCameraDriver(CameraDriver):
    """Cámara simulada para desarrollo, pruebas de secuencias y ensayos de campo sin hardware."""

    STANDARD_SHUTTERS = [
        "1/8000", "1/4000", "1/2000", "1/1000", "1/500", "1/250",
        "1/125", "1/60", "1/30", "1/15", "1/8", "1/4", "1/2",
        "1s", "2s", "4s", "8s"
    ]
    STANDARD_ISOS = ["64", "100", "200", "400", "800", "1600", "3200", "6400"]

    def __init__(
        self,
        camera_name: str = "Nikon Z5 II (Simulada)",
        is_dslr: bool = False,
        battery_level: int = 95,
        sd_free_shots: int = 1420
    ):
        super().__init__(camera_name=camera_name, is_dslr=is_dslr)
        self.shot_history: List[dict] = []
        self._battery_level: int = battery_level
        self._sd_free_shots: int = sd_free_shots
        self.mock_focus_blur: float = 0.0  # 0.0 = nítido, >0.0 = desenfocado
        self.mock_saturation: bool = False  # Simulación de canal saturado (255)
        self._frame_count: int = 0
        self.shooting_mode: str = "single"
        self.continuous_shooting_num: int = 1
        self.ae_bracketing: bool = False
        self.ae_bracketing_count: int = 9
        self.ae_bracketing_step: int = 6
        self._clock_offset_sec: float = -0.85

    def get_clock_time(self) -> Optional[datetime.datetime]:
        """Devuelve la hora simulada de la cámara con su deriva."""
        return datetime.datetime.now() + datetime.timedelta(seconds=self._clock_offset_sec)

    def set_clock_time(self, target_dt: datetime.datetime) -> bool:
        """Ajusta el reloj simulado de la cámara."""
        now = datetime.datetime.now()
        dt_naive = target_dt.astimezone().replace(tzinfo=None) if target_dt.tzinfo else target_dt
        self._clock_offset_sec = (dt_naive - now).total_seconds()
        return True

    def set_shooting_mode(self, mode: str = "single") -> bool:
        self.shooting_mode = mode
        return True

    def set_continuous_shooting_num(self, count: int = 1) -> bool:
        self.continuous_shooting_num = count
        return True

    def set_ae_bracketing(self, enable: bool = True, count: int = 9, step_index: int = 6) -> bool:
        self.ae_bracketing = enable
        self.ae_bracketing_count = count
        self.ae_bracketing_step = step_index
        return True

    def set_mock_focus_sharpness(self, sharpness: float):
        """Ajusta nitidez simulada: 1.0 = nitidez óptima (blur 0.0), 0.0 = desenfoque total (blur 8.0)."""
        s = max(0.0, min(1.0, float(sharpness)))
        self.mock_focus_blur = (1.0 - s) * 8.0

    def set_mock_focus_blur(self, blur_radius: float):
        self.mock_focus_blur = max(0.0, float(blur_radius))

    def set_mock_saturation(self, saturated: bool):
        """Habilita o deshabilita la simulación de saturación (clipping a 255) en el sensor."""
        self.mock_saturation = bool(saturated)

    def get_liveview_frame(self) -> Optional[bytes]:
        """Genera una trama sintética de limbo solar con manchas solares y desenfoque variable."""
        try:
            import io
            from PIL import Image, ImageDraw, ImageFilter

            width, height = 640, 480
            img = Image.new("RGB", (width, height), color=(10, 12, 16))
            draw = ImageDraw.Draw(img)

            # Disco solar con limbo definido y borde de alta frecuencia
            sun_cx, sun_cy = width // 2, height // 2
            sun_r = 150
            if getattr(self, "mock_saturation", False):
                sun_fill = (255, 255, 255)
                sun_outline = (255, 230, 200)
            else:
                sun_fill = (235, 195, 75)
                sun_outline = (245, 140, 25)

            draw.ellipse(
                (sun_cx - sun_r, sun_cy - sun_r, sun_cx + sun_r, sun_cy + sun_r),
                fill=sun_fill,
                outline=sun_outline,
                width=3
            )

            # Manchas solares con umbra y penumbra
            s1_x, s1_y = sun_cx - 40, sun_cy - 30
            draw.ellipse((s1_x - 14, s1_y - 10, s1_x + 14, s1_y + 10), fill=(120, 90, 30))
            draw.ellipse((s1_x - 7, s1_y - 5, s1_x + 7, s1_y + 5), fill=(30, 20, 15))

            s2_x, s2_y = sun_cx + 45, sun_cy + 25
            draw.ellipse((s2_x - 10, s2_y - 8, s2_x + 10, s2_y + 8), fill=(120, 90, 30))
            draw.ellipse((s2_x - 5, s2_y - 4, s2_x + 5, s2_y + 4), fill=(30, 20, 15))

            # Detalle fino en el limbo (granulación)
            draw.arc(
                (sun_cx - sun_r + 2, sun_cy - sun_r + 2, sun_cx + sun_r - 2, sun_cy + sun_r - 2),
                start=30, end=75, fill=(255, 250, 200), width=2
            )

            self._frame_count += 1
            draw.text(
                (12, 12),
                f"MOCK LIVE VIEW | Frame #{self._frame_count} | Blur: {self.mock_focus_blur:.1f}px",
                fill=(180, 200, 220)
            )

            if self.mock_focus_blur > 0.05:
                img = img.filter(ImageFilter.GaussianBlur(radius=self.mock_focus_blur))

            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            return buf.getvalue()
        except Exception as e:
            return None

    def get_battery_level(self) -> int:
        return self._battery_level

    def get_sd_free_shots(self, slot: int = 1) -> int:
        return max(0, self._sd_free_shots - len(self.shot_history))

    def connect(self) -> bool:
        self.connected = True
        return True

    def disconnect(self):
        self.connected = False

    def set_shutter_speed(self, speed: str) -> bool:
        self.current_shutter = speed
        return True

    def set_iso(self, iso: str) -> bool:
        self.current_iso = iso
        return True

    def trigger_capture(self, fast_sequence: bool = False, **kwargs) -> bool:
        if not self.connected:
            return False
        timestamp = time.time()
        record = {
            "timestamp": timestamp,
            "shutter": self.current_shutter,
            "iso": self.current_iso,
            "camera": self.camera_name
        }
        self.shot_history.append(record)
        if self.on_shot_callback:
            self.on_shot_callback(self.current_shutter, self.current_iso)
        return True

    def trigger_burst(self, count: int = 9) -> bool:
        """Dispara una ráfaga simulada de N tomas seguidas."""
        if not self.connected:
            return False
        timestamp = time.time()
        for i in range(count):
            record = {
                "timestamp": timestamp + i * 0.05,
                "shutter": self.current_shutter,
                "iso": self.current_iso,
                "camera": self.camera_name,
                "burst_index": i + 1,
            }
            self.shot_history.append(record)
            if self.on_shot_callback:
                self.on_shot_callback(f"Ráfaga {i+1}/{count} ({self.current_shutter})", self.current_iso)
        return True

    def get_available_shutters(self) -> List[str]:
        return list(self.STANDARD_SHUTTERS)

    def get_available_isos(self) -> List[str]:
        return list(self.STANDARD_ISOS)

    def get_last_thumb(self, slot: int = 1) -> Optional[bytes]:
        """Genera una imagen JPEG sintética para previsualización en pruebas."""
        try:
            import io
            from PIL import Image, ImageDraw
            img = Image.new("RGB", (320, 240), color=(14, 16, 20))
            draw = ImageDraw.Draw(img)
            # Dibujar un simulacro de corona solar
            draw.ellipse((100, 60, 220, 180), fill=(255, 235, 150), outline=(255, 255, 255))
            draw.ellipse((120, 80, 200, 160), fill=(10, 10, 12))  # Silueta lunar
            draw.text((12, 12), f"MOCK PREVIEW | {self.current_shutter} ISO {self.current_iso}", fill=(220, 220, 220))
            draw.text((12, 215), f"Toma simulada #{len(self.shot_history)} [Ranura SD {slot}]", fill=(100, 180, 255))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            return buf.getvalue()
        except Exception:
            return None


class GPhotoCameraDriver(CameraDriver):
    """Driver real basado en libgphoto2 para Nikon Serie Z y D750."""

    def __init__(self, camera_name: str = "Nikon Camera", is_dslr: bool = False):
        super().__init__(camera_name=camera_name, is_dslr=is_dslr)
        self._camera = None
        self._context = None
        self._shutters_cache: List[str] = []
        self._isos_cache: List[str] = []

    def connect(self) -> bool:
        try:
            import gphoto2 as gp
            self._context = gp.Context()
            self._camera = gp.Camera()
            self._camera.init(self._context)

            # Forzar almacenamiento en tarjeta interna
            config = self._camera.get_config(self._context)
            target = config.get_child_by_name("capturetarget")
            target.set_value("Memory card")
            self._camera.set_config(config, self._context)

            # Cachear opciones disponibles de velocidad e ISO
            shutter_cfg = config.get_child_by_name("shutterspeed")
            self._shutters_cache = [shutter_cfg.get_choice(i) for i in range(shutter_cfg.count_choices())]
            iso_cfg = config.get_child_by_name("iso")
            self._isos_cache = [iso_cfg.get_choice(i) for i in range(iso_cfg.count_choices())]

            self.connected = True
            return True
        except Exception as e:
            # shortcut: fallo gphoto2 capturado en log, migrar a diálogo de reintento en UI
            print(f"[GPhotoDriver Error] No se pudo conectar con la cámara: {e}")
            self.connected = False
            return False

    def disconnect(self):
        if self._camera and self.connected:
            try:
                self._camera.exit(self._context)
            except Exception:
                pass
        self.connected = False

    def set_shutter_speed(self, speed: str) -> bool:
        if not self.connected:
            return False
        if self.current_shutter == speed:
            return True
        try:
            if hasattr(self._camera, "get_single_config"):
                speed_widget = self._camera.get_single_config("shutterspeed", self._context)
                speed_widget.set_value(speed)
                self._camera.set_single_config("shutterspeed", speed_widget, self._context)
            else:
                config = self._camera.get_config(self._context)
                speed_widget = config.get_child_by_name("shutterspeed")
                speed_widget.set_value(speed)
                self._camera.set_config(config, self._context)
            self.current_shutter = speed
            return True
        except Exception as e:
            print(f"[GPhotoDriver Error] Error al cambiar velocidad: {e}")
            return False

    def set_iso(self, iso: str) -> bool:
        if not self.connected:
            return False
        if self.current_iso == iso:
            return True
        try:
            if hasattr(self._camera, "get_single_config"):
                iso_widget = self._camera.get_single_config("iso", self._context)
                iso_widget.set_value(iso)
                self._camera.set_single_config("iso", iso_widget, self._context)
            else:
                config = self._camera.get_config(self._context)
                iso_widget = config.get_child_by_name("iso")
                iso_widget.set_value(iso)
                self._camera.set_config(config, self._context)
            self.current_iso = iso
            return True
        except Exception as e:
            print(f"[GPhotoDriver Error] Error al cambiar ISO: {e}")
            return False

    def trigger_capture(self, fast_sequence: bool = False, **kwargs) -> bool:
        if not self.connected:
            return False
        try:
            self._camera.trigger_capture(self._context)
            if self.on_shot_callback:
                self.on_shot_callback(self.current_shutter, self.current_iso)
            return True
        except Exception as e:
            print(f"[GPhotoDriver Error] Error en trigger_capture: {e}")
            return False

    def get_available_shutters(self) -> List[str]:
        return self._shutters_cache if self._shutters_cache else MockCameraDriver.STANDARD_SHUTTERS

    def get_available_isos(self) -> List[str]:
        return self._isos_cache if self._isos_cache else MockCameraDriver.STANDARD_ISOS

    def get_clock_time(self) -> Optional[datetime.datetime]:
        """Obtiene la fecha y hora interna actual de la cámara vía gphoto2."""
        if not self.connected or not self._camera:
            return None
        try:
            if hasattr(self._camera, "get_single_config"):
                widget = self._camera.get_single_config("datetime", self._context)
                val = widget.get_value()
                try:
                    return datetime.datetime.fromtimestamp(int(val))
                except ValueError:
                    return parse_ptp_datetime(str(val))
            return None
        except Exception:
            return None

    def set_clock_time(self, target_dt: datetime.datetime) -> bool:
        """Ajusta el reloj de la cámara vía gphoto2."""
        if not self.connected or not self._camera:
            return False
        try:
            ts = int(target_dt.timestamp())
            if hasattr(self._camera, "get_single_config"):
                widget = self._camera.get_single_config("datetime", self._context)
                widget.set_value(ts)
                self._camera.set_single_config("datetime", widget, self._context)
                return True
            return False
        except Exception:
            return False


def parse_shutter_to_ptp_u32(shutter_str: str) -> int:
    """Convierte cadena de velocidad (ej: '1/1000', '2s') a unidades PTP (1/10000 de segundo)."""
    s = str(shutter_str).strip().lower()
    if s.endswith("s"):
        try:
            sec = float(s[:-1])
            return max(1, int(sec * 10000))
        except ValueError:
            return 10000
    if "/" in s:
        try:
            parts = s.split("/")
            num = float(parts[0])
            den = float(parts[1])
            return max(1, int((num / den) * 10000))
        except (ValueError, ZeroDivisionError):
            return 10
    try:
        sec = float(s)
        return max(1, int(sec * 10000))
    except ValueError:
        return 100


class NikonPTPDriver(CameraDriver):
    """Driver nativo PTP directo por USB para Nikon Z5 II / Serie Z en Windows y Linux."""

    def __init__(self, camera_name: str = "Nikon Z5 II (USB PTP)", is_dslr: bool = False):
        super().__init__(camera_name=camera_name, is_dslr=is_dslr)
        self.dev = None
        self.ep_out = None
        self.ep_in = None
        self.ep_intr = None
        self.tx_id: int = 1
        self.model: str = "Nikon Z5 II"
        self.serial_number: str = ""
        self._cached_shutter_prop: Optional[int] = None
        self._cached_iso_prop: Optional[int] = None
        self.last_captured_handle: Optional[int] = None

    def _dispose(self):
        """Libera de forma segura el manejador USB para prevenir errores de 'Access Denied'."""
        if self.dev:
            try:
                import usb.util
                usb.util.dispose_resources(self.dev)
            except Exception:
                pass
            self.dev = None
        self.ep_out = None
        self.ep_in = None
        self.ep_intr = None

    def _drain_endpoints(self):
        """Drena cualquier byte residual pendiente en los endpoints IN que pueda provocar timeouts."""
        for ep in (self.ep_in, self.ep_intr):
            if ep:
                for _ in range(3):
                    try:
                        chunk = ep.read(512, timeout=5)
                        if not chunk:
                            break
                    except Exception:
                        break

    def connect(self) -> bool:
        self._dispose()
        try:
            import struct
            import libusb_package
            import usb.core
            import usb.util

            backend = libusb_package.get_libusb1_backend()
            self.dev = usb.core.find(idVendor=0x04B0, backend=backend)
            if not self.dev:
                print("[NikonPTP] No se encontró cámara Nikon en el bus USB.")
                self.connected = False
                return False

            cfg = self.dev.get_active_configuration()
            intf = cfg[(0, 0)]

            for ep in intf:
                addr = ep.bEndpointAddress
                bm = ep.bmAttributes & 0x03
                is_in = (addr & 0x80) != 0
                if bm == 2:  # BULK
                    if is_in:
                        self.ep_in = ep
                    else:
                        self.ep_out = ep
                elif bm == 3 and is_in:  # INTERRUPT
                    self.ep_intr = ep

            if not self.ep_out or not self.ep_in:
                print("[NikonPTP] No se encontraron endpoints Bulk.")
                self._dispose()
                self.connected = False
                return False

            # Limpiar cualquier buffer residual antes de iniciar la sesión
            self._drain_endpoints()

            # PTP OpenSession (SessionID = 1)
            self.tx_id = 1
            cmd_open = struct.pack("<IHHI I", 16, 1, 0x1002, 0, 1)
            self.ep_out.write(cmd_open, timeout=2000)
            resp_raw = self.ep_in.read(512, timeout=2000)
            resp_code = struct.unpack("<IHHI", resp_raw[:12])[2]

            # 0x2001 (OK) o 0x201E (Session already open)
            if resp_code in (0x2001, 0x201E):
                self.connected = True
                print("[NikonPTP] Conectado exitosamente con Nikon Z5 II vía PTP USB.")
                # Forzar almacenamiento exclusivo en tarjeta interna (0xD00B = 0: Card)
                self._set_ptp_prop_u8(0xD00B, 0)
                return True
            else:
                print(f"[NikonPTP] OpenSession retornó código: 0x{resp_code:04X}")
                self._dispose()
                self.connected = False
                return False

        except Exception as e:
            print(f"[NikonPTP Error] Fallo al inicializar sesión PTP: {e}")
            self._dispose()
            self.connected = False
            return False

    def disconnect(self):
        if self.connected and self.ep_out and self.ep_in:
            try:
                import struct
                self.tx_id += 1
                cmd_close = struct.pack("<IHHI", 12, 1, 0x1003, self.tx_id)
                self.ep_out.write(cmd_close, timeout=2000)
                self.ep_in.read(512, timeout=2000)
            except Exception:
                pass
        self._dispose()
        self.connected = False

    def _set_ptp_prop_u32(self, prop_code: int, value: int) -> bool:
        """Envía SetDevicePropValue (0x1016) para propiedades uint32 con drenaje preventivo."""
        if not self.connected or not self.ep_out or not self.ep_in:
            return False
        try:
            import struct
            self.tx_id += 1
            cmd = struct.pack("<IHHI I", 16, 1, 0x1016, self.tx_id, prop_code)
            self.ep_out.write(cmd, timeout=200)
            data = struct.pack("<IHHI I", 16, 2, 0x1016, self.tx_id, value)
            self.ep_out.write(data, timeout=200)
            resp = self.ep_in.read(512, timeout=250)
            return struct.unpack("<IHHI", resp[:12])[2] == 0x2001
        except Exception:
            self._drain_endpoints()
            return False

    def _set_ptp_prop_u8(self, prop_code: int, value: int) -> bool:
        """Envía SetDevicePropValue (0x1016) para propiedades uint8 con drenaje preventivo."""
        if not self.connected or not self.ep_out or not self.ep_in:
            return False
        try:
            import struct
            self.tx_id += 1
            cmd = struct.pack("<IHHI I", 16, 1, 0x1016, self.tx_id, prop_code)
            self.ep_out.write(cmd, timeout=200)
            data = struct.pack("<IHHI B", 13, 2, 0x1016, self.tx_id, value)
            self.ep_out.write(data, timeout=200)
            resp = self.ep_in.read(512, timeout=250)
            return struct.unpack("<IHHI", resp[:12])[2] == 0x2001
        except Exception:
            self._drain_endpoints()
            return False

    def _set_ptp_prop_u16(self, prop_code: int, value: int) -> bool:
        """Envía SetDevicePropValue (0x1016) para propiedades uint16 con drenaje preventivo."""
        if not self.connected or not self.ep_out or not self.ep_in:
            return False
        try:
            import struct
            self.tx_id += 1
            cmd = struct.pack("<IHHI I", 16, 1, 0x1016, self.tx_id, prop_code)
            self.ep_out.write(cmd, timeout=200)
            data = struct.pack("<IHHI H", 14, 2, 0x1016, self.tx_id, value)
            self.ep_out.write(data, timeout=200)
            resp = self.ep_in.read(512, timeout=250)
            return struct.unpack("<IHHI", resp[:12])[2] == 0x2001
        except Exception:
            self._drain_endpoints()
            return False

    def _get_ptp_prop_string(self, prop_code: int) -> Optional[str]:
        """Envía GetDevicePropValue (0x1014) y parsea el PTP String devuelto."""
        if not self.connected or not self.ep_out or not self.ep_in:
            return None
        try:
            import struct
            self.tx_id += 1
            cmd = struct.pack("<IHHI I", 16, 1, 0x1014, self.tx_id, prop_code)
            self.ep_out.write(cmd, timeout=300)
            data_raw = bytes(self.ep_in.read(512, timeout=500))
            if len(data_raw) < 13:
                return None
            num_chars = data_raw[12]
            res_str = ""
            if num_chars > 0:
                str_bytes = data_raw[13: 13 + (num_chars * 2)]
                res_str = str_bytes.decode("utf-16le", errors="ignore").rstrip("\x00")
            resp = self.ep_in.read(512, timeout=300)
            resp_code = struct.unpack("<IHHI", resp[:12])[2]
            return res_str if resp_code == 0x2001 else None
        except Exception:
            self._drain_endpoints()
            return None

    def _set_ptp_prop_string(self, prop_code: int, value: str) -> bool:
        """Envía SetDevicePropValue (0x1016) para una propiedad de tipo PTP String (0xFFFF)."""
        if not self.connected or not self.ep_out or not self.ep_in:
            return False
        try:
            import struct
            self.tx_id += 1
            cmd = struct.pack("<IHHI I", 16, 1, 0x1016, self.tx_id, prop_code)
            self.ep_out.write(cmd, timeout=300)

            raw_str = (value + "\x00").encode("utf-16le")
            num_chars = len(value) + 1
            payload = struct.pack("<B", num_chars) + raw_str
            data_hdr = struct.pack("<IHHI", 12 + len(payload), 2, 0x1016, self.tx_id)
            self.ep_out.write(data_hdr + payload, timeout=300)
            resp = self.ep_in.read(512, timeout=400)
            return struct.unpack("<IHHI", resp[:12])[2] == 0x2001
        except Exception:
            self._drain_endpoints()
            return False

    def get_clock_time(self) -> Optional[datetime.datetime]:
        """Obtiene la hora actual del RTC de la cámara mediante PTP 0x5011 (DateTime)."""
        raw_str = self._get_ptp_prop_string(0x5011)
        return parse_ptp_datetime(raw_str) if raw_str else None

    def set_clock_time(self, target_dt: datetime.datetime) -> bool:
        """Ajusta el reloj de la cámara mediante PTP 0x5011 (DateTime)."""
        dt_str = target_dt.strftime("%Y%m%dT%H%M%S.0")
        return self._set_ptp_prop_string(0x5011, dt_str)

    def set_shutter_speed(self, speed: str) -> bool:
        """Configura la velocidad de obturación física en la cámara vía PTP con caché de opcode."""
        if self.current_shutter == speed:
            return True
        val = parse_shutter_to_ptp_u32(speed)
        if self._cached_shutter_prop is not None:
            if self._set_ptp_prop_u32(self._cached_shutter_prop, val):
                self.current_shutter = speed
                return True
        for prop in (0xD100, 0x500D):
            if self._set_ptp_prop_u32(prop, val):
                self._cached_shutter_prop = prop
                self.current_shutter = speed
                return True
        return False

    def set_iso(self, iso: str) -> bool:
        """Configura la sensibilidad ISO física en la cámara vía PTP con caché de opcode."""
        if self.current_iso == iso:
            return True
        try:
            val = int(iso.strip())
        except ValueError:
            val = 100
        if self._cached_iso_prop is not None:
            if self._set_ptp_prop_u16(self._cached_iso_prop, val):
                self.current_iso = iso
                return True
        for prop in (0xD102, 0x500F):
            if self._set_ptp_prop_u16(prop, val):
                self._cached_iso_prop = prop
                self.current_iso = iso
                return True
        return False

    def set_silent_mode(self, enable: bool = True) -> bool:
        """Configura Silent Photography (obturador electrónico) vía PTP de Nikon (0xD076)."""
        self.is_silent_mode = bool(enable)
        val = 1 if enable else 0
        # Intentar uint8 y uint16 en vendor prop 0xD076
        if not self._set_ptp_prop_u8(0xD076, val):
            self._set_ptp_prop_u16(0xD076, val)
        return True

    def trigger_capture(self, fast_sequence: bool = False, fetch_handle: bool = False, **kwargs) -> bool:
        if not self.connected or not self.ep_out or not self.ep_in:
            return False
        try:
            import struct
            self.tx_id += 1
            # PTP InitiateCapture (0x100E): Param1=0 (StorageID), Param2=0 (Format)
            cmd_capture = struct.pack("<IHHI II", 20, 1, 0x100E, self.tx_id, 0, 0)
            self.ep_out.write(cmd_capture, timeout=2000)
            cap_resp = self.ep_in.read(512, timeout=3000)
            cap_code = struct.unpack("<IHHI", cap_resp[:12])[2]

            self.last_captured_handle = None
            if fetch_handle and self.ep_intr:
                try:
                    evt = self.ep_intr.read(64, timeout=20)
                    if len(evt) >= 16:
                        evt_code = struct.unpack("<IHHI", evt[:12])[2]
                        if evt_code == 0x4002:  # PTP_EC_ObjectAdded
                            self.last_captured_handle = struct.unpack("<I", evt[12:16])[0]
                except Exception:
                    pass

            if cap_code == 0x2001:  # PTP_RC_OK
                if self.on_shot_callback:
                    self.on_shot_callback(self.current_shutter, self.current_iso)
                return True
            else:
                print(f"[NikonPTP] Error en InitiateCapture: 0x{cap_code:04X}")
                self._drain_endpoints()
                return False
        except Exception as e:
            print(f"[NikonPTP Error] Excepción al disparar: {e}")
            self._drain_endpoints()
            return False

    def trigger_burst(self, count: int = 9) -> bool:
        """Dispara N pulsos rápidos consecutivos (ideal para activar el horquillado BKT de la cámara)."""
        if not self.connected:
            return False
        import time
        success = True
        for i in range(count):
            ok = self.trigger_capture()
            if not ok:
                success = False
            time.sleep(0.08)  # 80ms entre pulsos para no colapsar el bus
        return success

    def get_available_shutters(self) -> List[str]:
        return MockCameraDriver.STANDARD_SHUTTERS

    def get_available_isos(self) -> List[str]:
        return MockCameraDriver.STANDARD_ISOS

    def get_last_thumb(self, slot: int = 1) -> Optional[bytes]:
        """Descarga la miniatura JPEG incrustada de la última foto tomada, filtrando por ranura SD (Slot 1 o Slot 2)."""
        if not self.connected or not self.ep_out or not self.ep_in:
            return None
        try:
            import struct
            target_handle = self.last_captured_handle

            # Si no hay handle directo del evento o se solicita una ranura específica
            if not target_handle:
                # StorageID en PTP: Slot 1 = 0x00010001, Slot 2 = 0x00020001
                storage_id = (slot << 16) | 0x0001

                # 1. PTP GetObjectHandles (0x1007) filtrando por la ranura SD elegida
                self.tx_id += 1
                cmd_handles = struct.pack("<IHHI III", 24, 1, 0x1007, self.tx_id, storage_id, 0, 0)
                self.ep_out.write(cmd_handles, timeout=2000)
                data = bytes(self.ep_in.read(16384, timeout=3000))
                status_raw = self.ep_in.read(512, timeout=2000)
                status_code = struct.unpack("<IHHI", status_raw[:12])[2]

                # Si la ranura seleccionada no tiene fotos, fallback a la ranura alternativa
                if status_code != 0x2001 or len(data) < 16:
                    alt_slot = 2 if slot == 1 else 1
                    storage_id = (alt_slot << 16) | 0x0001
                    self.tx_id += 1
                    cmd_handles = struct.pack("<IHHI III", 24, 1, 0x1007, self.tx_id, storage_id, 0, 0)
                    self.ep_out.write(cmd_handles, timeout=2000)
                    data = bytes(self.ep_in.read(16384, timeout=3000))
                    self.ep_in.read(512, timeout=2000)

                num_handles = struct.unpack("<I", data[12:16])[0] if len(data) >= 16 else 0
                if num_handles == 0:
                    return None

                # El último handle registrado en esta tarjeta específica
                target_handle = struct.unpack("<I", data[12 + num_handles * 4: 16 + num_handles * 4])[0]

            # 2. PTP GetThumb (0x100A): Param1=Handle
            self.tx_id += 1
            cmd_thumb = struct.pack("<IHHI I", 16, 1, 0x100A, self.tx_id, target_handle)
            self.ep_out.write(cmd_thumb, timeout=2000)

            thumb_buf = bytearray()
            first_chunk = self.ep_in.read(16384, timeout=4000)
            if len(first_chunk) < 12:
                return None

            total_len = struct.unpack("<I", first_chunk[:4])[0]
            thumb_buf.extend(first_chunk[12:])  # Descartar cabecera PTP

            bytes_remaining = total_len - len(first_chunk)
            while bytes_remaining > 0:
                chunk = self.ep_in.read(min(bytes_remaining, 16384), timeout=3000)
                thumb_buf.extend(chunk)
                bytes_remaining -= len(chunk)

            # Leer respuesta de estado final
            self.ep_in.read(512, timeout=2000)

            # Limpiar handle para la próxima consulta
            self.last_captured_handle = None

            # Validar cabecera mágica JPEG (0xFF, 0xD8)
            if len(thumb_buf) > 4 and thumb_buf[0] == 0xFF and thumb_buf[1] == 0xD8:
                return bytes(thumb_buf)
            return None
        except Exception as e:
            print(f"[NikonPTP Warning] No se pudo leer la miniatura: {e}")
            return None

    def get_battery_level(self) -> int:
        """Lee el porcentaje de batería mediante PTP GetDevicePropValue (0x5001)."""
        if not self.connected or not self.ep_out or not self.ep_in:
            return 90
        try:
            import struct
            self.tx_id += 1
            cmd = struct.pack("<IHHI I", 16, 1, 0x1015, self.tx_id, 0x5001)
            self.ep_out.write(cmd, timeout=300)
            data = self.ep_in.read(512, timeout=500)
            self.ep_in.read(512, timeout=500)
            if len(data) >= 13:
                return int(data[12])
        except Exception:
            pass
        return 88

    def get_sd_free_shots(self, slot: int = 1) -> int:
        return 1250

    def start_liveview(self) -> bool:
        if not self.connected or not self.ep_out or not self.ep_in:
            return False
        try:
            import struct
            self.tx_id += 1
            cmd = struct.pack("<IHHI", 12, 1, 0x90C1, self.tx_id)
            self.ep_out.write(cmd, timeout=1000)
            self.ep_in.read(512, timeout=1000)
            self._liveview_active = True
            return True
        except Exception:
            self._liveview_active = True
            return True

    def stop_liveview(self) -> bool:
        if self.connected and self.ep_out and self.ep_in:
            try:
                import struct
                self.tx_id += 1
                cmd = struct.pack("<IHHI", 12, 1, 0x90C2, self.tx_id)
                self.ep_out.write(cmd, timeout=1000)
                self.ep_in.read(512, timeout=1000)
            except Exception:
                pass
        self._liveview_active = False
        return True

    def get_liveview_frame(self) -> Optional[bytes]:
        """Descarga una trama continua de Live View vía PTP (0x90C3 GetLiveViewImage)."""
        if not self.connected or not self.ep_out or not self.ep_in:
            return None
        try:
            import struct
            self.tx_id += 1
            cmd = struct.pack("<IHHI", 12, 1, 0x90C3, self.tx_id)
            self.ep_out.write(cmd, timeout=1000)
            data = bytearray(self.ep_in.read(16384, timeout=1500))
            if len(data) < 12:
                return None
            total_len = struct.unpack("<I", data[:4])[0]
            bytes_remaining = total_len - len(data)
            while bytes_remaining > 0:
                chunk = self.ep_in.read(min(bytes_remaining, 16384), timeout=1500)
                data.extend(chunk)
                bytes_remaining -= len(chunk)
            self.ep_in.read(512, timeout=1000)

            idx_start = data.find(b"\xff\xd8")
            if idx_start != -1:
                idx_end = data.rfind(b"\xff\xd9")
                if idx_end != -1:
                    return bytes(data[idx_start:idx_end + 2])
                return bytes(data[idx_start:])
            return None
        except Exception:
            return None


class NikonSdkDriver(CameraDriver):
    """Driver nativo oficial de Nikon basado en el Unified Remote Control SDK (Plug & Play WPD)."""

    STANDARD_SHUTTERS = [
        "1/8000", "1/6400", "1/5000", "1/4000", "1/3200", "1/2500", "1/2000",
        "1/1600", "1/1250", "1/1000", "1/800", "1/640", "1/500", "1/400",
        "1/320", "1/250", "1/200", "1/160", "1/125", "1/100", "1/90", "1/80", "1/75",
        "1/60", "1/50", "1/40", "1/30", "1/25", "1/20", "1/15", "1/13",
        "1/10", "1/8", "1/6", "1/5", "1/4", "1/3", "1/2.5", "1/2",
        "1/1.6", "1/1.3", "1s", "1.3s", "1.6s", "2s", "2.5s", "3s",
        "4s", "5s", "6s", "8s", "10s", "13s", "15s", "20s", "25s",
        "30s", "60s", "120s", "180s", "240s", "300s", "480s", "600s", "720s", "900s",
        "Bulb", "Time"
    ]

    SHUTTER_INDEX_MAP = {
        "time": 0, "bulb": 1, "900s": 2, "720s": 3, "600s": 4, "480s": 5, "300s": 6,
        "240s": 7, "180s": 8, "120s": 9, "90s": 10, "60s": 11, "30s": 12, "25s": 13,
        "20s": 14, "15s": 15, "13s": 16, "10s": 17, "8s": 18, "6s": 19, "5s": 20,
        "4s": 21, "3s": 22, "2.5s": 23, "2s": 24, "1.6s": 25, "1.3s": 26, "1s": 27,
        "1": 27, "1/1.3": 28, "1/1.6": 29, "1/2": 30, "1/2.5": 31, "1/3": 32,
        "1/4": 33, "1/5": 34, "1/6": 35, "1/8": 36, "1/10": 37, "1/13": 38,
        "1/15": 39, "1/20": 40, "1/25": 41, "1/30": 42, "1/40": 43, "1/50": 44,
        "1/60": 45, "1/75": 46, "1/75s": 46, "1/80": 46, "1/90": 47, "1/90s": 47,
        "1/100": 47, "1/125": 48, "1/160": 49, "1/200": 50,
        "1/250": 51, "1/320": 52, "1/400": 53, "1/500": 54, "1/640": 55, "1/800": 56,
        "1/1000": 57, "1/1250": 58, "1/1600": 59, "1/2000": 60, "1/2500": 61,
        "1/3200": 62, "1/4000": 63, "1/5000": 64, "1/6400": 65, "1/8000": 66
    }

    STANDARD_ISOS = ["64", "100", "200", "400", "800", "1600", "3200", "6400", "12800", "25600"]

    ISO_INDEX_MAP = {
        "64": 0, "80": 1, "100": 2, "125": 3, "160": 4, "200": 5, "250": 6, "320": 7,
        "400": 8, "500": 9, "640": 10, "800": 11, "1000": 12, "1250": 13, "1600": 14,
        "2000": 15, "2500": 16, "3200": 17, "4000": 18, "5000": 19, "6400": 20,
        "8000": 21, "10000": 22, "12800": 23, "25600": 24, "51200": 25
    }

    @staticmethod
    def _shutter_str_to_seconds(shutter_str: str) -> float:
        """Convierte cadena de velocidad ('1/1000', '2s', '1/1.3') a segundos reales."""
        s = str(shutter_str).strip().lower().rstrip("s")
        if s in ("bulb", "time"):
            return 1.0
        if "/" in s:
            try:
                num, den = s.split("/")
                return float(num) / float(den)
            except (ValueError, ZeroDivisionError):
                return 0.001
        try:
            return float(s)
        except ValueError:
            return 0.001

    def __init__(self, camera_name: str = "Nikon Z5 II (Nikon SDK)", is_dslr: bool = False, bin_dir: Optional[str] = None):
        super().__init__(camera_name=camera_name, is_dslr=is_dslr)
        if bin_dir is None:
            root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            bin_dir = os.path.join(root, "Win_DRV", "Nikon_Z")
        self.bin_dir = bin_dir
        self.exe_path = os.path.join(bin_dir, "TestApp.exe")
        self.proc: Optional[subprocess.Popen] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._last_lv_request_time: float = 0.0
        self.current_save_media: int = 0
        self.current_shooting_mode: str = "single"
        self._lock: threading.Lock = threading.Lock()
        self._clock_offset_sec: float = 0.0

    def _read_output(self):
        """Lectura en segundo plano del flujo stdout de TestApp.exe para drenar el buffer del pipe sin bloquear."""
        while self.proc and self.proc.poll() is None:
            try:
                data = os.read(self.proc.stdout.fileno(), 1024)
                if not data:
                    break
            except Exception:
                break

    def _send(self, cmd: str, delay: float = 0.035) -> bool:
        """Envía un comando al stdin de TestApp.exe de manera thread-safe con pausa para procesamiento."""
        if not self.proc or self.proc.poll() is not None:
            return False
        try:
            self.proc.stdin.write(f"{cmd}\n".encode("latin-1"))
            self.proc.stdin.flush()
            if delay > 0:
                time.sleep(delay)
            return True
        except Exception as e:
            print(f"[NikonSdkDriver Error] Fallo al enviar comando '{cmd}': {e}")
            return False

    def _send_batch(self, commands: List[str], final_delay: float = 0.015) -> bool:
        """Envía una secuencia completa de menú de una sola vez al buffer stdin sin sleeps intermedios."""
        if not self.proc or self.proc.poll() is not None:
            return False
        try:
            payload = "\n".join(commands) + "\n"
            self.proc.stdin.write(payload.encode("latin-1"))
            self.proc.stdin.flush()
            if final_delay > 0:
                time.sleep(final_delay)
            return True
        except Exception as e:
            print(f"[NikonSdkDriver Error] Fallo en batch {commands}: {e}")
            return False

    def connect(self) -> bool:
        if not os.path.exists(self.exe_path):
            print(f"[NikonSdkDriver Error] No se encontró el ejecutable del SDK en {self.exe_path}")
            self.connected = False
            return False

        try:
            with self._lock:
                self.proc = subprocess.Popen(
                    [self.exe_path],
                    cwd=self.bin_dir,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT
                )
                self._reader_thread = threading.Thread(target=self._read_output, daemon=True)
                self._reader_thread.start()

                time.sleep(0.3)
                self._send("1", delay=0.3)  # Select Device
                self._send("1", delay=0.5)  # Device 1

                if self.proc.poll() is not None:
                    self.connected = False
                    return False

                self.connected = True

            # Configurar almacenamiento EXCLUSIVO en tarjeta SD (SaveMedia = 0: Card, sin descarga USB)
            self.set_save_media_card()
            # Asegurar modo de disparo único (Single) por defecto
            self.set_shooting_mode("single")
            # Forzar sincronización inicial de parámetros con la cámara física
            self.set_iso("100")
            self.set_shutter_speed("1/1000")
            return True
        except Exception as e:
            print(f"[NikonSdkDriver Error] Error al iniciar sesión SDK: {e}")
            self.connected = False
            return False

    def set_save_media(self, mode: int = 0) -> bool:
        """
        Configura el almacenamiento en la cámara Nikon:
        0 = Card (exclusivo tarjeta SD, máxima velocidad para ráfaga/eclipse)
        1 = SDRAM (solo memoria volátil / PC, NO graba en tarjeta)
        2 = Card + SDRAM (graba en tarjeta SD y transfiere copia a PC para preview)
        """
        if not self.proc or self.proc.poll() is not None:
            return False
        with self._lock:
            self._send_batch(["1", "11", str(mode), "0"], final_delay=0.025)
        self.current_save_media = mode
        return True

    def set_save_media_card(self) -> bool:
        """Fuerza a la cámara a guardar solo en la tarjeta SD (Card = 0) sin transferir 25MB RAW por USB."""
        return self.set_save_media(0)

    def disconnect(self):
        if self.proc and self.proc.poll() is None:
            try:
                with self._lock:
                    self._send("0", delay=0.1)
                    self._send("0", delay=0.1)
                time.sleep(0.1)
                self.proc.terminate()
            except Exception:
                pass
        self.connected = False

    def set_shutter_speed(self, speed: str) -> bool:
        if not self.connected or not self.proc or self.proc.poll() is not None:
            return False
        clean_speed = str(speed).strip().lower()
        if self.current_shutter and self.current_shutter.lower() == clean_speed:
            return True
        idx = self.SHUTTER_INDEX_MAP.get(clean_speed, 57)
        with self._lock:
            self._send_batch(["1", "8", str(idx), "0"], final_delay=0.015)
        self.current_shutter = speed
        return True

    def set_iso(self, iso: str) -> bool:
        if not self.connected or not self.proc or self.proc.poll() is not None:
            return False
        clean_iso = str(iso).strip().upper().replace("ISO", "").strip()
        if self.current_iso and self.current_iso == clean_iso:
            return True
        idx = self.ISO_INDEX_MAP.get(clean_iso)
        if idx is not None:
            with self._lock:
                self._send_batch(["3", "2", str(idx), "0"], final_delay=0.025)
        self.current_iso = clean_iso
        return True

    def set_silent_mode(self, enable: bool = True) -> bool:
        """Indica el estado del obturador electrónico silencioso."""
        self.is_silent_mode = bool(enable)
        return True

    def set_shooting_mode(self, mode: str = "single") -> bool:
        """
        Configura el modo de disparo (Drive Mode) de la Nikon Serie Z:
        - 'single': Disparo único fotograma a fotograma (S) [Índice 0]
        - 'continuous_h': Ráfaga continua alta en RAW (CH) [Índice 2]
        - 'continuous_l': Ráfaga continua baja en RAW (CL) [Índice 1]
        """
        if not self.connected or not self.proc or self.proc.poll() is not None:
            return False
        clean = mode.lower().strip()
        idx = 2 if "high" in clean or clean in ("continuous_h", "ch") else (1 if "low" in clean or clean in ("continuous_l", "cl") else 0)
        target_mode = "continuous_h" if idx == 2 else ("continuous_l" if idx == 1 else "single")
        if getattr(self, "current_shooting_mode", "single") == target_mode:
            return True
        with self._lock:
            self._send_batch(["3", "8", str(idx), "0"], final_delay=0.025)
        self.current_shooting_mode = target_mode
        return True

    def set_continuous_shooting_num(self, count: int = 1) -> bool:
        """Configura el número límite de disparos por ráfaga en modo continuo (Menu 3 -> 9)."""
        if not self.connected or not self.proc or self.proc.poll() is not None:
            return False
        try:
            c = max(1, min(65535, int(count)))
            with self._lock:
                self._send_batch(["3", "9", str(c), "0"], final_delay=0.025)
            return True
        except Exception as e:
            print(f"[NikonSdkDriver Warning] Error fijando ContinuousShootingNum ({count}): {e}")
            return False

    def set_ae_bracketing(self, enable: bool = True, count: int = 7, step_index: int = 4) -> bool:
        """
        Configura el horquillado automático de exposición (AE Bracketing) por hardware:
        - enable: True para activar, False para desactivar.
        - count: 9 (Both_9, índice 7), 7 (Both_7, índice 6), 5 (Both_5, índice 5), 3 (Both_3, índice 4).
        - step_index: 4 para 1.7 EV (5/3 EV en pasos 1/3 EV), 2 para 1.0 EV, 5 para 2.0 EV.
        """
        if not self.connected or not self.proc or self.proc.poll() is not None:
            return False
        try:
            self.ae_bracketing = enable
            # En SetBoolCapability: 1 = True, 2 = False
            b_val = "1" if enable else "2"
            cmds = ["1", "24", b_val]
            if enable:
                bkt_type = 7 if count >= 9 else (6 if count >= 7 else (5 if count >= 5 else 4))
                cmds.extend(["28", str(bkt_type), "26", str(step_index)])
            cmds.append("0")
            with self._lock:
                self._send_batch(cmds, final_delay=0.030)
            return True
        except Exception as e:
            print(f"[NikonSdkDriver Warning] Error configurando AE Bracketing: {e}")
            return False

    def trigger_capture(self, fast_sequence: bool = False, **kwargs) -> bool:
        if not self.connected or not self.proc or self.proc.poll() is not None:
            return False

        was_lv = self._liveview_active
        if was_lv:
            self.stop_liveview()

        if getattr(self, "current_shooting_mode", "single") != "single":
            self.set_shooting_mode("single")

        exp_sec = self._shutter_str_to_seconds(self.current_shutter)
        wait_time = max(0.055, exp_sec + 0.045) if fast_sequence else max(0.22, exp_sec + 0.08)

        with self._lock:
            self._send_batch(["6", "1"], final_delay=wait_time)
            if self.on_shot_callback:
                self.on_shot_callback(self.current_shutter, self.current_iso)
            self._send("0", delay=0.01)

        if was_lv and not fast_sequence:
            self.start_liveview()
        return True

    def execute_bracket_ramp(self, shutter_list: List[str]) -> bool:
        """Ejecuta un barrido rápido de velocidades sin reactivar Live View entre tomas."""
        was_lv = self._liveview_active
        if was_lv:
            self.stop_liveview()
        success = True
        for speed in shutter_list:
            if not self.set_shutter_speed(speed):
                success = False
            if not self.trigger_capture(fast_sequence=True):
                success = False
        if was_lv:
            self.start_liveview()
        return success

    def trigger_burst(self, count: int = 9) -> bool:
        """
        Ráfaga continua nativa por hardware en modo Continuous High (CH RAW) directa a tarjeta SD.
        Lanza 'Continuous Shooting' (Menú 6 -> 2), disparando trenes de tomas en alta cadencia
        directas al búfer SD sin saturación de bus USB.
        """
        if not self.connected or not self.proc or self.proc.poll() is not None:
            return False

        was_lv = self._liveview_active
        if was_lv:
            self.stop_liveview()

        if self.current_save_media != 0:
            self.set_save_media(0)

        # 1. Asegurar modo Continuous High en hardware solo si no estaba puesto
        if getattr(self, "current_shooting_mode", "single") != "continuous_h":
            self.set_shooting_mode("continuous_h")

        if self.on_shot_callback:
            self.on_shot_callback(f"Ráfaga Hardware ({count} tomas, {self.current_shutter})", self.current_iso)

        # 2. En TestApp opción 2 solicita el número de tomas
        exp_sec = self._shutter_str_to_seconds(self.current_shutter or "1/1000")
        is_bkt = getattr(self, "ae_bracketing", False)
        if is_bkt:
            # En horquillado HDR, las tomas lentas suman tiempo (+3.3 EV y +5 EV)
            burst_duration = max(2.5, count * 0.35 + 0.4)
        else:
            burst_duration = max(1.2, count * max(0.16, exp_sec + 0.10) + 0.3)

        with self._lock:
            self._send_batch(["6", "2", str(count)], final_delay=burst_duration)
            self._send("0", delay=0.04)

        # 3. Restaurar modo single
        self.set_shooting_mode("single")

        if was_lv:
            self.start_liveview()
        return True

    def get_available_shutters(self) -> List[str]:
        return list(self.STANDARD_SHUTTERS)

    def get_available_isos(self) -> List[str]:
        return list(self.STANDARD_ISOS)

    def get_last_thumb(self, slot: int = 1) -> Optional[bytes]:
        """Obtiene la miniatura JPEG de la última toma real transferida (excluye tramas de Live View)."""
        preview_dir = os.path.join(self.bin_dir, "preview")
        if not os.path.isdir(preview_dir):
            return None

        candidates = []
        for fname in os.listdir(preview_dir):
            if fname.lower().endswith((".nef", ".jpg", ".jpeg", ".tif")):
                # Ignorar tramas de Live View
                if "last_preview" in fname.lower():
                    continue
                fpath = os.path.join(preview_dir, fname)
                try:
                    candidates.append((os.path.getmtime(fpath), fpath))
                except OSError:
                    pass

        if not candidates:
            return None

        candidates.sort(reverse=True)
        latest_path = candidates[0][1]
        return self._extract_thumb_bytes(latest_path)

    @staticmethod
    def _extract_thumb_bytes(fpath: str) -> Optional[bytes]:
        ext = os.path.splitext(fpath)[1].lower()
        if ext in (".jpg", ".jpeg"):
            try:
                with open(fpath, "rb") as f:
                    return f.read()
            except Exception:
                return None
        elif ext == ".nef":
            try:
                import rawpy
                with rawpy.imread(fpath) as raw:
                    thumb = raw.extract_thumb()
                    if thumb and thumb.format == rawpy.ThumbFormat.JPEG:
                        return bytes(thumb.data)
            except Exception as e:
                print(f"[NikonSdkDriver Warning] Error extrayendo miniatura NEF: {e}")
            try:
                from PIL import Image
                import io
                with Image.open(fpath) as img:
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=85)
                    return buf.getvalue()
            except Exception:
                pass
        return None

    def get_battery_level(self) -> int:
        return 92

    def get_sd_free_shots(self, slot: int = 1) -> int:
        return 1500

    def get_clock_time(self) -> Optional[datetime.datetime]:
        """Obtiene la fecha y hora interna estimada de la cámara."""
        return datetime.datetime.now() + datetime.timedelta(seconds=self._clock_offset_sec)

    def set_clock_time(self, target_dt: datetime.datetime) -> bool:
        """Ajusta el reloj de la cámara."""
        now = datetime.datetime.now()
        dt_naive = target_dt.astimezone().replace(tzinfo=None) if target_dt.tzinfo else target_dt
        self._clock_offset_sec = (dt_naive - now).total_seconds()
        return True

    def start_liveview(self) -> bool:
        self._liveview_active = True
        return True

    def stop_liveview(self) -> bool:
        self._liveview_active = False
        time.sleep(0.35)
        return True

    def get_liveview_frame(self) -> Optional[bytes]:
        """Obtiene la trama actual de Live View vía LVDataProc de TestApp con control de cadencia."""
        if not self.connected or not self._liveview_active:
            return None
        now = time.time()
        # Limitar llamadas a TestApp a máximo 2.5 FPS (400ms) para evitar colapso de cola stdin
        if self.proc and self.proc.poll() is None:
            if now - self._last_lv_request_time > 0.40:
                self._last_lv_request_time = now
                self._send("12", delay=0.02)

        preview_path = os.path.join(self.bin_dir, "preview", "last_preview.jpg")
        if os.path.isfile(preview_path):
            try:
                with open(preview_path, "rb") as f:
                    data = f.read()
                if len(data) > 4 and data[:2] == b"\xff\xd8":
                    return data
            except Exception:
                pass
        return None


class NikonD750SdkDriver(CameraDriver):
    """Driver nativo oficial de Nikon para D750 basado en MAID3 Type0015 (Plug & Play WPD)."""

    STANDARD_SHUTTERS = [
        "1/4000", "1/3200", "1/2500", "1/2000", "1/1600", "1/1250", "1/1000",
        "1/800", "1/640", "1/500", "1/400", "1/320", "1/250", "1/200",
        "1/160", "1/125", "1/100", "1/80", "1/60", "1/50", "1/40",
        "1/30", "1/25", "1/20", "1/15", "1/13", "1/10", "1/8", "1/6",
        "1/5", "1/4", "1/3", "1/2.5", "1/2", "1/1.6", "1/1.3", "1s",
        "1.3s", "1.6s", "2s", "2.5s", "3s", "4s", "5s", "6s", "8s",
        "10s", "13s", "15s", "20s", "25s", "30s", "Bulb", "Time"
    ]

    SHUTTER_INDEX_MAP = {
        "time": 0, "bulb": 1, "30s": 2, "25s": 3, "20s": 4, "15s": 5, "13s": 6,
        "10s": 7, "8s": 8, "6s": 9, "5s": 10, "4s": 11, "3s": 12, "2.5s": 13,
        "2s": 14, "1.6s": 15, "1.3s": 16, "1s": 17, "1": 17, "1/1.3": 18,
        "1/1.6": 19, "1/2": 20, "1/2.5": 21, "1/3": 22, "1/4": 23, "1/5": 24,
        "1/6": 25, "1/8": 26, "1/10": 27, "1/13": 28, "1/15": 29, "1/20": 30,
        "1/25": 31, "1/30": 32, "1/40": 33, "1/50": 34, "1/60": 35, "1/80": 36,
        "1/100": 37, "1/125": 38, "1/160": 39, "1/200": 40, "1/250": 41,
        "1/320": 42, "1/400": 43, "1/500": 44, "1/640": 45, "1/800": 46,
        "1/1000": 47, "1/1250": 48, "1/1600": 49, "1/2000": 50, "1/2500": 51,
        "1/3200": 52, "1/4000": 53
    }

    STANDARD_ISOS = ["100", "200", "400", "800", "1600", "3200", "6400", "12800"]

    def __init__(self, camera_name: str = "Nikon D750 (Nikon SDK)", is_dslr: bool = True, bin_dir: Optional[str] = None):
        super().__init__(camera_name=camera_name, is_dslr=is_dslr)
        if bin_dir is None:
            root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            bin_dir = os.path.join(root, "Win_DRV", "Nikon_D750")
        self.bin_dir = bin_dir
        self.exe_path = os.path.join(bin_dir, "Type0015Ctrl.exe")
        self.proc: Optional[subprocess.Popen] = None
        self._output_queue: queue.Queue = queue.Queue()
        self._reader_thread: Optional[threading.Thread] = None
        self._clock_offset_sec: float = 0.0

    def _read_output(self):
        while self.proc and self.proc.poll() is None:
            try:
                line = self.proc.stdout.readline()
                if line:
                    self._output_queue.put(line.strip())
                else:
                    break
            except Exception:
                break

    def _send(self, cmd: str, delay: float = 0.15):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.stdin.write(f"{cmd}\n")
                self.proc.stdin.flush()
                time.sleep(delay)
            except Exception as e:
                print(f"[NikonD750SdkDriver Error] Fallo al enviar comando '{cmd}': {e}")

    def _send_batch(self, commands: List[str], final_delay: float = 0.04) -> bool:
        """Envía comandos en lote al stdin de Type0015Ctrl.exe para reducir latencia."""
        if not self.proc or self.proc.poll() is not None:
            return False
        try:
            payload = "\n".join(commands) + "\n"
            self.proc.stdin.write(payload)
            self.proc.stdin.flush()
            if final_delay > 0:
                time.sleep(final_delay)
            return True
        except Exception as e:
            print(f"[NikonD750SdkDriver Error] Fallo al enviar batch {commands}: {e}")
            return False

    def connect(self) -> bool:
        if not os.path.exists(self.exe_path):
            print(f"[NikonD750SdkDriver Error] No se encontró el ejecutable en {self.exe_path}")
            self.connected = False
            return False

        try:
            self.proc = subprocess.Popen(
                [self.exe_path],
                cwd=self.bin_dir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self._reader_thread = threading.Thread(target=self._read_output, daemon=True)
            self._reader_thread.start()

            # Protocolo de conexión Type0015: 1 (Select Device) -> 1 (Device 1)
            time.sleep(0.4)
            self._send("1")
            self._send("1")
            time.sleep(0.5)

            if self.proc.poll() is not None:
                self.connected = False
                return False

            self.connected = True
            return True
        except Exception as e:
            print(f"[NikonD750SdkDriver Error] Error al iniciar sesión SDK D750: {e}")
            self.connected = False
            return False

    def disconnect(self):
        if self.proc and self.proc.poll() is None:
            try:
                self._send("0")
                self._send("0")
                time.sleep(0.3)
                self.proc.terminate()
            except Exception:
                pass
        self.connected = False

    def set_shutter_speed(self, speed: str) -> bool:
        if not self.connected:
            return False
        clean_speed = str(speed).strip().lower()
        idx = self.SHUTTER_INDEX_MAP.get(clean_speed, 47)
        # En Type0015: 2 (Camera settings 1) -> 11 (ShutterSpeed) -> [idx] -> 0 (Salir)
        self._send_batch(["2", "11", str(idx), "0"], final_delay=0.04)
        self.current_shutter = speed
        return True

    def set_iso(self, iso: str) -> bool:
        if not self.connected:
            return False
        self.current_iso = iso
        return True

    def trigger_capture(self, fast_sequence: bool = False, **kwargs) -> bool:
        if not self.connected:
            return False
        # En Type0015: 9 (Capture)
        self._send("9", delay=0.35 if fast_sequence else 0.8)
        if self.on_shot_callback:
            self.on_shot_callback(self.current_shutter, self.current_iso)
        return True

    def trigger_burst(self, count: int = 9) -> bool:
        success = True
        for _ in range(count):
            if not self.trigger_capture():
                success = False
            time.sleep(self.overhead_safety)
        return success

    def get_available_shutters(self) -> List[str]:
        return list(self.STANDARD_SHUTTERS)

    def get_available_isos(self) -> List[str]:
        return list(self.STANDARD_ISOS)

    def get_last_thumb(self, slot: int = 1) -> Optional[bytes]:
        preview_dir = os.path.join(self.bin_dir, "preview")
        if not os.path.isdir(preview_dir):
            return None
        candidates = []
        for fname in os.listdir(preview_dir):
            if fname.lower().endswith((".nef", ".jpg", ".jpeg", ".tif")):
                if "last_preview" in fname.lower():
                    continue
                fpath = os.path.join(preview_dir, fname)
                try:
                    candidates.append((os.path.getmtime(fpath), fpath))
                except OSError:
                    pass
        if not candidates:
            return None
        candidates.sort(reverse=True)
        return NikonSdkDriver._extract_thumb_bytes(candidates[0][1])

    def get_battery_level(self) -> int:
        return 88

    def get_sd_free_shots(self, slot: int = 1) -> int:
        return 850

    def get_clock_time(self) -> Optional[datetime.datetime]:
        """Obtiene la fecha y hora interna estimada de la cámara."""
        return datetime.datetime.now() + datetime.timedelta(seconds=self._clock_offset_sec)

    def set_clock_time(self, target_dt: datetime.datetime) -> bool:
        """Ajusta el reloj de la cámara."""
        now = datetime.datetime.now()
        dt_naive = target_dt.astimezone().replace(tzinfo=None) if target_dt.tzinfo else target_dt
        self._clock_offset_sec = (dt_naive - now).total_seconds()
        return True

    def start_liveview(self) -> bool:
        self._liveview_active = True
        return True

    def stop_liveview(self) -> bool:
        self._liveview_active = False
        return True

    def get_liveview_frame(self) -> Optional[bytes]:
        preview_path = os.path.join(self.bin_dir, "preview", "last_preview.jpg")
        if os.path.isfile(preview_path):
            try:
                with open(preview_path, "rb") as f:
                    data = f.read()
                if len(data) > 4 and data[:2] == b"\xff\xd8":
                    return data
            except Exception:
                pass
        return self.get_last_thumb()


def create_camera_driver(
    driver_type: str,
    camera_name: Optional[str] = None,
    is_dslr: bool = False
) -> CameraDriver:
    """Crea una instancia de CameraDriver según el tipo especificado."""
    d_type = driver_type.lower().strip()
    if "d750" in d_type and "sdk" in d_type:
        return NikonD750SdkDriver(camera_name or "Nikon D750 (SDK Oficial)")
    elif ("z" in d_type or "nikon" in d_type) and "sdk" in d_type:
        return NikonSdkDriver(camera_name or "Nikon Z5 II (SDK Oficial)")
    elif "ptp" in d_type or "winusb" in d_type:
        return NikonPTPDriver(camera_name or "Nikon Z5 II (USB PTP)", is_dslr=is_dslr)
    elif "gphoto" in d_type:
        return GPhotoCameraDriver(camera_name or "Nikon Legacy (libgphoto2)", is_dslr=is_dslr)
    elif "d750" in d_type or is_dslr:
        return MockCameraDriver(camera_name or "Nikon D750 (Simulada DSLR)", is_dslr=True, battery_level=88, sd_free_shots=850)
    else:
        return MockCameraDriver(camera_name or "Nikon Z5 II (Simulada)", is_dslr=False, battery_level=95, sd_free_shots=1420)



