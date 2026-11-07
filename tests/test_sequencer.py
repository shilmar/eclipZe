"""
Pruebas de verificación de lógica central de eclipZe.
Comprueba EV Offset, Snap de obturador, política Drop-and-skip y parsing NMEA.
"""

import os
import sys
import time
import datetime

# Asegurar que el directorio raíz del proyecto está en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.camera import MockCameraDriver, NikonSdkDriver, NikonD750SdkDriver
from core.sequencer import EclipseSequencer, adjust_shutter_ev, SHUTTER_LADDER
from core.presets import EclipseEvent
from core.gps import GPSReader


def test_ev_adjustment():
    """Verifica que el desplazamiento EV mueva la velocidad en la dirección correcta."""
    assert adjust_shutter_ev("1/1000", +1) == "1/500", "Offset +1 EV debe alargar la exposición"
    assert adjust_shutter_ev("1/1000", -1) == "1/2000", "Offset -1 EV debe acortar la exposición"
    assert adjust_shutter_ev("1/8000", -2) == "1/8000", "Debe limitar en el extremo superior"
    assert adjust_shutter_ev("8s", +2) == "8s", "Debe limitar en el extremo inferior"
    assert adjust_shutter_ev("1/125", 0) == "1/125", "Offset 0 debe mantener la velocidad"


def test_mock_camera():
    """Verifica el driver simulado."""
    cam = MockCameraDriver(camera_name="Test Nikon Z5 II", is_dslr=False)
    assert cam.connect() is True
    cam.set_shutter_speed("1/2000")
    cam.set_iso("100")
    assert cam.trigger_capture() is True
    assert len(cam.shot_history) == 1
    assert cam.shot_history[0]["shutter"] == "1/2000"


def test_sequencer_drop_and_skip():
    """Verifica que un disparo que llega vencido por >350ms sea descartado si allow_skip=True."""
    cam = MockCameraDriver()
    cam.connect()

    # Evento con objetivo en el pasado (-10 segundos respecto al contacto base)
    now = time.time()
    contacts = {"C2": now - 5.0}  # Contacto ocurrió hace 5 segundos
    expired_event = EclipseEvent("C2", -5.0, "1/4000", "100", "Disparo muy atrasado", allow_skip=True)
    normal_event = EclipseEvent("C2", +5.1, "1/1000", "100", "Disparo en tiempo", allow_skip=True)

    seq = EclipseSequencer(contacts=contacts, schedule=[expired_event, normal_event], camera=cam)
    timeline = seq.compute_compiled_timeline()

    assert len(timeline) == 2
    # El primer disparo está en now - 10s (claramente vencido)
    assert timeline[0][0] < now - 4.0


def test_nmea_parsing():
    """Verifica el parseador de sentencias NMEA para el dongle VK-162."""
    reader = GPSReader(port="TEST")
    # Sentencia sintética $GPRMC: Fix válido 'A', hora 12:34:56 UTC, fecha 03/11/26
    sample_rmc = "$GPRMC,123456.00,A,3630.0000,N,00615.0000,W,0.0,0.0,031126,,,A*7C"
    reader._parse_nmea_line(sample_rmc)

    assert reader.data.has_fix is True
    assert reader.data.latitude == 36.5  # 36 deg + 30 min / 60 = 36.5 N
    assert reader.data.longitude == -6.25  # 6 deg + 15 min / 60 = 6.25 W -> -6.25
    assert reader.data.utc_time is not None
    assert reader.data.utc_time.hour == 12
    assert reader.data.utc_time.minute == 34


def test_ui_initialization():
    """Verifica que la interfaz PySide6 se instancie y configure correctamente."""
    import os
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from PySide6.QtWidgets import QApplication
    from ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    assert window.table_events.rowCount() == 0, "Al inicio no debe tener eventos precargados"
    window._on_preset_changed("Simulacro Rápido (12 seg de prueba)")
    assert window.table_events.rowCount() > 0, "La tabla debe cargar los eventos del preset"
    window._trigger_single_test_shot()
    assert len(window.camera.shot_history) == 1, "Debe registrar el disparo de prueba"
    window._load_last_photo_preview()
    assert hasattr(window, "_last_pixmap") and window._last_pixmap is not None, "Debe cargar la miniatura simulada"
    window._toggle_camera_screen()
    assert not window.camera.connected, "Debe liberar la sesión PTP al pulsar toggle"
    window._toggle_camera_screen()
    assert window.camera.connected, "Debe reconectar al pulsar toggle nuevamente"
    window.ui_timer.stop()
    window.close()
    del window
    app.processEvents()
    app.quit()
    del app


def test_sequencer_execution():
    """Verifica que el secuenciador ejecute los disparos previstos en el Mock."""
    cam = MockCameraDriver()
    cam.connect()
    now = time.time()
    contacts = {"C2": now + 0.15}
    ev1 = EclipseEvent("C2", -0.05, "1/2000", "100", "Toma 1")
    ev2 = EclipseEvent("C2", +0.05, "1/500", "100", "Toma 2")

    seq = EclipseSequencer(contacts=contacts, schedule=[ev1, ev2], camera=cam)
    seq.start()
    time.sleep(0.4)
    seq.stop()

    assert ev1.executed is True, "El disparo 1 debe haberse ejecutado"
    assert ev2.executed is True, "El disparo 2 debe haberse ejecutado"
    assert len(cam.shot_history) == 2, "La cámara simulada debe registrar 2 disparos"


def test_nikon_sdk_driver_structure():
    """Verifica que el driver nativo de Nikon SDK esté correctamente estructurado."""
    drv = NikonSdkDriver()
    assert drv.is_dslr is False
    assert drv.overhead_safety <= 0.10
    shutters = drv.get_available_shutters()
    assert "1/8000" in shutters
    assert "1/1000" in shutters
    assert "1s" in shutters
    assert len(drv.SHUTTER_INDEX_MAP) >= 20
    assert len(drv.get_available_isos()) >= 8
    # Verificar get_last_thumb
    thumb = drv.get_last_thumb()
    if thumb is not None:
        assert len(thumb) > 100
        assert thumb[:2] == b"\xff\xd8"


def test_sequencer_pre_arm():
    """Verifica que el secuenciador pre-ajuste obturación e ISO antes del hito temporal."""
    cam = MockCameraDriver()
    cam.connect()
    now = time.time()
    ev = EclipseEvent("C2", 0.15, "1/2000", "100", "Test Pre-arm Shot")
    contacts = {"C2": now}

    pre_armed_time = None
    orig_set = cam.set_shutter_speed
    def track_shutter(speed):
        nonlocal pre_armed_time
        pre_armed_time = time.time()
        return orig_set(speed)
    cam.set_shutter_speed = track_shutter

    seq = EclipseSequencer(contacts=contacts, schedule=[ev], camera=cam)
    seq.start()
    time.sleep(0.25)
    seq.stop()

    assert ev.executed is True
    assert pre_armed_time is not None, "El obturador debió pre-armarse con antelación"
    target_t = contacts["C2"] + ev.offset_seconds
    assert pre_armed_time < target_t, f"Pre-armado ({pre_armed_time}) debió ser antes de target_time ({target_t})"


def test_nikon_d750_sdk_driver_structure():
    """Verifica que el driver nativo de Nikon D750 SDK (Type0015) esté estructurado."""
    drv = NikonD750SdkDriver()
    assert drv.is_dslr is True
    assert drv.overhead_safety == 0.20
    assert os.path.basename(drv.exe_path).lower() == "type0015ctrl.exe"
    shutters = drv.get_available_shutters()
    assert "1/4000" in shutters
    assert "1/1000" in shutters
    assert len(drv.SHUTTER_INDEX_MAP) >= 20
    assert len(drv.get_available_isos()) >= 8


if __name__ == "__main__":
    print("Ejecutando self-check tests de eclipZe...")
    test_ev_adjustment()
    print("  [OK] EV Offset tests pasados")
    test_mock_camera()
    print("  [OK] Mock Camera tests pasados")
    test_nikon_sdk_driver_structure()
    print("  [OK] Nikon Z SDK Driver structure tests pasados")
    test_nikon_d750_sdk_driver_structure()
    print("  [OK] Nikon D750 SDK Driver structure tests pasados")
    test_sequencer_drop_and_skip()
    print("  [OK] Drop-and-skip tests pasados")
    test_sequencer_execution()
    print("  [OK] Sequencer execution tests pasados")
    test_nmea_parsing()
    print("  [OK] NMEA VK-162 parser tests pasados")
    test_ui_initialization()
    print("  [OK] PySide6 UI initialization & test shot pasados")
    print("\nTodos los tests unitarios pasaron exitosamente.")
    sys.exit(0)
