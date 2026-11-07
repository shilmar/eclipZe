"""
Núcleo Despachador Multi-Cámara y Árbitro de Prioridad para eclipZe v2.0.
Orquesta simultáneamente dos cuerpos fotográficos (Ranura A y Ranura B)
resolviendo empates temporales (|ΔT| < 25 ms) mediante micro-escalonamiento (+30 ms).
"""

import time
import threading
from typing import Optional, Dict, Any, Tuple
from .camera import CameraDriver


class PriorityArbiter:
    """
    Árbitro de Prioridad para la resolución determinista de colisiones en bus USB.
    Regla:
      - Si |T_A - T_B| < 25 ms:
          Cámara Master ejecuta en T_0 (+0 ms).
          Cámara Secundaria sufre micro-escalonamiento (+30 ms).
    """

    def __init__(
        self,
        master_slot: str = "A",
        tie_threshold_ms: float = 25.0,
        stagger_delay_ms: float = 30.0
    ):
        self.master_slot: str = master_slot.upper()
        self.tie_threshold_s: float = tie_threshold_ms / 1000.0
        self.stagger_delay_s: float = stagger_delay_ms / 1000.0

    def set_master(self, slot: str):
        """Designa la ranura con prioridad absoluta ('A' o 'B')."""
        clean_slot = slot.upper().strip()
        if clean_slot not in ("A", "B"):
            raise ValueError(f"Ranura inválida: {slot}. Debe ser 'A' o 'B'.")
        self.master_slot = clean_slot

    def is_master(self, slot: str) -> bool:
        return self.master_slot == slot.upper().strip()

    def resolve_collision(
        self,
        time_a: float,
        time_b: float
    ) -> Tuple[float, float, bool]:
        """
        Calcula tiempos de ejecución deterministas para A y B.
        Retorna: (t_a_efectivo, t_b_efectivo, colision_detectada)
        """
        delta = abs(time_a - time_b)
        if delta < self.tie_threshold_s:
            if self.master_slot == "A":
                eff_a = time_a
                eff_b = max(time_b, time_a) + self.stagger_delay_s
            else:
                eff_b = time_b
                eff_a = max(time_a, time_b) + self.stagger_delay_s
            return eff_a, eff_b, True
        return time_a, time_b, False


class MultiCameraDispatcher:
    """
    Despachador para orquestar 2 instancias de CameraDriver (Ranura A y Ranura B).
    Soporta hardware real y modo dual simulado.
    """

    def __init__(
        self,
        driver_a: Optional[CameraDriver] = None,
        driver_b: Optional[CameraDriver] = None,
        master_slot: str = "A",
        tie_threshold_ms: float = 25.0,
        stagger_delay_ms: float = 30.0
    ):
        self.driver_a: Optional[CameraDriver] = driver_a
        self.driver_b: Optional[CameraDriver] = driver_b
        self.arbiter = PriorityArbiter(
            master_slot=master_slot,
            tie_threshold_ms=tie_threshold_ms,
            stagger_delay_ms=stagger_delay_ms
        )
        self.execution_log: list[dict] = []
        self._lock = threading.Lock()

    def set_driver(self, slot: str, driver: Optional[CameraDriver]):
        clean = slot.upper().strip()
        if clean == "A":
            self.driver_a = driver
        elif clean == "B":
            self.driver_b = driver
        else:
            raise ValueError(f"Ranura desconocida: {slot}")

    def get_driver(self, slot: str) -> Optional[CameraDriver]:
        clean = slot.upper().strip()
        if clean == "A":
            return self.driver_a
        elif clean == "B":
            return self.driver_b
        return None

    def get_master_driver(self) -> Optional[CameraDriver]:
        return self.get_driver(self.arbiter.master_slot)

    def get_secondary_driver(self) -> Optional[CameraDriver]:
        sec_slot = "B" if self.arbiter.master_slot == "A" else "A"
        return self.get_driver(sec_slot)

    def set_master_slot(self, slot: str):
        self.arbiter.set_master(slot)

    def get_available_shutters(self, slot: str = "A") -> list:
        """Devuelve las velocidades disponibles del controlador solicitado o master."""
        drv = self.get_driver(slot) or self.get_master_driver()
        if drv and hasattr(drv, "get_available_shutters"):
            return drv.get_available_shutters()
        return ["1/8000", "1/4000", "1/2000", "1/1000", "1/500", "1/250", "1/125", "1/60", "1/30", "1/15", "1/8", "1/4", "1/2", "1s", "2s"]

    @property
    def overhead_safety(self) -> float:
        master = self.get_master_driver()
        return getattr(master, "overhead_safety", 0.06)

    def connect_all(self) -> Dict[str, bool]:
        """Conecta ambos controladores."""
        res = {"A": False, "B": False}
        if self.driver_a:
            res["A"] = self.driver_a.connect()
        if self.driver_b:
            res["B"] = self.driver_b.connect()
        return res

    def disconnect_all(self):
        """Desconecta ambos controladores de forma segura."""
        if self.driver_a and self.driver_a.connected:
            self.driver_a.disconnect()
        if self.driver_b and self.driver_b.connected:
            self.driver_b.disconnect()

    def trigger_capture(self) -> bool:
        """Disparo individual delegado en la cámara con prioridad Master."""
        m = self.get_master_driver()
        return m.trigger_capture() if m else False

    def trigger_burst(self, count: int = 9) -> bool:
        """Ráfaga delegada en la cámara con prioridad Master."""
        m = self.get_master_driver()
        return m.trigger_burst(count) if m else False

    def set_shooting_mode(self, mode: str = "single") -> bool:
        """Configura el modo de disparo en el controlador Master."""
        m = self.get_master_driver()
        if m and hasattr(m, "set_shooting_mode"):
            return m.set_shooting_mode(mode)
        return True

    def set_continuous_shooting_num(self, count: int = 1) -> bool:
        """Configura el número límite de ráfaga en el controlador Master."""
        m = self.get_master_driver()
        if m and hasattr(m, "set_continuous_shooting_num"):
            return m.set_continuous_shooting_num(count)
        return True

    def set_ae_bracketing(self, enable: bool = True, count: int = 9, step_index: int = 4) -> bool:
        """Configura AE Bracketing en el controlador Master."""
        m = self.get_master_driver()
        if m and hasattr(m, "set_ae_bracketing"):
            return m.set_ae_bracketing(enable, count=count, step_index=step_index)
        return True

    def set_silent_mode(self, enable: bool = True) -> bool:
        """Propaga el modo silencioso a todas las cámaras conectadas."""
        for drv in (self.driver_a, self.driver_b):
            if drv and hasattr(drv, "set_silent_mode"):
                drv.set_silent_mode(enable)
        return True

    def stop_liveview(self) -> bool:
        """Detiene Live View en todas las cámaras activas para liberar ancho de banda USB."""
        for drv in (self.driver_a, self.driver_b):
            if drv and hasattr(drv, "stop_liveview"):
                drv.stop_liveview()
        return True

    def is_liveview_active(self) -> bool:
        """Comprueba si alguna de las cámaras tiene Live View activo."""
        for drv in (self.driver_a, self.driver_b):
            if drv and hasattr(drv, "is_liveview_active") and drv.is_liveview_active():
                return True
        return False

    def trigger_single(
        self,
        slot: str,
        shutter: Optional[str] = None,
        iso: Optional[str] = None
    ) -> bool:
        """Disparo manual individual en la ranura indicada."""
        driver = self.get_driver(slot)
        if not driver:
            return False
        if not driver.connected:
            if not driver.connect():
                return False
        if shutter:
            driver.set_shutter_speed(shutter)
        if iso:
            driver.set_iso(iso)
        return driver.trigger_capture()

    def trigger_dual_simultaneous(
        self,
        shutter_a: Optional[str] = None,
        iso_a: Optional[str] = None,
        shutter_b: Optional[str] = None,
        iso_b: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta un disparo simultáneo en ambas ranuras con arbitraje de colisión:
        - Cámara Master ejecuta inmediatamente en T_0.
        - Cámara Secundaria se ejecuta tras micro-escalonamiento (+30 ms).
        """
        with self._lock:
            t0 = time.time()
            master_slot = self.arbiter.master_slot
            slave_slot = "B" if master_slot == "A" else "A"

            master_driver = self.get_driver(master_slot)
            slave_driver = self.get_driver(slave_slot)

            shutter_m = shutter_a if master_slot == "A" else shutter_b
            iso_m = iso_a if master_slot == "A" else iso_b
            shutter_s = shutter_b if master_slot == "A" else shutter_a
            iso_s = iso_b if master_slot == "A" else iso_a

            report = {
                "t0": t0,
                "master_slot": master_slot,
                "slave_slot": slave_slot,
                "master_success": False,
                "slave_success": False,
                "master_timestamp": 0.0,
                "slave_timestamp": 0.0,
                "delta_ms": 0.0,
                "stagger_applied_ms": self.arbiter.stagger_delay_s * 1000.0,
                "collision_resolved": True
            }

            # 1. Cámara Master dispara en T_0
            if master_driver and master_driver.connected:
                if shutter_m:
                    master_driver.set_shutter_speed(shutter_m)
                if iso_m:
                    master_driver.set_iso(iso_m)
                report["master_timestamp"] = time.time()
                report["master_success"] = master_driver.trigger_capture()

            # 2. Micro-escalonamiento para evitar contención USB (solo si la secundaria está activa)
            if slave_driver and slave_driver.connected:
                time.sleep(self.arbiter.stagger_delay_s)

                # 3. Cámara Secundaria dispara en T_0 + 30ms
                if shutter_s:
                    slave_driver.set_shutter_speed(shutter_s)
                if iso_s:
                    slave_driver.set_iso(iso_s)
                report["slave_timestamp"] = time.time()
                report["slave_success"] = slave_driver.trigger_capture()

            if report["master_timestamp"] > 0 and report["slave_timestamp"] > 0:
                report["delta_ms"] = (report["slave_timestamp"] - report["master_timestamp"]) * 1000.0

            self.execution_log.append(report)
            return report
