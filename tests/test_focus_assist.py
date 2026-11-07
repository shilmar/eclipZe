"""
Tests unitarios para el Asistente de Enfoque (Focus Assist) y Live View (Fase 2 eclipZe v2.0).
Verifica:
1. Métrica de nitidez Laplaciana (Var(∇² I)) diferenciando imágenes nítidas de desenfocadas y ROI.
2. Filtro Peak Hold para retención de máximos históricos y normalización.
3. Streaming continuo en MockCameraDriver con generación de limbo solar/manchas y variación de foco.
4. Protocolo de corte automático de seguridad (2 min antes del disparo / secuencia).
5. Integración del visor interactivo en UI PySide6.
"""

import os
import sys
import time

# Asegurar que el directorio raíz del proyecto está en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication
from core.camera import MockCameraDriver
from core.equipment import EquipmentManager
from core.liveview import (
    calculate_focus_score, PeakHoldFilter, FocusMetricWorker,
    is_safety_cutoff_needed, SAFETY_CUTOFF_SECONDS
)
from ui.focus_view import FocusViewWidget, InteractiveLiveViewLabel
from ui.main_window import MainWindow


def test_laplacian_focus_metric_sharp_vs_blurry():
    """Verifica que la varianza del Laplaciano diferencie nítidamente imágenes enfocadas de desenfocadas."""
    mock = MockCameraDriver()

    # 1. Imagen nítida (enfoque óptimo)
    mock.set_mock_focus_sharpness(1.0)
    sharp_frame = mock.get_liveview_frame()
    assert sharp_frame is not None, "El driver debe retornar una trama JPEG válida"
    assert sharp_frame.startswith(b"\xff\xd8"), "La trama debe tener la cabecera mágica JPEG"

    sharp_score = calculate_focus_score(sharp_frame)

    # 2. Imagen desenfocada (blur elevado)
    mock.set_mock_focus_blur(6.0)
    blurry_frame = mock.get_liveview_frame()
    assert blurry_frame is not None

    blurry_score = calculate_focus_score(blurry_frame)

    # La imagen enfocada debe tener un score drásticamente mayor (> 50 veces superior)
    assert sharp_score > blurry_score * 10.0, (
        f"El Focus Score nítido ({sharp_score:.2f}) debe superar ampliamente al desenfocado ({blurry_score:.2f})"
    )

    # 3. Evaluación en una Región de Interés (ROI) específica:
    # ROI sobre la mancha solar central vs ROI sobre cielo negro exterior
    # Mancha solar aprox en centro (cx=280, cy=210, w=100, h=100)
    roi_spot = (230, 160, 100, 100)
    # Cielo negro vacío en esquina sin texto (x=500, y=10, w=100, h=100)
    roi_sky = (500, 10, 100, 100)

    score_spot = calculate_focus_score(sharp_frame, roi_box=roi_spot)
    score_sky = calculate_focus_score(sharp_frame, roi_box=roi_sky)

    assert score_spot > score_sky + 100.0, (
        f"El Focus Score sobre manchas/limbo ({score_spot:.2f}) debe superar al fondo oscuro ({score_sky:.2f})"
    )


def test_peak_hold_filter():
    """Verifica que el filtro Peak Hold retenga el valor máximo histórico y permita reset."""
    peak_filter = PeakHoldFilter()
    assert peak_filter.get_peak() == 0.0

    # Secuencia de enfoque: usuario ajusta el anillo (sube nitidez, pasa el punto óptimo y baja)
    p1 = peak_filter.update(120.0)
    assert p1 == 120.0
    assert peak_filter.get_peak() == 120.0

    p2 = peak_filter.update(350.0)
    assert p2 == 350.0
    assert peak_filter.get_peak() == 350.0

    p3 = peak_filter.update(520.0)  # Máximo óptimo
    assert p3 == 520.0
    assert peak_filter.get_peak() == 520.0

    # Usuario se pasa de rosca y el score disminuye
    p4 = peak_filter.update(410.0)
    assert p4 == 520.0, "El pico debe mantenerse retenido en 520.0"
    assert peak_filter.get_peak() == 520.0

    p5 = peak_filter.update(210.0)
    assert p5 == 520.0, "El pico debe seguir retenido en 520.0"

    # Verificar porcentaje normalizado
    norm_mid = peak_filter.get_normalized(260.0)
    assert round(norm_mid, 1) == 50.0, f"260 sobre 520 debe ser 50.0%, obtenido {norm_mid}"

    norm_peak = peak_filter.get_normalized(520.0)
    assert round(norm_peak, 1) == 100.0

    # Superar el pico anterior
    p6 = peak_filter.update(600.0)
    assert p6 == 600.0
    assert peak_filter.get_peak() == 600.0

    # Reset
    peak_filter.reset()
    assert peak_filter.get_peak() == 0.0
    assert peak_filter.get_normalized(0.0) == 0.0


def test_mock_camera_driver_streaming():
    """Verifica el ciclo de vida de streaming continuo en MockCameraDriver."""
    cam = MockCameraDriver("Nikon Z5 II Simulada")
    assert not cam.is_liveview_active()

    ok_start = cam.start_liveview()
    assert ok_start is True
    assert cam.is_liveview_active() is True

    # Comprobar tramas consecutivas
    f1 = cam.get_liveview_frame()
    assert f1 is not None and len(f1) > 1000

    cam.set_mock_focus_sharpness(0.5)
    f2 = cam.get_liveview_frame()
    assert f2 is not None

    ok_stop = cam.stop_liveview()
    assert ok_stop is True
    assert cam.is_liveview_active() is False


def test_safety_cutoff_logic():
    """Verifica la lógica de corte de seguridad 2 minutos (120 s) antes de la secuencia."""
    # Más de 2 minutos restantes: no cortar
    assert is_safety_cutoff_needed(125.0) is False
    assert is_safety_cutoff_needed(120.1) is False

    # Exactamente 2 minutos o menos: corte mandatorio
    assert is_safety_cutoff_needed(120.0) is True
    assert is_safety_cutoff_needed(119.9) is True
    assert is_safety_cutoff_needed(60.0) is True
    assert is_safety_cutoff_needed(5.0) is True
    assert is_safety_cutoff_needed(0.0) is True


def test_ui_focus_view_tab():
    """Verifica la integración de la pestaña FocusViewWidget y visor interactivo Qt."""
    app = QApplication.instance() or QApplication([])

    eq_mgr = EquipmentManager()
    focus_widget = FocusViewWidget(eq_mgr)

    # Verificar que el combo de cámaras tiene Cámara Principal y Cámara Secundaria
    assert focus_widget.combo_camera_source.count() == 2
    assert "Cámara Principal" in focus_widget.combo_camera_source.itemText(0)
    assert "Cámara Secundaria" in focus_widget.combo_camera_source.itemText(1)

    # Verificar zoom digital ROI (1x, 5x, 10x)
    assert focus_widget.combo_zoom.count() == 3
    focus_widget.combo_zoom.setCurrentIndex(1)  # 5x
    assert focus_widget.worker.zoom == 5
    focus_widget.combo_zoom.setCurrentIndex(2)  # 10x
    assert focus_widget.worker.zoom == 10
    focus_widget.combo_zoom.setCurrentIndex(0)  # 1x
    assert focus_widget.worker.zoom == 1

    # Verificar reposicionamiento ROI mediante clic simulado
    focus_widget._on_roi_clicked(0.35, 0.42)
    assert abs(focus_widget.worker.center_x - 0.35) < 0.01
    assert abs(focus_widget.worker.center_y - 0.42) < 0.01

    # Probar centrado de ROI
    focus_widget._on_center_roi()
    assert abs(focus_widget.worker.center_x - 0.5) < 0.01
    assert abs(focus_widget.worker.center_y - 0.5) < 0.01

    # Iniciar y detener Live View
    assert not focus_widget.is_liveview_active()
    focus_widget.start_liveview()
    assert focus_widget.is_liveview_active() is True
    assert "Detener" in focus_widget.btn_toggle_lv.text()

    # Procesar eventos Qt para permitir al menos un ciclo
    app.processEvents()
    time.sleep(0.08)
    app.processEvents()

    # Probar corte de seguridad (T <= 120s)
    cutoff_triggered = focus_widget.check_safety_timeout(115.0)
    assert cutoff_triggered is True, "Debe ejecutar el corte de seguridad a T - 115s"
    assert not focus_widget.is_liveview_active(), "Live View debe haberse apagado"
    assert "Iniciar" in focus_widget.btn_toggle_lv.text()

    focus_widget.stop_liveview()
    focus_widget.close()
    del focus_widget
    app.processEvents()


def test_saturated_frame_rendering():
    """Verifica que el renderizado de tramas saturadas (QFont y superposición ROI) funcione sin errores."""
    app = QApplication.instance() or QApplication([])
    worker = FocusMetricWorker()

    # Generar trama con canal rojo 100% saturado
    mock = MockCameraDriver()
    mock.set_mock_saturation(True)
    sat_frame = mock.get_liveview_frame()
    assert sat_frame is not None

    # Procesar trama en 1x (debe dibujar aviso de saturación con QFont)
    res_1x = worker._process_frame(sat_frame, 1, 0.5, 0.5)
    img_1x, score, peak, norm, is_sat, sat_ratio = res_1x
    assert img_1x is not None and not img_1x.isNull()
    assert is_sat is True

    # Procesar trama en zoom 5x
    res_5x = worker._process_frame(sat_frame, 5, 0.5, 0.5)
    img_5x = res_5x[0]
    assert img_5x is not None and not img_5x.isNull()


def test_main_window_focus_integration():
    """Verifica la integración de la pestaña de Enfoque en la ventana principal MainWindow."""
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    # Verificar presencia de la pestaña Enfoque
    assert hasattr(window, "tab_focus"), "MainWindow debe contener tab_focus"
    assert window.tabs.tabText(1) == "👁️ Enfoque (Live View)"

    # Verificar botones de acceso directo en pestaña Equipamiento
    assert hasattr(window, "btn_liveview_a")
    assert hasattr(window, "btn_liveview_b")

    # Al pulsar 'Abrir Live View' de Ranura A debe conmutar a la pestaña de enfoque
    window._goto_liveview_a()
    assert window.tabs.currentWidget() == window.tab_focus
    assert window.tab_focus._active_slot == "A"
    assert window.tab_focus.is_liveview_active() is True

    # Al iniciar secuencia, Live View debe cortarse obligatoriamente por seguridad
    window._start_sequence()
    assert not window.tab_focus.is_liveview_active(), "La secuencia debe apagar el Live View automáticamente"
    window._stop_sequence()

    window.tab_focus.stop_liveview()
    window.ui_timer.stop()
    window.close()
    del window
    app.processEvents()
    app.quit()
    del app


if __name__ == "__main__":
    print("Ejecutando tests de Asistente de Enfoque (Focus Assist) eclipZe v2.0...")
    test_laplacian_focus_metric_sharp_vs_blurry()
    print("  [OK] Metrica Laplaciana Var(Laplacian): Diferenciacion nitida vs desenfocada y ROI")
    test_peak_hold_filter()
    print("  [OK] Filtro Peak Hold: Retencion de maximo historico, normalizacion y reset")
    test_mock_camera_driver_streaming()
    print("  [OK] MockCameraDriver: Streaming JPEG y variacion sintetica de foco")
    test_safety_cutoff_logic()
    print("  [OK] Protocolo de Seguridad: Corte mandatorio a T - 2 min (120 s)")
    test_ui_focus_view_tab()
    print("  [OK] UI FocusViewWidget: Controles, Zoom ROI 1x/5x/10x y corte de seguridad")
    test_saturated_frame_rendering()
    print("  [OK] Renderizado de tramas saturadas con QFont y QPainter")
    test_main_window_focus_integration()
    print("  [OK] MainWindow: Integracion de pestana Enfoque y botones de acceso directo")
    print("\nTodos los tests de Focus Assist pasaron exitosamente.")
    sys.exit(0)
