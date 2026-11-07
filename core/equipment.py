"""
Gestor de Equipamiento y Detección Plug & Play para eclipZe v2.0.
Inventario en caliente de dispositivos USB Nikon (Vendor ID 0x04B0) y
asignación de ranuras ópticas (Ranura A y Ranura B) con telemetría.
"""

import sys
import re
import time
import datetime
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple

from .camera import (
    CameraDriver, MockCameraDriver, NikonSdkDriver,
    NikonD750SdkDriver, NikonPTPDriver, GPhotoCameraDriver,
    create_camera_driver
)
from .dispatcher import MultiCameraDispatcher


# Mapeo de PIDs conocidos de Nikon USB a nombres comerciales
NIKON_PID_MAP: Dict[int, tuple[str, str]] = {
    0x0438: ("Nikon D750", "nikon_d750_sdk"),
    0x0450: ("Nikon Z5 II", "nikon_z_sdk"),
    0x0456: ("Nikon Z5 II", "nikon_z_sdk"),
    0x0446: ("Nikon Z5", "nikon_z_sdk"),
    0x0448: ("Nikon Z6 II", "nikon_z_sdk"),
    0x0449: ("Nikon Z7 II", "nikon_z_sdk"),
    0x044E: ("Nikon Z8", "nikon_z_sdk"),
    0x044C: ("Nikon Z9", "nikon_z_sdk"),
    0x044F: ("Nikon Zf", "nikon_z_sdk"),
    0x0440: ("Nikon Z6", "nikon_z_sdk"),
    0x0441: ("Nikon Z7", "nikon_z_sdk"),
    0x0442: ("Nikon Z50", "nikon_z_sdk"),
    0x043A: ("Nikon D850", "nikon_d750_sdk"),
    0x0435: ("Nikon D810", "nikon_d750_sdk"),
    0x0447: ("Nikon D780", "nikon_d750_sdk"),
}


@dataclass
class DiscoveredCamera:
    """Información de hardware de una cámara detectada en el bus USB."""
    vendor_id: int
    product_id: int
    model_name: str
    serial_number: str = "Desconocido"
    port_path: str = "USB"
    driver_type: str = "nikon_z_sdk"

    @property
    def display_name(self) -> str:
        sn = f" [SN: {self.serial_number}]" if self.serial_number and self.serial_number != "Desconocido" else ""
        return f"{self.model_name}{sn} - {self.port_path}"


@dataclass
class CameraSlot:
    """Ranura óptica individual (Ranura A o B) con su telemetría y driver asignado."""
    slot_id: str                              # "A" o "B"
    role_name: str                            # "Cámara A (Principal)" / "Cámara B (Secundaria)"
    optical_setup: str                        # Ej: "Telescopio ED80 600mm f/7.5"
    driver: Optional[CameraDriver] = None
    status: str = "Desconectada"               # "Conectada", "Desconectada", "Error", "Liberada"
    battery_level: int = 100
    sd_free_shots: int = 1000
    is_priority_master: bool = False
    assigned_device: Optional[DiscoveredCamera] = None
    enabled: bool = True
    clock_time_str: str = "--:--:--"
    clock_delta_sec: float = 0.0
    clock_sync_status: str = "unknown"        # "synced", "drift", "desynced", "unknown"
    last_clock_sync_time: float = 0.0


class EquipmentManager:
    """
    Gestor de inventario PnP y configuración multi-cámara para eclipZe v2.0.
    """

    def __init__(self):
        # Ranura A: Por defecto Rol Principal / Telescopio (Master)
        self.slot_a = CameraSlot(
            slot_id="A",
            role_name="Cámara A (Principal / Telescopio)",
            optical_setup="Telescopio ED80 600mm f/7.5",
            is_priority_master=True
        )
        # Ranura B: Por defecto Rol Secundario / Gran Angular (Slave)
        self.slot_b = CameraSlot(
            slot_id="B",
            role_name="Cámara B (Secundaria / Contexto)",
            optical_setup="Nikkor 24-70mm @ 24mm f/5.6",
            is_priority_master=False
        )

        self.dispatcher = MultiCameraDispatcher(
            master_slot="A",
            tie_threshold_ms=25.0,
            stagger_delay_ms=30.0
        )
        self.discovered_devices: List[DiscoveredCamera] = []

        # Inicialización por defecto en modo simulado para desarrollo
        self.assign_camera("A", "mock_z", camera_name="Nikon Z5 II (Simulada)")
        self.assign_camera("B", "mock_d750", camera_name="Nikon D750 (Simulada DSLR)")

    def scan_usb_devices(self) -> List[DiscoveredCamera]:
        """
        Escanea el bus USB buscando dispositivos Nikon (Vendor ID 0x04B0).
        Utiliza libusb y, en Windows, consulta además las entidades PnP del sistema.
        """
        found: List[DiscoveredCamera] = []
        seen_keys = set()

        # 1. Escaneo nativo con libusb
        try:
            import libusb_package
            import usb.core
            import usb.util

            backend = libusb_package.get_libusb1_backend()
            usb_devs = list(usb.core.find(find_all=True, idVendor=0x04B0, backend=backend) or [])
            for dev in usb_devs:
                pid = getattr(dev, "idProduct", 0)
                sn = "Desconocido"
                try:
                    sn = usb.util.get_string(dev, dev.iSerialNumber) or "Desconocido"
                except Exception:
                    pass

                model_info = NIKON_PID_MAP.get(pid)
                if model_info:
                    model_name, driver_type = model_info
                else:
                    try:
                        p_str = usb.util.get_string(dev, dev.iProduct)
                        model_name = p_str if p_str else f"Nikon USB (0x{pid:04X})"
                    except Exception:
                        model_name = f"Nikon USB (0x{pid:04X})"
                    driver_type = "ptp"

                key = (pid, sn)
                if key not in seen_keys:
                    seen_keys.add(key)
                    found.append(DiscoveredCamera(
                        vendor_id=0x04B0,
                        product_id=pid,
                        model_name=model_name,
                        serial_number=sn,
                        port_path=f"USB Bus {getattr(dev, 'bus', 1)} Dev {getattr(dev, 'address', 1)}",
                        driver_type=driver_type
                    ))
        except Exception:
            pass

        # 2. En Windows, consultar PnP (detecta cámaras controladas por WPD / Nikon SDK)
        if sys.platform == "win32":
            try:
                cmd = 'Get-PnpDevice -PresentOnly | Where-Object { $_.InstanceId -match "VID_04B0" } | Select-Object InstanceId, FriendlyName'
                res = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", cmd],
                    capture_output=True, text=True, timeout=3
                )
                if res.returncode == 0 and res.stdout:
                    for line in res.stdout.splitlines():
                        match = re.search(r"VID_04B0&PID_([0-9A-Fa-f]{4})(?:\\([^\s]+))?", line)
                        if match:
                            pid = int(match.group(1), 16)
                            sn = match.group(2) if match.group(2) else "Desconocido"
                            key = (pid, sn)
                            if key not in seen_keys:
                                seen_keys.add(key)
                                model_info = NIKON_PID_MAP.get(pid)
                                model_name = model_info[0] if model_info else f"Nikon Camera (PID 0x{pid:04X})"
                                driver_type = model_info[1] if model_info else "ptp"
                                found.append(DiscoveredCamera(
                                    vendor_id=0x04B0,
                                    product_id=pid,
                                    model_name=model_name,
                                    serial_number=sn,
                                    port_path="PnP WPD",
                                    driver_type=driver_type
                                ))
            except Exception:
                pass

        self.discovered_devices = found
        return found

    def get_slot(self, slot_id: str) -> CameraSlot:
        clean = slot_id.upper().strip()
        if clean == "A":
            return self.slot_a
        elif clean == "B":
            return self.slot_b
        raise ValueError(f"Ranura desconocida: {slot_id}")

    def assign_camera(
        self,
        slot_id: str,
        driver_type: str,
        camera_name: Optional[str] = None,
        discovered_dev: Optional[DiscoveredCamera] = None
    ) -> bool:
        """Asigna e inicializa un controlador de cámara en la ranura indicada."""
        slot = self.get_slot(slot_id)

        # Desconectar driver previo si existía
        if slot.driver and slot.driver.connected:
            slot.driver.disconnect()

        is_dslr = "d750" in driver_type.lower() or (discovered_dev and "d750" in discovered_dev.model_name.lower())
        driver = create_camera_driver(
            driver_type=driver_type,
            camera_name=camera_name or (discovered_dev.display_name if discovered_dev else None),
            is_dslr=is_dslr
        )

        ok = driver.connect()
        slot.driver = driver
        slot.assigned_device = discovered_dev
        slot.status = "Conectada" if ok else "Error de Conexión"
        slot.battery_level = driver.get_battery_level()
        slot.sd_free_shots = driver.get_sd_free_shots()

        self.dispatcher.set_driver(slot.slot_id, driver)
        return ok

    def set_slot_enabled(self, slot_id: str, enabled: bool):
        """Habilita o deshabilita la ranura óptica indicada."""
        slot = self.get_slot(slot_id)
        slot.enabled = enabled
        if not enabled:
            if slot.driver and slot.driver.connected:
                slot.driver.disconnect()
            slot.status = "Deshabilitada"
            self.dispatcher.set_driver(slot_id, None)
            if slot.is_priority_master and slot_id.upper().strip() == "B":
                self.set_priority_master("A")
        else:
            slot.status = "Desconectada"
            if slot.driver:
                self.dispatcher.set_driver(slot_id, slot.driver)
                if slot.driver.connect():
                    slot.status = "Conectada"

    def set_priority_master(self, slot_id: str):
        """Define qué ranura tiene prioridad Master en empates temporales."""
        clean = slot_id.upper().strip()
        if clean not in ("A", "B"):
            raise ValueError(f"Ranura inválida: {slot_id}")
        self.slot_a.is_priority_master = (clean == "A")
        self.slot_b.is_priority_master = (clean == "B")
        self.dispatcher.set_master_slot(clean)

    def test_shot(self, slot_id: str) -> bool:
        """Disparo manual de prueba en la ranura seleccionada."""
        slot = self.get_slot(slot_id)
        if not slot.enabled or not slot.driver:
            return False
        success = self.dispatcher.trigger_single(slot_id)
        if success:
            slot.status = "Conectada"
            slot.battery_level = slot.driver.get_battery_level()
            slot.sd_free_shots = slot.driver.get_sd_free_shots()
        return success

    def release_camera_controls(self):
        """Libera la sesión PTP/SDK en las cámaras activas para desbloquear pantalla y menús."""
        if self.slot_a.driver and self.slot_a.driver.connected:
            self.slot_a.driver.disconnect()
            self.slot_a.status = "Liberada (Manual)"
        if self.slot_b.enabled and self.slot_b.driver and self.slot_b.driver.connected:
            self.slot_b.driver.disconnect()
            self.slot_b.status = "Liberada (Manual)"
        elif not self.slot_b.enabled:
            self.slot_b.status = "Deshabilitada"

    def reconnect_camera_controls(self):
        """Restablece la sesión de control en las cámaras activas."""
        if self.slot_a.driver:
            self.slot_a.status = "Conectada" if self.slot_a.driver.connect() else "Error"
            self.slot_a.battery_level = self.slot_a.driver.get_battery_level()
            self.slot_a.sd_free_shots = self.slot_a.driver.get_sd_free_shots()

        if self.slot_b.enabled and self.slot_b.driver:
            self.slot_b.status = "Conectada" if self.slot_b.driver.connect() else "Error"
            self.slot_b.battery_level = self.slot_b.driver.get_battery_level()
            self.slot_b.sd_free_shots = self.slot_b.driver.get_sd_free_shots()
        elif not self.slot_b.enabled:
            self.slot_b.status = "Deshabilitada"

    def get_telemetry(self, slot_id: str) -> Dict[str, Any]:
        """Obtiene la telemetría actual de la ranura."""
        slot = self.get_slot(slot_id)
        if not slot.enabled:
            cam_name = "Deshabilitada"
            status = "Deshabilitada"
            battery = 0
            sd_shots = 0
        else:
            cam_name = slot.driver.camera_name if slot.driver else "Sin Cámara"
            status = slot.status
            battery = slot.battery_level
            sd_shots = slot.sd_free_shots
        return {
            "slot_id": slot.slot_id,
            "role_name": slot.role_name,
            "optical_setup": slot.optical_setup,
            "status": status,
            "battery_level": battery,
            "sd_free_shots": sd_shots,
            "is_priority_master": slot.is_priority_master,
            "camera_name": cam_name,
            "enabled": slot.enabled,
            "clock_time_str": slot.clock_time_str,
            "clock_delta_sec": slot.clock_delta_sec,
            "clock_sync_status": slot.clock_sync_status,
            "last_clock_sync_time": slot.last_clock_sync_time
        }

    def read_camera_clock(self, slot_id: str, gps_data: Optional[Any] = None) -> Dict[str, Any]:
        """
        Lee el reloj interno de la cámara en la ranura indicada y calcula la desviación temporal.
        Tiene en cuenta si la cámara almacena hora local o UTC.
        """
        slot = self.get_slot(slot_id)
        if not slot.enabled or not slot.driver or not slot.driver.connected:
            return {"ok": False, "error": "Cámara no conectada"}

        cam_dt = slot.driver.get_clock_time()
        if cam_dt is None:
            return {"ok": False, "error": "No se pudo leer el reloj de la cámara"}

        now_local = datetime.datetime.now()
        now_utc = datetime.datetime.now(datetime.timezone.utc)

        gps_offset = gps_data.clock_offset_seconds if (gps_data and getattr(gps_data, "has_fix", False)) else 0.0
        ref_local = now_local + datetime.timedelta(seconds=gps_offset)
        ref_utc = (gps_data.utc_time if (gps_data and getattr(gps_data, "has_fix", False) and getattr(gps_data, "utc_time", None))
                   else (now_utc + datetime.timedelta(seconds=gps_offset)))

        cam_dt_naive = cam_dt.replace(tzinfo=None) if cam_dt.tzinfo else cam_dt
        ref_local_naive = ref_local.replace(tzinfo=None)
        ref_utc_naive = ref_utc.replace(tzinfo=None)

        delta_local = (cam_dt_naive - ref_local_naive).total_seconds()
        delta_utc = (cam_dt_naive - ref_utc_naive).total_seconds()

        is_camera_utc = False
        is_tz_mismatch = False

        if abs(delta_utc) < 60 and abs(delta_local) >= 1800:
            is_camera_utc = True
            delta = delta_utc
        else:
            delta = delta_local
            if abs(abs(delta_utc) - 3600) < 60 or abs(abs(delta_utc) - 7200) < 60:
                is_tz_mismatch = True

        slot.clock_time_str = cam_dt.strftime("%H:%M:%S")
        slot.clock_delta_sec = delta

        if abs(delta) < 0.25:
            slot.clock_sync_status = "synced"
        elif abs(delta) <= 2.0:
            slot.clock_sync_status = "drift"
        else:
            slot.clock_sync_status = "desynced"

        return {
            "ok": True,
            "clock_str": slot.clock_time_str,
            "delta_sec": delta,
            "status": slot.clock_sync_status,
            "is_camera_utc": is_camera_utc,
            "tz_mismatch": is_tz_mismatch,
            "has_gps_fix": bool(gps_data and getattr(gps_data, "has_fix", False))
        }

    def sync_camera_clock(
        self,
        slot_id: str,
        gps_data: Optional[Any] = None,
        use_utc: bool = False
    ) -> Tuple[bool, str, float]:
        """
        Sincroniza el reloj interno de la cámara con el GPS (o reloj de sistema).
        use_utc = False: Aplica hora local con exactitud GPS (recomendado para menú Nikon).
        use_utc = True: Aplica hora satelital UTC pura.
        Retorna (éxito, mensaje, desfase_previo).
        """
        slot = self.get_slot(slot_id)
        if not slot.enabled or not slot.driver or not slot.driver.connected:
            return False, "Cámara no conectada", 0.0

        read_res = self.read_camera_clock(slot_id, gps_data)
        prev_delta = read_res.get("delta_sec", 0.0) if read_res.get("ok") else 0.0

        now_local = datetime.datetime.now()
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        has_fix = bool(gps_data and getattr(gps_data, "has_fix", False))
        gps_offset = gps_data.clock_offset_seconds if has_fix else 0.0

        if use_utc:
            ref_dt = (gps_data.utc_time if (has_fix and getattr(gps_data, "utc_time", None))
                      else (now_utc + datetime.timedelta(seconds=gps_offset)))
            target_dt = ref_dt.replace(tzinfo=None)
        else:
            ref_dt = now_local + datetime.timedelta(seconds=gps_offset)
            target_dt = ref_dt.replace(tzinfo=None)

        # Compensación de latencia de bus USB (~25 ms)
        target_dt += datetime.timedelta(milliseconds=25)

        success = slot.driver.set_clock_time(target_dt)
        if success:
            slot.clock_delta_sec = 0.0
            slot.clock_sync_status = "synced"
            slot.last_clock_sync_time = time.time()
            slot.clock_time_str = target_dt.strftime("%H:%M:%S")
            mode_lbl = "UTC Satelital" if use_utc else ("Hora Local (GPS)" if has_fix else "Hora Local (PC)")
            return True, f"Reloj calibrado con {mode_lbl} (Desfase previo: {prev_delta:+.2f}s)", prev_delta
        else:
            return False, "Fallo al escribir en el RTC de la cámara", prev_delta

    def sync_all_cameras(
        self,
        gps_data: Optional[Any] = None,
        use_utc: bool = False
    ) -> Dict[str, Tuple[bool, str, float]]:
        """Sincroniza todas las cámaras activas (Ranura A y B)."""
        results = {}
        for slot_id in ("A", "B"):
            slot = self.get_slot(slot_id)
            if slot.enabled and slot.driver and slot.driver.connected:
                results[slot_id] = self.sync_camera_clock(slot_id, gps_data, use_utc)
        return results
