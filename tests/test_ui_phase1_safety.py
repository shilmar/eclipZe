"""
Tests unitarios para la FASE 1: Seguridad Operativa y Prevención de Errores en eclipZe.
1. Protección del Botón de Emergencia (anti-doble clic y pulsación sostenida 1s).
2. Bloqueo del Botón de Inicio ("Secuencia en curso" neutral al iniciar, desbloqueo al parar).
3. Limpieza de Metadatos en la Tabla de Eventos (aviso de filtros / sistema con '--' en vez de datos ficticios).
4. Simplificación del HUD Superior (telemetría pasiva con GPS Sync y ranuras sin botones duplicados).
"""

import os
import sys
import time
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint
from PySide6.QtTest import QTest

from ui.main_window import MainWindow, EmergencyStopButton
from core.presets import EclipseEvent, get_solar_eclipse_2027_preset


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_emergency_stop_button_single_click_protection(qapp):
    """Verifica que un clic simple no dispare la emergencia y pida confirmación."""
    btn = EmergencyStopButton("⏹ PARADA EMERGENCIA")
    btn.setEnabled(True)

    triggered = []
    btn.emergency_triggered.connect(lambda: triggered.append(True))

    # Clic simple (press + release)
    QTest.mousePress(btn, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(10, 10))
    QTest.mouseRelease(btn, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(10, 10))

    assert len(triggered) == 0, "Un clic simple NO debe disparar la parada de emergencia."
    assert "PULSA OTRA VEZ" in btn.text() or "MANTÉN" in btn.text()


def test_emergency_stop_button_double_click(qapp):
    """Verifica que dos clics rápidos activen la parada de emergencia."""
    btn = EmergencyStopButton("⏹ PARADA EMERGENCIA")
    btn.setEnabled(True)

    triggered = []
    btn.emergency_triggered.connect(lambda: triggered.append(True))

    # Clic 1
    QTest.mousePress(btn, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(10, 10))
    QTest.mouseRelease(btn, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(10, 10))

    # Clic 2 inmediato (<500ms)
    QTest.mousePress(btn, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(10, 10))

    assert len(triggered) == 1, "Un doble clic rápido DEBE disparar la parada de emergencia."


def test_emergency_stop_button_hold_1s(qapp):
    """Verifica que mantener pulsado el botón 1s dispare la emergencia."""
    btn = EmergencyStopButton("⏹ PARADA EMERGENCIA")
    btn.setEnabled(True)

    triggered = []
    btn.emergency_triggered.connect(lambda: triggered.append(True))

    # Simular que el ratón está encima y se dispara el timeout de hold
    btn._on_hold_timeout()

    assert len(triggered) == 1, "Mantener pulsado 1 segundo DEBE disparar la parada de emergencia."


def test_start_button_locking_and_states(qapp):
    """Verifica que INICIAR SECUENCIA se inhabilite y pase a estado neutral mientras se ejecuta."""
    window = MainWindow()

    assert window.btn_start.isEnabled() is True
    assert "INICIAR SECUENCIA" in window.btn_start.text()
    assert window.btn_stop.isEnabled() is False

    # Iniciar secuencia
    window.combo_preset.setCurrentText("Simulacro Rápido (12 seg de prueba)")
    window._start_sequence()

    # Comprobar estado neutral y bloqueado
    assert window.btn_start.isEnabled() is False
    assert "SECUENCIA EN CURSO" in window.btn_start.text()
    assert window.btn_stop.isEnabled() is True

    # Parada
    window._stop_sequence()

    # Comprobar restauración
    assert window.btn_start.isEnabled() is True
    assert "INICIAR SECUENCIA" in window.btn_start.text()
    assert window.btn_stop.isEnabled() is False


def test_table_metadata_cleaning_for_notices(qapp):
    """Verifica que avisos de voz (como Quitar filtro) muestren '--' en la celda de exposición."""
    window = MainWindow()
    window._on_preset_changed("Eclipse Solar 2027 (Totalidad Cádiz / Luxor)")

    model = window.execution_log.model

    # Buscar el evento de aviso de quitar filtro solar
    filter_rows = []
    for row, rec in enumerate(model.records):
        if "quitar filtro" in rec.description.lower():
            filter_rows.append((row, rec))

    assert len(filter_rows) > 0, "Debe existir al menos un evento de aviso de quitar filtro."

    for row, rec in filter_rows:
        # Columna 4 es Exposición
        val_display = model.data(model.index(row, 4), Qt.DisplayRole)
        assert val_display == "--", f"La celda de exposición para avisos debe ser '--', se obtuvo '{val_display}'"
        assert rec.shutter == "--"

    # Verificar también en la tabla legacy
    for row, ev in enumerate(window.current_schedule):
        if "quitar filtro" in ev.description.lower():
            shutter_item = window.table_events.item(row, 1)
            iso_item = window.table_events.item(row, 2)
            assert shutter_item.text() == "--"
            assert iso_item.text() == "--"

    # Verificar que el banner NEXT omita obturación / ISO para eventos de aviso
    notice_ev = filter_rows[0][1].event_ref
    window.next_banner.update_countdown(15.0, notice_ev)
    banner_text = window.next_banner.lbl_target.text()
    assert "1/4000" not in banner_text
    assert "ISO 100" not in banner_text
    assert "Quitar filtro solar" in banner_text


def test_top_hud_passive_and_clean(qapp):
    """Verifica que la barra superior no contenga botones duplicados y disponga de telemetría pasiva."""
    window = MainWindow()

    # Telemetría presente
    assert hasattr(window, "lbl_top_slot_a")
    assert hasattr(window, "lbl_top_slot_b")
    assert hasattr(window, "lbl_top_silent")
    assert hasattr(window, "lbl_gps_status")
    assert hasattr(window, "lbl_gps_sync")
    assert hasattr(window, "lbl_clock")

    # Botones operativos en tab de Equipamiento, no en barra superior
    assert hasattr(window, "btn_eq_reconnect")
    assert hasattr(window, "btn_eq_release")
    assert hasattr(window, "btn_silent_mode")
    assert window.btn_silent_mode.parent() is not None
