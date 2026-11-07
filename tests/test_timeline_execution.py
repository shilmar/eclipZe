"""
Tests unitarios para la Fase 3 de eclipZe v2.0:
1. Timeline Gráfico Vectorial (EclipseTimelineWidget): cálculo de coordenadas, pistas duales A y B, playhead y renderizado.
2. Log de Ejecución y Telemetría de Jitter (ExecutionLogWidget): cálculo de desfase milimétrico, colores de umbral y badges.
3. Banner NEXT Dinámico (NextBannerWidget): cuenta atrás en milisegundos y umbrales de proximidad de color.
4. Integración en MainWindow: señales del secuenciador, actualización simultánea de timeline, log y banner.
"""

import os
import sys
import time
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Asegurar path raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QPainter, QColor

from core.presets import (
    EclipseEvent,
    get_quick_rehearsal_preset,
    get_solar_eclipse_2027_preset,
    assign_event_metadata
)
from ui.timeline_widget import EclipseTimelineWidget, PHASE_COLORS, STATUS_COLORS
from ui.execution_log import (
    ExecutionLogWidget,
    calculate_jitter_ms,
    get_jitter_color,
    format_timestamp_ms
)
from ui.next_banner import (
    NextBannerWidget,
    format_countdown_ms,
    get_proximity_color
)
from ui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    """Instancia global de QApplication para tests Qt headless."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_timeline_coordinates_and_zoom(qapp):
    """Valida el cálculo de coordenadas de tiempo a píxeles en Vista Completa y Zoom Totalidad."""
    widget = EclipseTimelineWidget()
    widget.resize(1000, 200)

    contacts = {
        "C1": 1000.0,
        "C2": 1100.0,
        "MAX": 1150.0,
        "C3": 1200.0,
        "C4": 1300.0
    }
    widget.set_contacts(contacts)

    # 1. Modo Vista Completa (C1 a C4)
    widget.set_zoom_mode("full")
    assert widget.zoom_mode == "full"
    assert widget.t_start <= 1000.0
    assert widget.t_end >= 1300.0

    x_c1 = widget.time_to_x(widget.t_start)
    x_c4 = widget.time_to_x(widget.t_end)
    assert x_c1 == pytest.approx(widget.margin_left, abs=0.5)
    usable_w = widget.width() - widget.margin_left - widget.margin_right
    assert x_c4 == pytest.approx(widget.margin_left + usable_w, abs=0.5)

    # Prueba de biyección: time_to_x -> x_to_time
    test_time = 1150.0
    calc_x = widget.time_to_x(test_time)
    reconstructed_t = widget.x_to_time(calc_x)
    assert reconstructed_t == pytest.approx(test_time, abs=0.01)

    # 2. Modo Zoom Totalidad (C2 - 60s a C3 + 60s)
    widget.set_zoom_mode("totality")
    assert widget.zoom_mode == "totality"
    expected_start = 1100.0 - 60.0  # 1040.0
    expected_end = 1200.0 + 60.0    # 1260.0
    assert widget.t_start == pytest.approx(expected_start)
    assert widget.t_end == pytest.approx(expected_end)

    x_start = widget.time_to_x(expected_start)
    x_end = widget.time_to_x(expected_end)
    assert x_start == pytest.approx(widget.margin_left, abs=0.5)
    assert x_end == pytest.approx(widget.margin_left + usable_w, abs=0.5)

    # Botón de alternancia de zoom
    widget.toggle_zoom()
    assert widget.zoom_mode == "full"
    widget.toggle_zoom()
    assert widget.zoom_mode == "totality"


def test_timeline_dual_camera_tracks_and_rendering(qapp):
    """Valida la separación de disparos en Pista A y Pista B y renderizado QPainter."""
    widget = EclipseTimelineWidget()
    widget.resize(1000, 200)

    contacts = {
        "C1": 1000.0,
        "C2": 1100.0,
        "MAX": 1150.0,
        "C3": 1200.0,
        "C4": 1300.0
    }

    events = [
        EclipseEvent("C2", -4.0, "1/4000", "100", "Baily Beads A", camera_slot="A", event_id="L01", phase="BB"),
        EclipseEvent("C2", -3.5, "1/2000", "200", "Paisaje Umbra B", camera_slot="B", event_id="L02", phase="BB"),
        EclipseEvent("C2", +2.0, "1/1000", "100", "Corona Interna A", camera_slot="A", event_id="L03", phase="PR"),
        EclipseEvent("C2", +2.5, "1/500",  "200", "Paisaje Totalidad B", camera_slot="B", event_id="L04", phase="PR"),
    ]

    widget.set_events(events, contacts)

    assert len(widget.events_a) == 2, "La Pista Superior debe contener exactamente 2 eventos de Cámara A"
    assert len(widget.events_b) == 2, "La Pista Inferior debe contener exactamente 2 eventos de Cámara B"

    # Verificar actualización de estados
    widget.update_event_status("L01", "executed")
    widget.update_event_status("L02", "skipped")
    assert widget.events_a[0]["status"] == "executed"
    assert widget.events_b[0]["status"] == "skipped"

    # Renderizado gráfico vectorial sobre un QPixmap offscreen (sin errores ni cuelgues)
    pixmap = QPixmap(1000, 200)
    widget.render(pixmap)
    assert not pixmap.isNull(), "El renderizado vectorial con QPainter debe generar un pixmap válido"


def test_timeline_playhead_animation(qapp):
    """Verifica el movimiento e interpolación suave del playhead animado a 30 FPS."""
    widget = EclipseTimelineWidget()
    contacts = {"C2": 1000.0, "C3": 1100.0}
    widget.set_contacts(contacts)

    widget.set_playhead_time(1000.0)
    assert widget.current_playhead_time == 1000.0

    # Iniciar animación y verificar que el timer está activo
    widget.start_animation(base_wall_time=1000.0)
    assert widget._is_animating is True
    assert widget._timer.isActive() is True

    # Simular paso de tiempo
    widget._perf_base -= 0.100  # 100 ms transcurridos
    widget._on_playhead_tick()
    assert widget.current_playhead_time >= 1000.090, "El Playhead debe avanzar con time.perf_counter()"

    widget.stop_animation()
    assert widget._is_animating is False
    assert not widget._timer.isActive()


def test_execution_log_jitter_and_colors(qapp):
    """Verifica el cálculo de jitter en milisegundos, los colores de umbral y badges de cámara."""
    # 1. Función matemática directa de jitter
    t_sched = 1730000000.000
    t_real_ok = 1730000000.004   # +4 ms
    t_real_warn = 1730000000.035 # +35 ms
    t_real_crit = 1730000000.082 # +82 ms

    j_ok = calculate_jitter_ms(t_sched, t_real_ok)
    j_warn = calculate_jitter_ms(t_sched, t_real_warn)
    j_crit = calculate_jitter_ms(t_sched, t_real_crit)

    assert j_ok == pytest.approx(4.0, abs=0.01)
    assert j_warn == pytest.approx(35.0, abs=0.01)
    assert j_crit == pytest.approx(82.0, abs=0.01)

    # 2. Umbrales de color oficiales (<15ms Verde, 15-50ms Amarillo, >50ms Rojo)
    c_ok = get_jitter_color(j_ok)
    c_warn = get_jitter_color(j_warn)
    c_crit = get_jitter_color(j_crit)

    assert c_ok.name().upper() == "#10B981", "Jitter <15ms debe ser verde #10B981"
    assert c_warn.name().upper() == "#F59E0B", "Jitter 15-50ms debe ser amarillo #F59E0B"
    assert c_crit.name().upper() == "#EF4444", "Jitter >50ms debe ser rojo #EF4444"

    # 3. Widget ExecutionLogWidget y tabla
    log_widget = ExecutionLogWidget()
    contacts = {"C2": 1000.0, "C3": 1100.0}

    events = [
        EclipseEvent("C2", -4.0, "1/4000", "100", "Baily Beads", camera_slot="A", event_id="L01", phase="BB"),
        EclipseEvent("C2", -3.5, "1/2000", "200", "Paisaje Umbra", camera_slot="B", event_id="L02", phase="BB"),
        EclipseEvent("C2", +1.0, "1/1000", "100", "Corona", camera_slot="A", event_id="L03", phase="PR"),
    ]
    log_widget.set_schedule(events, contacts)
    assert log_widget.model.rowCount() == 3

    # Registro de disparo con éxito para Cámara A
    real_t1 = 996.004  # 1000 - 4 + 0.004 -> Jitter +4ms
    log_widget.record_shot(events[0], real_t1, success=True, shutter="1/4000", iso="100", camera_slot="A")

    rec0 = log_widget.model.records[0]
    assert rec0.status == "DONE"
    assert rec0.jitter_ms == pytest.approx(4.0, abs=0.1)
    assert rec0.camera_slot == "A"

    # Registro de omisión drop-and-skip para Cámara B
    log_widget.record_skip(events[1], delay_s=0.350, camera_slot="B")
    rec1 = log_widget.model.records[1]
    assert rec1.status == "SKIPPED"
    assert rec1.jitter_ms == pytest.approx(350.0, abs=0.1)
    assert rec1.camera_slot == "B"

    # Verificar que el badge de cámara en Columna 2 se presenta correctamente
    idx_a = log_widget.model.index(0, 2)
    assert log_widget.model.data(idx_a) == "[CÁMARA A]"
    idx_b = log_widget.model.index(1, 2)
    assert log_widget.model.data(idx_b) == "[CÁMARA B]"

    # Comprobar lista de valores de jitter
    jitters = log_widget.get_jitter_values()
    assert len(jitters) == 2
    assert 4.0 in [round(j, 1) for j in jitters]


def test_next_banner_countdown_and_colors(qapp):
    """Valida la cuenta atrás granular en milisegundos y los cambios de color del banner NEXT."""
    # 1. Formateo de milisegundos T - MM:SS.mmm
    assert format_countdown_ms(15.500) == "T - 00:15.500"
    assert format_countdown_ms(8.250) == "T - 00:08.250"
    assert format_countdown_ms(1.120) == "T - 00:01.120"
    assert format_countdown_ms(0.000) == "T - 00:00.000"

    # 2. Umbrales de color de proximidad
    assert get_proximity_color(15.0) == "#38BDF8", ">10s debe ser Azul #38BDF8"
    assert get_proximity_color(10.0) == "#F59E0B", "<=10s debe ser Naranja #F59E0B"
    assert get_proximity_color(5.0) == "#F59E0B", "<=10s debe ser Naranja #F59E0B"
    assert get_proximity_color(3.0) == "#EF4444", "<=3s debe ser Rojo #EF4444"
    assert get_proximity_color(0.5) == "#EF4444", "<=3s debe ser Rojo #EF4444"

    # 3. Widget NextBannerWidget
    banner = NextBannerWidget()
    event = EclipseEvent(
        contact_ref="C2",
        offset_seconds=-4.0,
        shutter_speed="1/4000",
        iso="100",
        description="Baily Beads inicio",
        camera_slot="A",
        event_id="L25",
        aperture="f/5.6"
    )

    # Caso >10s: Azul
    banner.update_countdown(14.250, event)
    assert banner.get_countdown_text() == "T - 00:14.250"
    assert banner.current_color == "#38BDF8"
    assert "L25" in banner.get_target_text()
    assert "[CÁMARA A]" in banner.get_target_text()

    # Caso <=10s: Naranja
    banner.update_countdown(8.100, event)
    assert banner.get_countdown_text() == "T - 00:08.100"
    assert banner.current_color == "#F59E0B"

    # Caso <=3s: Rojo inminente
    banner.update_countdown(1.234, event)
    assert banner.get_countdown_text() == "T - 00:01.234"
    assert banner.current_color == "#EF4444"

    # Caso 0s / Disparando
    banner.update_countdown(0.0, event)
    assert "DISPARANDO" in banner.get_countdown_text()
    assert banner.current_color == "#EF4444"

    # Estado completado
    banner.set_finished()
    assert banner.get_countdown_text() == "COMPLETADO"
    assert banner.current_color == "#10B981"


def test_main_window_phase3_integration(qapp):
    """Verifica que MainWindow integre Timeline, ExecutionLog y Banner NEXT con las señales de disparo."""
    window = MainWindow()

    # Comprobar presencia de los 3 componentes en la pestaña de ejecución
    assert hasattr(window, "timeline_widget"), "MainWindow debe contener timeline_widget"
    assert hasattr(window, "execution_log"), "MainWindow debe contener execution_log"
    assert hasattr(window, "next_banner"), "MainWindow debe contener next_banner"
    assert window.table_events.rowCount() == 0, "Al inicio no debe haber eventos precargados"

    # Simular cambio de perfil de preset a Eclipse Solar 2027
    window._on_preset_changed("Eclipse Solar 2027 (Totalidad Cádiz / Luxor)")
    assert window.table_events.rowCount() > 0, "Tabla debe quedar poblada tras cargar perfil"
    assert len(window.current_schedule) > 10
    assert len(window.timeline_widget.events_a) > 0
    assert len(window.timeline_widget.events_b) > 0, "El preset 2027 debe incluir disparos para Cámara B"
    assert window.execution_log.model.rowCount() == len(window.current_schedule)

    # Simular señal de tick a 5.0 segundos
    test_event = window.current_schedule[0]
    window._on_tick(time.time(), test_event, 5.0)
    assert "T - 00:05.000" in window.next_banner.get_countdown_text()
    assert window.next_banner.current_color == "#F59E0B"

    # Simular disparo completado
    window._on_shot_triggered(test_event, test_event.shutter_speed, test_event.iso)
    rec0 = window.execution_log.model.records[0]
    assert rec0.status == "DONE"
    assert rec0.jitter_ms is not None

    # Simular disparo omitido (Drop-and-skip)
    test_event2 = window.current_schedule[1]
    window._on_shot_skipped(test_event2, delay=0.360)
    rec1 = window.execution_log.model.records[1]
    assert rec1.status == "SKIPPED"
    assert rec1.jitter_ms == pytest.approx(360.0, abs=1.0)

    # Cerrar ventana
    window.ui_timer.stop()
    window.close()
