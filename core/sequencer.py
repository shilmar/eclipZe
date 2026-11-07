"""
Motor de ejecución secuencial determinista para eclipZe.
Coordina el timeline relativo a contactos astronómicos, política drop-and-skip,
compensación de exposición al vuelo (EV Offset) y avisos de voz.
"""

import time
import threading
from typing import Dict, List, Optional, Callable
from .camera import CameraDriver
from .presets import EclipseEvent
from .audio import AudioNotifier


SHUTTER_LADDER = [
    "1/8000", "1/4000", "1/2000", "1/1000", "1/500", "1/250",
    "1/125", "1/60", "1/30", "1/15", "1/8", "1/4", "1/2",
    "1s", "2s", "4s", "8s"
]


def _shutter_to_seconds(shutter_str: str) -> float:
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


def adjust_shutter_ev(base_shutter: str, ev_offset: int) -> str:
    """Modifica la velocidad base N pasos EV hacia arriba (más exposición) o abajo (menos exposición)."""
    if ev_offset == 0 or base_shutter not in SHUTTER_LADDER:
        return base_shutter
    idx = SHUTTER_LADDER.index(base_shutter)
    new_idx = max(0, min(len(SHUTTER_LADDER) - 1, idx + ev_offset))
    return SHUTTER_LADDER[new_idx]


class EclipseSequencer:
    """Despachador de tiempo real para eventos de eclipse."""

    def __init__(
        self,
        contacts: Dict[str, float],
        schedule: List[EclipseEvent],
        camera: CameraDriver,
        audio: Optional[AudioNotifier] = None
    ):
        self.contacts = dict(contacts)
        self.schedule = schedule
        self.camera = camera
        self.audio = audio or AudioNotifier(enabled=True)

        self.ev_offset: int = 0
        self.is_running: bool = False
        self._stop_requested: bool = False
        self._thread: Optional[threading.Thread] = None

        # Callbacks para desacoplar de la UI
        self.on_event_triggered: Optional[Callable[[EclipseEvent, str, str], None]] = None
        self.on_event_skipped: Optional[Callable[[EclipseEvent, float], None]] = None
        self.on_tick: Optional[Callable[[float, Optional[EclipseEvent], float], None]] = None
        self.on_finished: Optional[Callable[[], None]] = None

    def set_ev_offset(self, offset: int):
        """Ajusta la compensación global EV (-3 a +3 EV) en tiempo real ante nubes o bruma."""
        self.ev_offset = max(-3, min(3, offset))

    def compute_compiled_timeline(self) -> List[tuple[float, EclipseEvent]]:
        """Compila los offsets relativos a tiempos absolutos de reloj."""
        compiled = []
        for event in self.schedule:
            slot = getattr(event, "camera_slot", "A").upper().strip()
            if slot == "B" and hasattr(self.camera, "get_driver") and self.camera.get_driver("B") is None:
                continue
            t_ref = self.contacts.get(event.contact_ref)
            if t_ref is not None:
                abs_time = t_ref + event.offset_seconds
                compiled.append((abs_time, event))
        compiled.sort(key=lambda x: x[0])
        return compiled

    def start(self):
        """Inicia la secuencia en un hilo de alta prioridad sin congelar la interfaz."""
        if self.is_running:
            return
        self.is_running = True
        self._stop_requested = False
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Detiene inmediatamente la secuencia."""
        self._stop_requested = True
        self.is_running = False
        if self._thread and self._thread.is_alive() and threading.current_thread() != self._thread:
            self._thread.join(timeout=1.0)

    def _run_loop(self):
        timeline = self.compute_compiled_timeline()
        if not timeline:
            self.is_running = False
            if self.on_finished:
                self.on_finished()
            return

        if hasattr(self.camera, "get_available_shutters"):
            available_shutters = self.camera.get_available_shutters()
        else:
            available_shutters = SHUTTER_LADDER

        # Asegurar modo silencioso antes de comenzar la secuencia
        if hasattr(self.camera, "set_silent_mode"):
            self.camera.set_silent_mode(True)

        _last_tick_time: float = 0.0
        _handled_indices: set[int] = set()

        for idx, (target_time, event) in enumerate(timeline):
            if self._stop_requested:
                break

            if idx in _handled_indices:
                continue

            desc_lower = event.description.lower()

            # Parada preventiva de Live View para despejar bus USB antes de Baily o ráfagas
            if ("live view" in desc_lower and "parada" in desc_lower) or event.phase in ("BB", "DR"):
                if hasattr(self.camera, "is_liveview_active") and self.camera.is_liveview_active():
                    self.camera.stop_liveview()

            # Pre-cálculo de parámetros efectivos y selección de driver
            effective_shutter = adjust_shutter_ev(event.shutter_speed, self.ev_offset)
            slot = getattr(event, "camera_slot", "A").upper().strip()
            driver = self.camera
            if hasattr(self.camera, "get_driver"):
                target_drv = self.camera.get_driver(slot)
                if target_drv is None and slot == "B":
                    event.skipped = True
                    if self.on_event_skipped:
                        self.on_event_skipped(event, 0.0)
                    continue
                if target_drv is not None:
                    driver = target_drv

            avail = driver.get_available_shutters() if hasattr(driver, "get_available_shutters") else available_shutters
            if effective_shutter not in avail and avail:
                target_sec = _shutter_to_seconds(effective_shutter)
                effective_shutter = min(avail, key=lambda x: abs(_shutter_to_seconds(x) - target_sec))
            effective_iso = event.iso

            _armed_shot: bool = False

            while not self._stop_requested:
                now = time.time()
                time_to_shot = target_time - now

                # Notificación periódica a la UI (máx 20 Hz, nunca en el spin-wait de 20ms)
                if self.on_tick and (now - _last_tick_time >= 0.050) and time_to_shot > 0.020:
                    _last_tick_time = now
                    self.on_tick(now, event, time_to_shot)

                # Pre-armado / Pre-staging anticipado (350ms a 40ms antes del hito)
                if not _armed_shot and getattr(event, "is_shot", True) and 0.040 < time_to_shot <= 0.350:
                    _armed_shot = True
                    if getattr(driver, "current_shutter", None) != effective_shutter:
                        driver.set_shutter_speed(effective_shutter)
                    if getattr(driver, "current_iso", None) != effective_iso:
                        driver.set_iso(effective_iso)
                    if getattr(event, "phase", "") == "BB" and hasattr(driver, "set_shooting_mode"):
                        if getattr(driver, "current_shooting_mode", None) != "continuous_h":
                            driver.set_shooting_mode("continuous_h")

                # 1. Política Drop-and-Skip: si se retrasó >350ms y admite skip, descartar
                if time_to_shot < -0.350:
                    if event.allow_skip:
                        event.skipped = True
                        if self.on_event_skipped:
                            self.on_event_skipped(event, abs(time_to_shot))
                        break
                    # Si no permite skip (ej: fotos críticas de contacto), se dispara de inmediato

                # 2. Ventana de disparo alcanzada (margen <= 12ms)
                if time_to_shot <= 0.012:
                    # Avisos de voz sincronizados exactamente con el instante programado del evento
                    if not event.executed:
                        if "enfoque" in desc_lower:
                            self.audio.speak("Atención: Comprobar y fijar enfoque en la cámara principal")
                        elif "mantener" in desc_lower or "asegurado" in desc_lower or "no retirar" in desc_lower or "no quitar" in desc_lower:
                            self.audio.speak("Atención de seguridad: Mantener filtro solar colocado")
                        elif "30 segundo" in desc_lower or "preparado" in desc_lower:
                            self.audio.speak("Quedan 30 segundos, preparado para el filtro")
                        elif "quitar" in desc_lower or "retirar" in desc_lower:
                            self.audio.speak("¡Quitar filtro solar ahora!")
                        elif "colocar" in desc_lower or "recolocar" in desc_lower or "poner" in desc_lower:
                            self.audio.speak("¡Atención: Colocar filtro solar inmediatamente!")

                    # Si es parada preventiva de Live View, ejecutarla
                    if "live view" in desc_lower and "parada" in desc_lower:
                        if hasattr(self.camera, "is_liveview_active") and self.camera.is_liveview_active():
                            self.camera.stop_liveview()

                    # Evento sin disparo fotográfico (solo aviso de voz o acción de sistema)
                    if not getattr(event, "is_shot", True):
                        # Pre-armar modo ráfaga si el siguiente evento inicia una ráfaga (ej: Baily tras parada de Live View)
                        if (idx + 1) < len(timeline):
                            next_ev = timeline[idx + 1][1]
                            if getattr(next_ev, "phase", "") == "BB":
                                if hasattr(driver, "set_shutter_speed") and getattr(driver, "current_shutter", None) != next_ev.shutter_speed:
                                    driver.set_shutter_speed(adjust_shutter_ev(next_ev.shutter_speed, self.ev_offset))
                                if hasattr(driver, "set_shooting_mode") and getattr(driver, "current_shooting_mode", None) != "continuous_h":
                                    driver.set_shooting_mode("continuous_h")

                        event.executed = True
                        event.actual_timestamp = now
                        if self.on_event_triggered:
                            self.on_event_triggered(event, event.shutter_speed, event.iso)
                        break

                    # Detectar si este evento inicia una ráfaga rápida (fase BB consecutiva con cadencia < 300ms)
                    burst_group = [event]
                    burst_indices = [idx]
                    scan = idx + 1
                    while scan < len(timeline):
                        next_t, next_ev = timeline[scan]
                        prev_t, prev_ev = timeline[scan - 1]
                        if (getattr(next_ev, "phase", "") == "BB" and getattr(prev_ev, "phase", "") == "BB" and
                            (next_t - prev_t) < 0.300 and
                            getattr(next_ev, "camera_slot", "A").upper().strip() == slot and
                            getattr(next_ev, "is_shot", True)):
                            burst_group.append(next_ev)
                            burst_indices.append(scan)
                            scan += 1
                        else:
                            break

                    if len(burst_group) > 1:
                        # Ráfaga continua por hardware en modo Continuous High (CH RAW)
                        if getattr(driver, "current_shutter", None) != effective_shutter:
                            driver.set_shutter_speed(effective_shutter)
                        if getattr(driver, "current_iso", None) != effective_iso:
                            driver.set_iso(effective_iso)

                        if hasattr(driver, "set_shooting_mode"):
                            driver.set_shooting_mode("continuous_h")
                        if hasattr(driver, "set_continuous_shooting_num"):
                            driver.set_continuous_shooting_num(len(burst_group))

                        driver.trigger_burst(count=len(burst_group))

                        # Restaurar inmediatamente a disparo único para preparar el Anillo de Diamante
                        if hasattr(driver, "set_shooting_mode"):
                            driver.set_shooting_mode("single")
                        # Pre-armar velocidad del siguiente evento (ej. Diamante a 1/2000s) durante el margen
                        scan_next = max(burst_indices) + 1
                        if scan_next < len(timeline):
                            next_ev = timeline[scan_next][1]
                            if getattr(next_ev, "phase", "") == "DR" and hasattr(driver, "set_shutter_speed"):
                                driver.set_shutter_speed(adjust_shutter_ev(next_ev.shutter_speed, self.ev_offset))

                        burst_now = time.time()
                        for b_ev in burst_group:
                            b_ev.executed = True
                            b_ev.actual_timestamp = burst_now
                            if self.on_event_triggered:
                                self.on_event_triggered(b_ev, effective_shutter, effective_iso)

                        _handled_indices.update(burst_indices)
                        overhead = getattr(driver, "overhead_safety", 0.06)
                        time.sleep(overhead)
                        break

                    # Ráfaga de Horquillado AE Bracketing por hardware (Totalidad HDR)
                    if getattr(event, "burst_count", 1) > 1:
                        b_count = event.burst_count
                        if getattr(driver, "current_shutter", None) != effective_shutter:
                            driver.set_shutter_speed(effective_shutter)
                        if getattr(driver, "current_iso", None) != effective_iso:
                            driver.set_iso(effective_iso)

                        is_bkt = getattr(event, "phase", "") in ("HDR_BKT", "BKT", "PR")
                        if is_bkt and hasattr(driver, "set_ae_bracketing"):
                            driver.set_ae_bracketing(True, count=b_count, step_index=4)  # 1.7 EV (5/3 EV, índice 4 en SDK Z5 II)
                        if hasattr(driver, "set_shooting_mode"):
                            driver.set_shooting_mode("continuous_h")
                        if hasattr(driver, "set_continuous_shooting_num"):
                            driver.set_continuous_shooting_num(b_count)

                        driver.trigger_burst(count=b_count)

                        if is_bkt and hasattr(driver, "set_ae_bracketing"):
                            time.sleep(0.30)
                            driver.set_ae_bracketing(False)
                        if hasattr(driver, "set_shooting_mode"):
                            driver.set_shooting_mode("single")

                        event.executed = True
                        event.actual_timestamp = time.time()
                        if self.on_event_triggered:
                            self.on_event_triggered(event, effective_shutter, effective_iso)

                        overhead = getattr(driver, "overhead_safety", 0.06)
                        time.sleep(overhead)
                        break

                    # Configurar y disparar cámara seleccionada solo si han cambiado
                    if getattr(driver, "current_shutter", None) != effective_shutter:
                        driver.set_shutter_speed(effective_shutter)
                    if getattr(driver, "current_iso", None) != effective_iso:
                        driver.set_iso(effective_iso)

                    event.executed = True
                    event.actual_timestamp = now

                    if self.on_event_triggered:
                        self.on_event_triggered(event, effective_shutter, effective_iso)

                    success = driver.trigger_capture()

                    # Pausa técnica de seguridad (evita colapsar búfer / espejo según cámara)
                    overhead = getattr(driver, "overhead_safety", 0.06)
                    time.sleep(overhead)
                    break

                    # Pausa técnica de seguridad (evita colapsar búfer / espejo según cámara)
                    overhead = getattr(driver, "overhead_safety", 0.06)
                    time.sleep(overhead)
                    break

                # 3. Espera granular adaptativa (mantiene CPU < 1%)
                if time_to_shot > 0.100:
                    time.sleep(0.040)
                elif time_to_shot > 0.020:
                    time.sleep(0.005)
                else:
                    # Spin-wait breve solo en los últimos 20ms para máxima precisión temporal
                    pass

        self.is_running = False
        if self.on_finished:
            self.on_finished()
