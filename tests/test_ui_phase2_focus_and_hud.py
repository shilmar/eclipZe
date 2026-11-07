"""
Tests unitarios para la Fase 2 de eclipZe v2.0:
1. Rediseño de la Barra NEXT y Contadores:
   - Tipografía HUD de gran formato para contadores de micro-acción y contactos astronómicos.
   - División visual en dos bloques:
     * Izquierda: Próxima micro-acción inminente (ej. 'T - 00:08.250' / descripción).
     * Derecha: Hito astronómico principal de referencia (ej. 'C2 EN: 00:19s', 'FIN TOTALIDAD EN: 01:45s').
2. Mejoras en la Pestaña Enfoque (Live View):
   - Mini gráfico temporal Sparkline (últimos 10s de Focus Score) mostrando la campana gaussiana.
   - Detección y aviso visual sutil en pantalla de saturación en canal rojo (picos a 255) en el ROI solar.
"""

import os
import sys
import time
import pytest
import numpy as np

os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Asegurar path raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap

from core.presets import EclipseEvent
from core.camera import MockCameraDriver
from core.equipment import EquipmentManager
from core.liveview import check_saturation, FocusMetricWorker
from ui.next_banner import NextBannerWidget, format_countdown_ms, get_proximity_color
from ui.focus_view import FocusViewWidget, FocusSparklineWidget
from ui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    """Instancia global de QApplication para tests Qt headless."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


# =========================================================================
# PARTE 1: Rediseño de la Barra NEXT y Contadores HUD
# =========================================================================

def test_next_banner_hud_typography_and_blocks(qapp):
    """Verifica la división en dos bloques y la presencia de tipografía HUD grande."""
    banner = NextBannerWidget()

    # 1. Verificar existencia de ambos bloques visuales
    assert hasattr(banner, "block_left"), "Debe existir el bloque visual izquierdo para micro-acciones"
    assert hasattr(banner, "block_right"), "Debe existir el bloque visual derecho para el hito principal"

    # Verificar componentes del bloque izquierdo
    assert banner.lbl_countdown is not None
    assert banner.lbl_target is not None
    assert banner.lbl_badge is not None

    # Verificar componentes del bloque derecho
    assert banner.lbl_milestone is not None
    assert banner.lbl_milestone_title is not None

    # 2. Verificar tipografía HUD grande (Consolas en tamaño >= 18)
    font_countdown = banner.lbl_countdown.font()
    assert font_countdown.family().lower() in ("consolas", "monospace")
    assert font_countdown.pointSize() >= 20 or font_countdown.pixelSize() >= 22
    assert font_countdown.bold() is True

    font_milestone = banner.lbl_milestone.font()
    assert font_milestone.family().lower() in ("consolas", "monospace")
    assert font_milestone.pointSize() >= 18 or font_milestone.pixelSize() >= 18
    assert font_milestone.bold() is True


def test_next_banner_milestone_relative_to_c2_and_totality(qapp):
    """Verifica que el hito astronómico de la derecha calcule correctamente C2 y FIN TOTALIDAD."""
    banner = NextBannerWidget()

    now = 10000.0
    contacts = {
        "C1": now - 300.0,
        "C2": now + 19.5,    # En 19 segundos
        "MAX": now + 60.0,
        "C3": now + 105.0,   # Fin de totalidad en 1m 45s
        "C4": now + 400.0,
    }
    banner.set_contacts(contacts)

    event_baily = EclipseEvent(
        contact_ref="C2",
        offset_seconds=-0.08,
        shutter_speed="1/4000",
        iso="100",
        description="Perlas de Baily #1",
        camera_slot="A",
        event_id="L10"
    )

    # 1. Antes de C2: El hito debe ser C2 (ej. 'C2 EN: 00:19s')
    banner.update_countdown(time_to_shot=0.08, event=event_baily, now=now, contacts=contacts)
    assert banner.get_countdown_text() == "T - 00:00.080"
    milestone_text = banner.get_milestone_text()
    assert "C2 EN:" in milestone_text
    assert "00:19s" in milestone_text or "00:20s" in milestone_text
    assert "TOTALIDAD" in banner.lbl_milestone_title.text()

    # 2. Durante la Totalidad (después de C2, antes de C3): El hito debe ser FIN TOTALIDAD (ej. 01:45s)
    now_totality = now + 20.0  # 10020.0 (C3 está en 10105.0 -> restan 85s = 01:25s)
    event_corona = EclipseEvent(
        contact_ref="C2",
        offset_seconds=+5.0,
        shutter_speed="1/15",
        iso="100",
        description="Corona Media",
        camera_slot="A",
        event_id="L15"
    )
    banner.update_countdown(time_to_shot=1.5, event=event_corona, now=now_totality, contacts=contacts)
    milestone_text = banner.get_milestone_text()
    assert "FIN TOTALIDAD EN:" in milestone_text
    assert "01:25s" in milestone_text
    assert "TOTALIDAD" in banner.lbl_milestone_title.text()


def test_next_banner_fallback_from_event(qapp):
    """Verifica que el banner calcule el hito relativo a partir del evento cuando no se pasan contactos."""
    banner = NextBannerWidget()
    event_c2 = EclipseEvent(
        contact_ref="C2",
        offset_seconds=-4.0,  # 4 segundos antes de C2
        shutter_speed="1/4000",
        iso="100",
        description="Baily beads pre-C2",
        camera_slot="A",
        event_id="L05"
    )

    # Si faltan 15s para el evento y el evento es C2 - 4s, faltan 19s para C2
    banner.update_countdown(time_to_shot=15.0, event=event_c2)
    milestone = banner.get_milestone_text()
    assert "C2 EN:" in milestone
    assert "00:19s" in milestone


# =========================================================================
# PARTE 2: Mini Gráfico Sparkline de Enfoque (10 segundos)
# =========================================================================

def test_focus_sparkline_widget_history_and_pruning(qapp):
    """Verifica que FocusSparklineWidget almacene muestras y purgue las mayores a 10s."""
    sparkline = FocusSparklineWidget(window_seconds=10.0)
    assert len(sparkline.get_samples()) == 0

    base_time = 1000.0

    # Añadir muestras simulando una campana gaussiana al girar el anillo de foco
    scores = [120.0, 240.0, 480.0, 750.0, 520.0, 310.0]
    for idx, sc in enumerate(scores):
        sparkline.add_sample(score=sc, timestamp=base_time + idx * 1.0)

    samples = sparkline.get_samples()
    assert len(samples) == 6
    assert samples[-1][1] == 310.0

    # Añadir una muestra 12 segundos después de base_time: las primeras deben purgarse
    sparkline.add_sample(score=150.0, timestamp=base_time + 12.0)
    samples_after = sparkline.get_samples()
    # Las muestras con timestamp < (base_time + 12.0 - 10.0 = base_time + 2.0) deben haber sido eliminadas
    assert len(samples_after) < 7
    assert all(t >= base_time + 2.0 for t, _ in samples_after)

    # Verificar reset
    sparkline.reset()
    assert len(sparkline.get_samples()) == 0


def test_focus_sparkline_rendering(qapp):
    """Verifica que paintEvent renderice el gráfico gaussiano vectorial sobre QPixmap sin errores."""
    sparkline = FocusSparklineWidget(window_seconds=10.0)
    sparkline.resize(200, 30)

    # Con menos de 2 muestras
    pix1 = QPixmap(200, 30)
    sparkline.render(pix1)
    assert not pix1.isNull()

    # Con suficientes muestras (campana de foco)
    t0 = time.time()
    for dt, sc in [(0.0, 50.0), (2.0, 180.0), (4.0, 600.0), (6.0, 320.0), (8.0, 90.0)]:
        sparkline.add_sample(sc, timestamp=t0 + dt)

    pix2 = QPixmap(200, 30)
    sparkline.render(pix2)
    assert not pix2.isNull()


# =========================================================================
# PARTE 3: Detección y Aviso de Saturación en Canal Rojo (255)
# =========================================================================

def test_check_saturation_clean_vs_overexposed():
    """Verifica que check_saturation detecte picos a 255 en el canal rojo."""
    # 1. Imagen no saturada (valores moderados < 250)
    clean_arr = np.full((100, 100, 3), fill_value=[50, 180, 220], dtype=np.uint8)
    is_sat, ratio = check_saturation(clean_arr)
    assert is_sat is False, "Una imagen con valor 220 no debe marcarse como saturada"
    assert ratio == 0.0

    # 2. Imagen con canal rojo saturado al 100% (> 5% píxeles a 255)
    sat_arr = clean_arr.copy()
    # Poner 1000 píxeles (10% del área 100x100) con rojo a 255
    sat_arr[:10, :, 2] = 255
    is_sat_over, ratio_over = check_saturation(sat_arr)
    assert is_sat_over is True, "Una imagen con 10% de píxeles rojos a 255 debe marcarse como saturada"
    assert ratio_over == pytest.approx(0.10, abs=0.01)

    # 3. Con ROI específico
    roi = (20, 20, 40, 40)
    sat_arr_roi = clean_arr.copy()
    # Saturar solo dentro del ROI
    sat_arr_roi[20:60, 20:60, 2] = 255
    is_sat_roi, ratio_roi = check_saturation(sat_arr_roi, roi_box=roi)
    assert is_sat_roi is True
    assert ratio_roi >= 0.95


def test_focus_view_saturation_warning_integration(qapp):
    """Verifica que FocusViewWidget active la advertencia en ámbar cuando el sensor se satura."""
    eq_mgr = EquipmentManager()
    focus_view = FocusViewWidget(eq_mgr)
    focus_view.show()

    # Inicialmente el aviso de saturación debe estar oculto
    assert hasattr(focus_view, "lbl_saturation_warning")
    assert not focus_view.lbl_saturation_warning.isVisible()
    assert focus_view.is_saturation_detected() is False

    # Disparar señal de saturación detectada
    focus_view._on_saturation_detected(True, 0.12)
    assert focus_view.is_saturation_detected() is True
    assert focus_view.lbl_saturation_warning.isVisible()
    assert "saturado" in focus_view.lbl_saturation_warning.text().lower()

    # Al normalizarse la exposición, el aviso debe ocultarse
    focus_view._on_saturation_detected(False, 0.0)
    assert focus_view.is_saturation_detected() is False
    assert not focus_view.lbl_saturation_warning.isVisible()

    focus_view.close()
    del focus_view


def test_mock_camera_saturation_switch(qapp):
    """Verifica que MockCameraDriver genere tramas saturadas al activar mock_saturation."""
    mock = MockCameraDriver()
    mock.set_mock_saturation(False)
    frame_clean = mock.get_liveview_frame()
    is_sat_clean, _ = check_saturation(frame_clean)
    assert is_sat_clean is False, "Por defecto la cámara simulada no debe estar saturada"

    mock.set_mock_saturation(True)
    frame_sat = mock.get_liveview_frame()
    is_sat_hot, ratio_hot = check_saturation(frame_sat)
    assert is_sat_hot is True, "Al activar set_mock_saturation(True) debe detectar saturación en el disco solar"
    assert ratio_hot > 0.05


def test_focus_view_lateral_layout_organization(qapp):
    """Verifica que el panel de Enfoque esté organizado lateralmente para maximizar el visor central."""
    from PySide6.QtWidgets import QHBoxLayout, QGroupBox, QFrame
    eq_mgr = EquipmentManager()
    focus_view = FocusViewWidget(eq_mgr)
    focus_view.resize(1280, 720)
    focus_view.show()

    # Comprobar la existencia del layout horizontal principal para visor y panel lateral
    root = focus_view.layout()
    assert root is not None

    # Buscar el layout horizontal contenedor
    found_h_layout = False
    for i in range(root.count()):
        item = root.itemAt(i)
        if item.layout() and isinstance(item.layout(), QHBoxLayout):
            h_layout = item.layout()
            found_h_layout = True
            # Debe contener exactamente 2 elementos principales: Visor (stretch=1) y Panel Lateral
            assert h_layout.count() == 2
            widget_left = h_layout.itemAt(0).widget()
            widget_right = h_layout.itemAt(1).widget()

            assert isinstance(widget_left, QFrame), "El visor central debe estar a la izquierda"
            assert isinstance(widget_right, QGroupBox), "La telemetría debe estar en la columna lateral"

            # El panel lateral debe tener ancho fijo dedicado
            assert widget_right.maximumWidth() <= 320
            assert widget_right.minimumWidth() >= 260
            break

    assert found_h_layout is True, "El visor y el panel de telemetría deben disponerse en un QHBoxLayout lateral"

    # Verificar que los widgets de telemetría residen dentro del panel lateral
    assert focus_view.history_graph.parent() is not None
    assert focus_view.bar_sharpness.parent() is not None
    assert focus_view.lbl_current_score.parent() is not None

    # Verificar que el visor central tiene política de expansión máxima
    assert focus_view.live_view_label.sizePolicy().horizontalPolicy().name == "Expanding"
    assert focus_view.live_view_label.sizePolicy().verticalPolicy().name == "Expanding"

    focus_view.close()
    del focus_view
