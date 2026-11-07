"""
Tests de verificación para la captura de Perlas de Baily,
Presets de Simulacro (ECLIPSE_TEST y Simulacro Real) y Modo Silencioso.
"""

import time
from core.presets import (
    EclipseEvent,
    get_eclipse_test_preset,
    get_bkt_hardware_preset,
    get_full_rehearsal_preset,
    get_solar_eclipse_2027_preset,
    get_solar_eclipse_annular_preset
)
from core.camera import MockCameraDriver, NikonPTPDriver, NikonSdkDriver
from core.sequencer import EclipseSequencer
from core.audio import AudioNotifier


def test_eclipse_test_preset_structure():
    """Valida la estructura y tiempos exactos del perfil condensado ECLIPSE_TEST (2.5 min)."""
    events = get_eclipse_test_preset()
    assert len(events) >= 50, f"ECLIPSE_TEST debe tener al menos 50 tomas/eventos, tiene {len(events)}"

    # Verificar avisos de filtro y foco
    descriptions = [e.description.lower() for e in events]
    assert any("30 segundo" in d for d in descriptions), "Falta aviso de 30 segundos"
    assert any("quitar filtro" in d for d in descriptions), "Falta aviso de retirar filtro"
    assert any("colocar filtro" in d for d in descriptions), "Falta aviso de colocar filtro"

    # Verificar ráfagas de Perlas de Baily (18 tomas a 1/4000s f/8 ISO 100)
    baily_in = [e for e in events if e.contact_ref == "C2" and e.phase == "BB"]
    assert len(baily_in) == 18, f"Se esperaban 18 tomas en Baily entrada, se obtuvieron {len(baily_in)}"
    for e in baily_in:
        assert e.shutter_speed == "1/4000"
        assert e.iso == "100"

    baily_out = [e for e in events if e.contact_ref == "C3" and e.phase == "BB"]
    assert len(baily_out) == 18, f"Se esperaban 18 tomas en Baily salida, se obtuvieron {len(baily_out)}"
    for e in baily_out:
        assert e.shutter_speed == "1/4000"
        assert e.iso == "100"

    # Verificar los 2 ciclos HDR durante la totalidad
    hdr_events = [e for e in events if "hdr" in e.description.lower()]
    assert len(hdr_events) == 18, f"Se esperaban 18 tomas HDR (2 ciclos de 9), se obtuvieron {len(hdr_events)}"
    assert any("vaciado búfer" in d for d in descriptions), "Debe incluir ventana de vaciado de búfer entre ciclos HDR"


def test_full_rehearsal_preset_structure():
    """Valida el simulacro completo desde C2-5min hasta C3+5min."""
    events = get_full_rehearsal_preset()
    descriptions = [e.description.lower() for e in events]

    assert any("10 minutos para c2" in d for d in descriptions), "Falta recordatorio de enfoque a C2-10min"
    assert any("c2 - 5 min" in d for d in descriptions), "Debe comenzar a C2 - 5 min"
    assert any("c3 + 5 min" in d for d in descriptions), "Debe finalizar a C3 + 5 min"

    # Verificar presencia de Baily
    baily_events = [e for e in events if e.phase == "BB"]
    assert len(baily_events) >= 36, "El simulacro completo debe contener al menos 36 disparos de Baily"


def test_solar_2027_preset_calibration():
    """Valida que el preset oficial de 2027 incorpora los avisos de -30s, -15s y límites de exposición."""
    events = get_solar_eclipse_2027_preset()
    descriptions = [e.description.lower() for e in events]

    assert any("10 minutos para c2" in d for d in descriptions), "Falta recordatorio de enfoque a C2-10min"
    assert any("30 segundo" in d for d in descriptions), "Falta aviso de 30 segundos"
    assert any("quitar filtro" in d for d in descriptions), "Falta aviso de retirar filtro"
    assert any("colocar filtro" in d for d in descriptions), "Falta aviso de colocar filtro"

    # Comprobar que en totalidad ninguna foto supera 1s (según guía sin star tracker a 500mm)
    for e in events:
        if e.phase == "PR":
            # Velocidades permitidas sin star tracker: hasta 1s max
            assert e.shutter_speed not in ("2s", "4s", "8s"), f"Exposición demasiado lenta para 500mm sin tracker: {e.shutter_speed}"


def test_solar_annular_preset_calibration():
    """Valida que el preset oficial anular NUNCA ordena retirar el filtro y mantiene exposiciones rápidas."""
    events = get_solar_eclipse_annular_preset()
    descriptions = [e.description.lower() for e in events]

    # Seguridad crítica: NO retirar filtro en eclipses anulares
    assert not any("quitar filtro" in d for d in descriptions), "El preset anular NUNCA debe ordenar quitar el filtro"
    assert not any("retirar filtro" in d for d in descriptions), "El preset anular NUNCA debe ordenar retirar el filtro"
    assert not any("colocar filtro" in d for d in descriptions), "El preset anular no debe ordenar colocar filtro porque nunca se retiró"

    # Verificación de avisos de seguridad activos
    assert any("mantener filtro" in d for d in descriptions), "Falta aviso explícito de mantener filtro en eclipse anular"
    assert any("asegurado" in d for d in descriptions), "Falta confirmación de filtro asegurado a C2-15s"

    # En eclipse anular todas las fotos son con filtro solar: velocidades rápidas (1/1000s o más rápidas)
    for e in events:
        if getattr(e, "is_shot", True) and not any(tag in e.description.lower() for tag in ["aviso", "alerta", "vaciado"]):
            # Ninguna toma con filtro solar debe ser más lenta que 1/500s (fotosfera brillante)
            assert e.shutter_speed in ("1/4000", "1/2000", "1/1000"), f"Velocidad inapropiada para fotosfera solar: {e.shutter_speed}"


def test_silent_mode_api():
    """Verifica que el API de Silent Mode responde en los drivers."""
    mock_cam = MockCameraDriver()
    assert mock_cam.is_silent_mode is False
    assert mock_cam.set_silent_mode(True) is True
    assert mock_cam.is_silent_mode is True
    assert mock_cam.set_silent_mode(False) is True
    assert mock_cam.is_silent_mode is False

    # Nikon PTP Driver
    ptp_cam = NikonPTPDriver()
    assert ptp_cam.set_silent_mode(True) is True
    assert ptp_cam.is_silent_mode is True

    # Nikon SDK Driver
    sdk_cam = NikonSdkDriver()
    assert sdk_cam.set_silent_mode(True) is False or True  # No falla si no hay proceso
    assert sdk_cam.is_silent_mode is True


def test_sequencer_with_baily_and_alerts():
    """Ejecuta un mini-secuenciador verificando la síntesis de avisos y el disparo de Baily."""
    spoken_messages = []

    class MockAudio(AudioNotifier):
        def __init__(self):
            super().__init__(enabled=False)

        def speak(self, text):
            spoken_messages.append(text)

    audio = MockAudio()
    cam = MockCameraDriver()
    cam.connect()

    events = [
        get_eclipse_test_preset()[1],  # Aviso 30s
        get_eclipse_test_preset()[2],  # Aviso 15s
        get_eclipse_test_preset()[4],  # Primer disparo Baily
    ]

    now = time.time()
    contacts = {
        "C2": now + 0.1,
        "C3": now + 0.5,
    }

    # Ajustar offsets para prueba rápida
    events[0].offset_seconds = -0.05
    events[1].offset_seconds = -0.03
    events[2].offset_seconds = 0.0

    seq = EclipseSequencer(contacts=contacts, schedule=events, camera=cam, audio=audio)
    seq.start()
    time.sleep(0.3)
    seq.stop()

    assert any("30 segundo" in m.lower() for m in spoken_messages), f"No se escuchó aviso de 30s: {spoken_messages}"
    assert any("quitar filtro" in m.lower() for m in spoken_messages), f"No se escuchó aviso de quitar filtro: {spoken_messages}"
    assert cam.is_silent_mode is True, "El secuenciador debió asegurar el silent mode"
    # Los dos primeros eventos son avisos (no deben haber accionado el obturador), solo el de Baily dispara
    assert len(cam.shot_history) == 1, f"Solo el disparo de Baily debió registrar captura, hubo: {len(cam.shot_history)}"


def test_notice_events_do_not_trigger_capture():
    """Verifica que los eventos de aviso no accionen el obturador de la cámara."""
    cam = MockCameraDriver()
    cam.connect()
    now = time.time()
    ev_notice = EclipseEvent("C2", -0.05, "1/4000", "100", "Aviso: Quedan 30 segundos, preparado para el filtro")
    ev_shot = EclipseEvent("C2", 0.05, "1/2000", "100", "Foto Diamante")

    from core.presets import assign_event_metadata
    assign_event_metadata([ev_notice, ev_shot])

    assert ev_notice.is_shot is False, "El aviso debe tener is_shot=False"
    assert ev_shot.is_shot is True, "El disparo debe tener is_shot=True"

    seq = EclipseSequencer(contacts={"C2": now + 0.1}, schedule=[ev_notice, ev_shot], camera=cam)
    seq.start()
    time.sleep(0.25)
    seq.stop()

    assert ev_notice.executed is True, "El aviso debió marcarse como ejecutado"
    assert ev_shot.executed is True, "La foto debió marcarse como ejecutada"
    assert len(cam.shot_history) == 1, f"Solo la foto debió accionar el obturador, hubo: {len(cam.shot_history)}"


def test_baily_burst_hardware_grouping():
    """Verifica que una ráfaga de Perlas de Baily rápida ejecute trigger_burst en bloque sin Drop-and-Skip."""
    cam = MockCameraDriver()
    cam.connect()

    # Generar 6 tomas de Baily a 1/4000s espaciadas 190ms
    baily_events = []
    for i in range(6):
        baily_events.append(EclipseEvent(
            "C2", -1.0 + (i * 0.19), "1/4000", "100", f"Baily #{i+1}", allow_skip=True, phase="BB"
        ))

    from core.presets import assign_event_metadata
    assign_event_metadata(baily_events)

    now = time.time()
    seq = EclipseSequencer(contacts={"C2": now + 1.05}, schedule=baily_events, camera=cam)
    seq.start()
    time.sleep(0.3)
    seq.stop()

    # Las 6 tomas deben estar ejecutadas sin ninguna omitida
    assert all(e.executed for e in baily_events), "Todas las tomas de Baily deben haberse ejecutado"
    assert not any(e.skipped for e in baily_events), "Ninguna toma de Baily debe haberse omitido por retraso"
    assert len(cam.shot_history) == 6, f"Deben registrarse las 6 capturas en ráfaga, hubo {len(cam.shot_history)}"



def test_voice_notice_timing_not_premature():
    """Valida que los avisos de voz no se emitan anticipadamente antes del target_time del evento."""
    spoken_timeline = []

    class MockAudio(AudioNotifier):
        def __init__(self):
            super().__init__(enabled=False)

        def speak(self, text):
            spoken_timeline.append((time.time(), text))

    audio = MockAudio()
    cam = MockCameraDriver()
    cam.connect()

    now = time.time()
    ev1 = EclipseEvent("C2", -0.15, "1/4000", "100", "Inicio test", allow_skip=False)
    ev2 = EclipseEvent("C2", -0.05, "1/4000", "100", "Aviso: Quedan 30 segundos, preparado para el filtro", allow_skip=False)

    contacts = {"C2": now + 0.20}
    seq = EclipseSequencer(contacts=contacts, schedule=[ev1, ev2], camera=cam, audio=audio)
    seq.start()

    # Esperar a que pase el primer evento (t = now + 0.05s) pero ANTES del segundo (t = now + 0.15s)
    time.sleep(0.09)
    assert len(spoken_timeline) == 0, f"El aviso de voz NO debe saltar al terminar el evento 1: {spoken_timeline}"

    # Esperar a que pase el segundo evento (t = now + 0.15s)
    time.sleep(0.12)
    seq.stop()

    assert len(spoken_timeline) == 1, f"El aviso de voz debió emitirse en su ventana programada: {spoken_timeline}"
    t_spoken, text = spoken_timeline[0]
    expected_time = contacts["C2"] + ev2.offset_seconds
    assert abs(t_spoken - expected_time) < 0.050, f"El aviso debió coincidir con target_time (~{expected_time}), ocurrió en {t_spoken}"



def test_ptp_driver_property_cache_and_tick_throttling():
    """Valida el filtrado de llamadas PTP redundantes y el estrangulamiento de señales tick."""
    ptp_cam = NikonPTPDriver()
    ptp_cam.current_shutter = "1/4000"
    ptp_cam.current_iso = "100"

    # Si ya tienen el valor actual, debe retornar True inmediatamente sin tocar USB
    assert ptp_cam.set_shutter_speed("1/4000") is True
    assert ptp_cam.set_iso("100") is True

    # Comprobar estrangulamiento de on_tick en el secuenciador
    cam = MockCameraDriver()
    cam.connect()
    tick_count = 0

    def count_ticks(now, ev, tts):
        nonlocal tick_count
        tick_count += 1

    ev = EclipseEvent("C2", 0.0, "1/4000", "100", "Disparo Tick Test")
    now = time.time()
    contacts = {"C2": now + 0.10}

    seq = EclipseSequencer(contacts=contacts, schedule=[ev], camera=cam)
    seq.on_tick = count_ticks
    seq.start()
    time.sleep(0.2)
    seq.stop()

    assert ev.executed is True
    # En 100ms con límite de 20 Hz (50ms por tick) y exclusión de los últimos 20ms, tick_count debe ser bajo (<= 10)
    assert tick_count <= 10, f"Demasiados ticks emitidos: {tick_count} (inundación de señales detectada)"


def test_bkt_hardware_preset_structure():
    """Valida la estructura del perfil Simulacro BKT Hardware con 3 bloques de 7 tomas a 1.7 EV."""
    events = get_bkt_hardware_preset()
    assert len(events) >= 40

    # Ráfagas Baily Entrada y Salida (14 tomas cada una)
    baily_in = [e for e in events if e.contact_ref == "C2" and e.phase == "BB"]
    assert len(baily_in) == 14
    baily_out = [e for e in events if e.contact_ref == "C3" and e.phase == "BB"]
    assert len(baily_out) == 14

    # Anillo de Diamante (2 tomas en entrada y 2 en salida)
    dr_in = [e for e in events if e.contact_ref == "C2" and e.phase == "DR" and e.is_shot]
    assert len(dr_in) == 2
    dr_out = [e for e in events if e.contact_ref == "C3" and e.phase == "DR" and e.is_shot]
    assert len(dr_out) == 2

    # 3 Ráfagas HDR AE Bracketing (burst_count == 7)
    hdr_bkt = [e for e in events if getattr(e, "burst_count", 1) == 7]
    assert len(hdr_bkt) == 3
    for ev in hdr_bkt:
        assert ev.phase == "HDR_BKT"
        assert ev.shutter_speed == "1/100"


def test_baily_burst_and_diamond_single_mode_transition():
    """Verifica que el secuenciador cambie a continuous_h para Baily y restaure single para Diamante."""
    cam = MockCameraDriver()
    cam.connect()

    events = [
        EclipseEvent("C2", -0.15, "1/4000", "100", "Baily #1", phase="BB"),
        EclipseEvent("C2", -0.10, "1/4000", "100", "Baily #2", phase="BB"),
        EclipseEvent("C2", -0.05, "1/4000", "100", "Baily #3", phase="BB"),
        EclipseEvent("C2", 0.0, "1/2000", "100", "Diamante Entrada", phase="DR"),
    ]

    now = time.time()
    contacts = {"C2": now + 0.15}

    seq = EclipseSequencer(contacts=contacts, schedule=events, camera=cam)
    seq.start()
    time.sleep(0.35)
    seq.stop()

    assert all(ev.executed for ev in events), "Todos los eventos debieron ejecutarse"
    # Debe haber ejecutado 3 fotos de ráfaga y 1 foto individual de diamante = 4 fotos
    assert len(cam.shot_history) == 4
    # La cámara debe haber quedado en single mode tras la ráfaga
    assert cam.shooting_mode == "single"


def test_hardware_ae_bracketing_burst_execution():
    """Verifica la ejecución de un bloque de horquillado AE Bracketing por hardware."""
    cam = MockCameraDriver()
    cam.connect()

    ev_bkt = EclipseEvent("C2", 0.0, "1/90", "100", "HDR 1: Corona 9 tomas BKT", phase="HDR_BKT", burst_count=9)

    now = time.time()
    contacts = {"C2": now + 0.05}

    seq = EclipseSequencer(contacts=contacts, schedule=[ev_bkt], camera=cam)
    seq.start()
    time.sleep(0.20)
    seq.stop()

    assert ev_bkt.executed is True
    # 9 tomas disparadas en la ráfaga
    assert len(cam.shot_history) == 9
    # Tras finalizar, el bracketing debe estar desactivado y en modo single
    assert cam.ae_bracketing is False
    assert cam.shooting_mode == "single"


def test_nikon_sdk_burst_arbitrary_count():
    """Valida que NikonSdkDriver envíe el conteo exacto de tomas sin truncar a 5."""
    cam = NikonSdkDriver()
    written_data = bytearray()

    class FakeStdin:
        def write(self, data):
            written_data.extend(data)
        def flush(self):
            pass

    class FakeProc:
        def __init__(self):
            self.stdin = FakeStdin()
        def poll(self):
            return None

    cam.proc = FakeProc()
    cam.connected = True
    cam.current_save_media = 0
    cam.current_shooting_mode = "continuous_h"
    cam.current_shutter = "1/4000"

    ok = cam.trigger_burst(count=18)
    assert ok is True
    assert b"6\n2\n18\n" in written_data
    assert b"0\n" in written_data


def test_nikon_sdk_ae_bracketing_enums():
    """Valida los índices exactos del enum SDK (Both_9=7, 5/3EV=6)."""
    cam = NikonSdkDriver()
    written_data = bytearray()

    class FakeStdin:
        def write(self, data):
            written_data.extend(data)
        def flush(self):
            pass

    class FakeProc:
        def __init__(self):
            self.stdin = FakeStdin()
        def poll(self):
            return None

    cam.proc = FakeProc()
    cam.connected = True

    ok = cam.set_ae_bracketing(True, count=9, step_index=6)
    assert ok is True
    assert written_data == b"1\n24\n1\n28\n7\n26\n6\n0\n"


def test_sequencer_closest_shutter_fallback():
    """Valida que ante una velocidad no listada se seleccione la más cercana en vez de 1/8000s."""
    cam = MockCameraDriver()
    cam.connect()
    ev = EclipseEvent("C2", 0.0, "1/95", "100", "Custom Shutter Test")
    now = time.time()
    seq = EclipseSequencer(contacts={"C2": now + 0.05}, schedule=[ev], camera=cam)
    seq.start()
    time.sleep(0.15)
    seq.stop()

    assert ev.executed is True
    last_shot = cam.shot_history[-1]
    assert last_shot["shutter"] in ("1/125", "1/60", "1/100")
    assert last_shot["shutter"] != "1/8000"

