"""
Vista de Asistente de Enfoque (Focus Assist) y Visualizador Interactivo de Live View para eclipZe v2.0.
Permite inspección de alta resolución con Zoom ROI (1x, 5x, 10x), retícula astronómica,
barra de nitidez con Peak Hold histórico y corte de seguridad automático.
"""

from typing import Optional, Tuple
from collections import deque
import time

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QProgressBar, QGroupBox, QFrame, QSlider, QSizePolicy,
    QCheckBox
)
from PySide6.QtCore import Qt, Signal, QPointF, QRect
from PySide6.QtGui import (
    QFont, QPixmap, QMouseEvent, QImage, QPainter, QPen,
    QBrush, QColor, QPainterPath, QLinearGradient
)

from core.equipment import EquipmentManager
from core.camera import CameraDriver, MockCameraDriver
from core.liveview import FocusMetricWorker, is_safety_cutoff_needed, SAFETY_CUTOFF_SECONDS


class FocusSparklineWidget(QWidget):
    """
    Mini gráfico de línea temporal (sparkline) de los últimos 10 segundos del Focus Score.
    Facilita ver la campana gaussiana al girar el anillo de enfoque del telescopio
    a través del punto de máxima nitidez.
    """

    def __init__(self, parent: Optional[QWidget] = None, window_seconds: float = 10.0):
        super().__init__(parent)
        self.window_seconds: float = float(window_seconds)
        self.samples: deque[Tuple[float, float]] = deque()  # (timestamp, score)
        self.setMinimumSize(180, 26)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def add_sample(self, score: float, timestamp: Optional[float] = None):
        """Añade una muestra de nitidez y purga las muestras con más de window_seconds."""
        t = time.time() if timestamp is None else float(timestamp)
        self.samples.append((t, float(score)))
        cutoff = t - self.window_seconds
        while self.samples and self.samples[0][0] < cutoff:
            self.samples.popleft()
        self.update()

    def reset(self):
        """Limpia el búfer histórico de puntuaciones."""
        self.samples.clear()
        self.update()

    def get_samples(self) -> list[Tuple[float, float]]:
        """Retorna copia de la lista de muestras actuales."""
        return list(self.samples)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Fondo oscuro tipo HUD
        painter.fillRect(0, 0, w, h, QColor("#0F172A"))
        painter.setPen(QPen(QColor("#334155"), 1))
        painter.drawRoundedRect(0, 0, w - 1, h - 1, 4, 4)

        if len(self.samples) < 2:
            painter.setPen(QPen(QColor("#475569"), 1, Qt.DashLine))
            painter.drawLine(8, h // 2, w - 8, h // 2)
            painter.setFont(QFont("Segoe UI", 8))
            painter.setPen(QColor("#64748B"))
            painter.drawText(QRect(0, 0, w, h), Qt.AlignCenter, "Historial 10s (Esperando foco)")
            painter.end()
            return

        t_now = self.samples[-1][0]
        t_start = t_now - self.window_seconds
        scores = [s for _, s in self.samples]
        max_s = max(scores)
        min_s = min(scores)

        # Margen de escala para destacar la campana gaussiana
        scale_max = max(10.0, max_s * 1.15)
        scale_min = 0.0

        pad_x = 6
        pad_y = 4
        usable_w = max(1, w - 2 * pad_x)
        usable_h = max(1, h - 2 * pad_y)

        pts = []
        for t, s in self.samples:
            rel_t = max(0.0, min(1.0, (t - t_start) / self.window_seconds))
            rel_s = max(0.0, min(1.0, (s - scale_min) / (scale_max - scale_min)))
            px = pad_x + rel_t * usable_w
            py = pad_y + (1.0 - rel_s) * usable_h
            pts.append(QPointF(px, py))

        # Línea guía de referencia 50%
        painter.setPen(QPen(QColor("#1E293B"), 1, Qt.DotLine))
        painter.drawLine(pad_x, pad_y + usable_h // 2, pad_x + usable_w, pad_y + usable_h // 2)

        # Relleno de área bajo la curva (gradiente verde esmeralda)
        path = QPainterPath()
        bottom_y = pad_y + usable_h
        path.moveTo(pts[0].x(), bottom_y)
        for pt in pts:
            path.lineTo(pt)
        path.lineTo(pts[-1].x(), bottom_y)
        path.closeSubpath()

        gradient = QLinearGradient(0, pad_y, 0, bottom_y)
        gradient.setColorAt(0.0, QColor(16, 185, 129, 85))
        gradient.setColorAt(1.0, QColor(16, 185, 129, 5))
        painter.fillPath(path, gradient)

        # Trazado continuo de la curva de enfoque
        painter.setPen(QPen(QColor("#10B981"), 2))
        for i in range(len(pts) - 1):
            painter.drawLine(pts[i], pts[i + 1])

        # Punto brillante en la muestra más reciente
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#38BDF8"))
        painter.drawEllipse(pts[-1], 3.0, 3.0)

        # Superposición de información breve
        painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
        painter.setPen(QColor("#94A3B8"))
        painter.drawText(pad_x + 3, pad_y + 9, "10s")
        painter.setPen(QColor("#38BDF8"))
        painter.drawText(QRect(0, pad_y, w - pad_x - 3, 11), Qt.AlignRight, f"Pico: {max_s:.1f}")

        painter.end()


class InteractiveLiveViewLabel(QLabel):
    """
    Visor de imagen interactivo que captura clics del ratón para centrar
    y desplazar la Región de Interés (ROI) sobre el limbo solar o estrellas.
    """
    roi_clicked = Signal(float, float)  # Coordenadas relativas cx, cy en rango (0.0 - 1.0)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(480, 360)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self._last_pixmap: Optional[QPixmap] = None

    def set_display_pixmap(self, pixmap: QPixmap):
        self._last_pixmap = pixmap
        # Escalar manteniendo relación de aspecto sin sobrepasar el contenedor
        scaled = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._last_pixmap and not self._last_pixmap.isNull():
            scaled = self._last_pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setPixmap(scaled)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            pm = self.pixmap()
            if pm and not pm.isNull():
                lbl_w = self.width()
                lbl_h = self.height()
                pm_w = pm.width()
                pm_h = pm.height()

                # Posición de inicio del pixmap centrado dentro del QLabel
                offset_x = (lbl_w - pm_w) / 2.0
                offset_y = (lbl_h - pm_h) / 2.0

                pos = event.position()
                click_x = pos.x() - offset_x
                click_y = pos.y() - offset_y

                if 0 <= click_x <= pm_w and 0 <= click_y <= pm_h:
                    rel_x = max(0.05, min(0.95, click_x / pm_w))
                    rel_y = max(0.05, min(0.95, click_y / pm_h))
                    self.roi_clicked.emit(rel_x, rel_y)

        super().mousePressEvent(event)


class FocusViewWidget(QWidget):
    """
    Pestaña "👁️ Enfoque (Live View)" con control de streaming, selector ROI,
    métrica Laplaciana de nitidez, marcador de Peak Hold y seguridad térmica.
    """
    liveview_state_changed = Signal(bool)

    def __init__(self, equipment_manager: EquipmentManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.equipment_manager = equipment_manager
        self.worker: Optional[FocusMetricWorker] = None
        self._is_active: bool = False
        self._active_slot: str = "A"

        self._setup_ui()
        self._setup_worker()
        self.refresh_cameras()

    def _setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(10)

        # 1. Barra de Control Superior
        control_group = QGroupBox("Control de Live View & Región de Interés (ROI)")
        control_layout = QHBoxLayout(control_group)
        control_layout.setSpacing(12)

        # Selector de cámara origen (Ranura A vs Ranura B)
        control_layout.addWidget(QLabel("Cámara:"))
        self.combo_camera_source = QComboBox()
        self.combo_camera_source.currentIndexChanged.connect(self._on_camera_source_changed)
        control_layout.addWidget(self.combo_camera_source)

        # Botón de encendido / apagado de Live View
        self.btn_toggle_lv = QPushButton("▶ Iniciar Live View")
        self.btn_toggle_lv.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 7px 16px;")
        self.btn_toggle_lv.clicked.connect(self._toggle_liveview)
        control_layout.addWidget(self.btn_toggle_lv)

        control_layout.addSpacing(10)

        # Selector digital de Zoom ROI (1x, 5x, 10x)
        control_layout.addWidget(QLabel("Zoom ROI:"))
        self.combo_zoom = QComboBox()
        self.combo_zoom.addItems([
            "1x (Campo Completo)",
            "5x (Zoom Detalle)",
            "10x (Zoom Extremo Limbo)"
        ])
        self.combo_zoom.currentIndexChanged.connect(self._on_zoom_changed)
        control_layout.addWidget(self.combo_zoom)

        # Botón centrar ROI
        self.btn_center_roi = QPushButton("🎯 Centrar ROI")
        self.btn_center_roi.setToolTip("Restablece el centro del análisis al centro óptico de la imagen")
        self.btn_center_roi.clicked.connect(self._on_center_roi)
        control_layout.addWidget(self.btn_center_roi)

        # Botón reset pico
        self.btn_reset_peak = QPushButton("🔄 Reset Pico")
        self.btn_reset_peak.setToolTip("Reinicia la memoria del valor máximo de nitidez")
        self.btn_reset_peak.clicked.connect(self._on_reset_peak)
        control_layout.addWidget(self.btn_reset_peak)

        # Indicador de coordenadas ROI
        self.lbl_roi_coords = QLabel("ROI: Centro (50%, 50%)")
        self.lbl_roi_coords.setStyleSheet("color: #9CA3AF; font-size: 11px;")
        control_layout.addWidget(self.lbl_roi_coords)

        control_layout.addStretch()

        # Control interactivo de simulador (visible si la cámara es Mock)
        self.mock_focus_container = QWidget()
        mock_layout = QHBoxLayout(self.mock_focus_container)
        mock_layout.setContentsMargins(0, 0, 0, 0)
        mock_layout.addWidget(QLabel("Foco Simulado:"))
        self.slider_mock_focus = QSlider(Qt.Horizontal)
        self.slider_mock_focus.setRange(0, 100)
        self.slider_mock_focus.setValue(100)  # 100 = Foco nítido
        self.slider_mock_focus.setFixedWidth(130)
        self.slider_mock_focus.setToolTip("Simula el giro del anillo de enfoque del objetivo")
        self.slider_mock_focus.valueChanged.connect(self._on_mock_focus_slider_changed)
        mock_layout.addWidget(self.slider_mock_focus)

        self.chk_mock_saturation = QCheckBox("Simular Saturación R")
        self.chk_mock_saturation.setToolTip("Simula sobreexposición con canal rojo saturado a 255")
        self.chk_mock_saturation.toggled.connect(self._on_mock_saturation_toggled)
        mock_layout.addWidget(self.chk_mock_saturation)

        control_layout.addWidget(self.mock_focus_container)

        root_layout.addWidget(control_group)

        # 2. Contenedor Principal: Disposición Horizontal (Visor Central + Panel Lateral)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)

        # 2A. Área Central: Visor Interactivo de Live View (Máximo Espacio)
        view_frame = QFrame()
        view_frame.setStyleSheet("""
            QFrame {
                background-color: #0A0C0F;
                border: 1px solid #2D323B;
                border-radius: 6px;
            }
        """)
        view_layout = QVBoxLayout(view_frame)
        view_layout.setContentsMargins(4, 4, 4, 4)

        self.live_view_label = InteractiveLiveViewLabel()
        self.live_view_label.setText("👁️ Live View Apagado\nPulsa '▶ Iniciar Live View' para comenzar la calibración de foco.")
        self.live_view_label.setStyleSheet("color: #6B7280; font-size: 13px; font-weight: bold;")
        self.live_view_label.roi_clicked.connect(self._on_roi_clicked)
        view_layout.addWidget(self.live_view_label, stretch=1)

        # Nota al pie del visor
        lbl_hint = QLabel("💡 Haz clic con el ratón en cualquier punto de la imagen para desplazar la Región de Interés (ROI).")
        lbl_hint.setStyleSheet("color: #64748B; font-size: 11px; padding-left: 6px;")
        view_layout.addWidget(lbl_hint)

        content_layout.addWidget(view_frame, stretch=1)

        # 2B. Panel Lateral Dedicado: Telemetría de Nitidez y Foco (Columna Derecha)
        metric_group = QGroupBox("Telemetría de Enfoque (Focus Assist)")
        metric_group.setFixedWidth(295)
        metric_layout = QVBoxLayout(metric_group)
        metric_layout.setContentsMargins(10, 10, 10, 10)
        metric_layout.setSpacing(8)

        # Badge de estado centrado
        self.lbl_focus_badge = QLabel("● LIVE VIEW INACTIVO")
        self.lbl_focus_badge.setAlignment(Qt.AlignCenter)
        self.lbl_focus_badge.setStyleSheet(
            "background-color: #1F2937; color: #9CA3AF; font-weight: bold; padding: 5px 10px; border-radius: 4px;"
        )
        metric_layout.addWidget(self.lbl_focus_badge)

        # Bloque de valores numéricos de nitidez
        scores_frame = QFrame()
        scores_frame.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #1F2937;
                border-radius: 6px;
            }
        """)
        scores_layout = QVBoxLayout(scores_frame)
        scores_layout.setContentsMargins(10, 8, 10, 8)
        scores_layout.setSpacing(6)

        self.lbl_current_score = QLabel("Score Actual: 0.0")
        self.lbl_current_score.setFont(QFont("Consolas", 15, QFont.Bold))
        self.lbl_current_score.setStyleSheet("color: #E2E8F0;")
        scores_layout.addWidget(self.lbl_current_score)

        self.lbl_peak_score = QLabel("Pico Máximo (Peak Hold): 0.0")
        self.lbl_peak_score.setFont(QFont("Consolas", 13, QFont.Bold))
        self.lbl_peak_score.setStyleSheet("color: #38BDF8;")
        scores_layout.addWidget(self.lbl_peak_score)

        self.lbl_efficiency = QLabel("Eficiencia: 0.0%")
        self.lbl_efficiency.setFont(QFont("Consolas", 13, QFont.Bold))
        self.lbl_efficiency.setStyleSheet("color: #9CA3AF;")
        scores_layout.addWidget(self.lbl_efficiency)

        metric_layout.addWidget(scores_frame)

        # Barra visual de nitidez (0-100%)
        lbl_bar_title = QLabel("Nitidez Relativa al Pico:")
        lbl_bar_title.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: bold; margin-top: 2px;")
        metric_layout.addWidget(lbl_bar_title)

        self.bar_sharpness = QProgressBar()
        self.bar_sharpness.setRange(0, 100)
        self.bar_sharpness.setValue(0)
        self.bar_sharpness.setFixedHeight(24)
        self.bar_sharpness.setTextVisible(True)
        self.bar_sharpness.setFormat("%p% (Óptimo: 100%)")
        self.bar_sharpness.setStyleSheet("""
            QProgressBar {
                border: 1px solid #374151;
                border-radius: 4px;
                background-color: #111827;
                text-align: center;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background-color: #10B981;
                border-radius: 3px;
            }
        """)
        metric_layout.addWidget(self.bar_sharpness)

        # Título y Mini gráfico temporal Sparkline (últimos 10s de campana gaussiana)
        lbl_graph_title = QLabel("Curva Gaussiana de Enfoque (10s):")
        lbl_graph_title.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: bold; margin-top: 4px;")
        metric_layout.addWidget(lbl_graph_title)

        self.history_graph = FocusSparklineWidget(self, window_seconds=30.0)
        self.history_graph.setFixedHeight(180)
        self.history_graph.setToolTip("Evolución temporal del Focus Score (últimos 10s) mostrando curva gaussiana de enfoque al girar el anillo")
        metric_layout.addWidget(self.history_graph)

        # Aviso sutil de saturación del canal rojo (oculto por defecto)
        self.lbl_saturation_warning = QLabel(
            "⚠️ [AVISO] Disco solar sobreexpuesto (Canal Rojo saturado a 255): reduce velocidad o ISO para una métrica de enfoque precisa."
        )
        self.lbl_saturation_warning.setWordWrap(True)
        self.lbl_saturation_warning.setStyleSheet("""
            background-color: #451A03;
            color: #FCD34D;
            border: 1px solid #D97706;
            border-radius: 4px;
            padding: 5px 8px;
            font-weight: bold;
            font-size: 11px;
        """)
        self.lbl_saturation_warning.setVisible(False)
        metric_layout.addWidget(self.lbl_saturation_warning)

        # Banner informativo de seguridad
        self.lbl_safety_banner = QLabel("🛡️ Protocolo Activo: Corte a T - 2 min para enfriar sensor y proteger batería.")
        self.lbl_safety_banner.setWordWrap(True)
        self.lbl_safety_banner.setStyleSheet("color: #60A5FA; font-size: 11px;")
        metric_layout.addWidget(self.lbl_safety_banner)

        metric_layout.addStretch()

        content_layout.addWidget(metric_group)
        root_layout.addLayout(content_layout, stretch=1)

    def _setup_worker(self):
        """Inicializa el hilo de procesamiento de métricas."""
        self.worker = FocusMetricWorker()
        self.worker.frame_ready.connect(self._on_frame_ready)
        self.worker.saturation_detected.connect(self._on_saturation_detected)
        self.worker.liveview_stopped.connect(self._on_worker_stopped)
        self.worker.error_occurred.connect(self._on_worker_error)

    def refresh_cameras(self):
        """Actualiza la lista desplegable de cámaras conectadas según el EquipmentManager."""
        self.combo_camera_source.blockSignals(True)
        self.combo_camera_source.clear()

        slot_a = self.equipment_manager.slot_a
        slot_b = self.equipment_manager.slot_b

        name_a = slot_a.driver.camera_name if slot_a.driver else "Sin Cámara"
        name_b = slot_b.driver.camera_name if slot_b.driver else "Sin Cámara"

        self.combo_camera_source.addItem(f"Cámara Principal [Master]: {name_a}", "A")
        if getattr(slot_b, "enabled", True):
            self.combo_camera_source.addItem(f"Cámara Secundaria: {name_b}", "B")
        elif self._active_slot == "B":
            if self._is_active:
                self.stop_liveview()
            self._active_slot = "A"

        idx = 0 if self._active_slot == "A" else 1
        if idx >= self.combo_camera_source.count():
            idx = 0
            self._active_slot = "A"
        self.combo_camera_source.setCurrentIndex(idx)
        self.combo_camera_source.blockSignals(False)

        self._update_mock_visibility()

    def set_camera_slot(self, slot_id: str):
        """Selecciona externamente la ranura de cámara (A o B)."""
        clean = slot_id.upper().strip()
        if clean == "B" and not getattr(self.equipment_manager.slot_b, "enabled", True):
            clean = "A"
        if clean in ("A", "B"):
            self._active_slot = clean
            idx = 0 if clean == "A" else 1
            if idx < self.combo_camera_source.count():
                self.combo_camera_source.setCurrentIndex(idx)

    def _update_mock_visibility(self):
        driver = self.get_current_driver()
        is_mock = isinstance(driver, MockCameraDriver)
        self.mock_focus_container.setVisible(is_mock)

    def get_current_driver(self) -> Optional[CameraDriver]:
        slot = self.equipment_manager.get_slot(self._active_slot)
        return slot.driver if slot else None

    def is_liveview_active(self) -> bool:
        return self._is_active

    def _toggle_liveview(self):
        if self._is_active:
            self.stop_liveview()
        else:
            self.start_liveview()

    def start_liveview(self):
        """Inicia el streaming de Live View."""
        if self._is_active:
            return

        driver = self.get_current_driver()
        if not driver:
            self.lbl_focus_badge.setText("● ERROR: CÁMARA NO ASIGNADA")
            self.lbl_focus_badge.setStyleSheet("background-color: #7F1D1D; color: #FCA5A5; font-weight: bold; padding: 4px 10px; border-radius: 4px;")
            return

        if not driver.connected:
            driver.connect()

        self._is_active = True
        self.btn_toggle_lv.setText("⏹ Detener Live View")
        self.btn_toggle_lv.setStyleSheet("background-color: #DC2626; color: white; font-weight: bold; padding: 7px 16px;")
        self.lbl_focus_badge.setText("● LIVE VIEW EN VIVO")
        self.lbl_focus_badge.setStyleSheet("background-color: #064E3B; color: #34D399; font-weight: bold; padding: 4px 10px; border-radius: 4px;")

        self.worker.set_driver(driver)
        self._on_zoom_changed(self.combo_zoom.currentIndex())
        self.worker.start_worker()
        self.liveview_state_changed.emit(True)

    def stop_liveview(self):
        """Detiene el streaming de Live View."""
        if not self._is_active:
            return

        self._is_active = False
        self._is_saturated = False
        self._saturation_ratio = 0.0
        self.lbl_saturation_warning.setVisible(False)
        self.btn_toggle_lv.setText("▶ Iniciar Live View")
        self.btn_toggle_lv.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 7px 16px;")
        self.lbl_focus_badge.setText("● LIVE VIEW DETENIDO")
        self.lbl_focus_badge.setStyleSheet("background-color: #1F2937; color: #9CA3AF; font-weight: bold; padding: 4px 10px; border-radius: 4px;")

        if self.worker and self.worker.isRunning():
            self.worker.stop()

        self.live_view_label.setText("👁️ Live View Apagado\nPulsa '▶ Iniciar Live View' para reiniciar la calibración de foco.")
        self.liveview_state_changed.emit(False)

    def check_safety_timeout(self, time_to_event_s: float) -> bool:
        """
        Comprueba si restan <= 120s (2 min) para el inicio de la secuencia o evento crítico.
        Si es así, corta el Live View de forma inmediata y segura.
        """
        if is_safety_cutoff_needed(time_to_event_s) and self._is_active:
            self.stop_liveview()
            self.lbl_safety_banner.setText("⚠️ [CORTE DE SEGURIDAD] Live View apagado automáticamente (T - 2 min) para enfriar sensor y proteger batería.")
            self.lbl_safety_banner.setStyleSheet("color: #EF4444; font-weight: bold; font-size: 11px;")
            self.lbl_focus_badge.setText("🛡️ CORTE DE SEGURIDAD T - 2m")
            self.lbl_focus_badge.setStyleSheet("background-color: #7F1D1D; color: #FECACA; font-weight: bold; padding: 4px 10px; border-radius: 4px;")
            return True
        return False

    def _on_camera_source_changed(self, idx: int):
        slot = self.combo_camera_source.currentData() or ("A" if idx == 0 else "B")
        self._active_slot = slot
        self._update_mock_visibility()
        if self._is_active:
            # Conmutar fuente en caliente
            driver = self.get_current_driver()
            if driver and not driver.connected:
                driver.connect()
            self.worker.set_driver(driver)

    def _on_zoom_changed(self, idx: int):
        zoom_map = {0: 1, 1: 5, 2: 10}
        zoom_val = zoom_map.get(idx, 1)
        if self.worker:
            self.worker.set_zoom(zoom_val)

    def _on_roi_clicked(self, cx: float, cy: float):
        if self.worker:
            self.worker.set_roi_center(cx, cy)
        pct_x = int(cx * 100)
        pct_y = int(cy * 100)
        self.lbl_roi_coords.setText(f"ROI: Desplazado ({pct_x}%, {pct_y}%)")

    def _on_center_roi(self):
        if self.worker:
            self.worker.set_roi_center(0.5, 0.5)
        self.lbl_roi_coords.setText("ROI: Centro (50%, 50%)")

    def _on_reset_peak(self):
        if self.worker:
            self.worker.reset_peak()
        self.lbl_peak_score.setText("Pico Máximo (Peak Hold): 0.0")
        self.lbl_efficiency.setText("Eficiencia: 0.0%")
        self.bar_sharpness.setValue(0)
        if hasattr(self, "history_graph"):
            self.history_graph.reset()

    def _on_mock_focus_slider_changed(self, val: int):
        driver = self.get_current_driver()
        if isinstance(driver, MockCameraDriver):
            sharpness = val / 100.0
            driver.set_mock_focus_sharpness(sharpness)

    def _on_mock_saturation_toggled(self, checked: bool):
        driver = self.get_current_driver()
        if isinstance(driver, MockCameraDriver):
            driver.set_mock_saturation(checked)

    def _on_saturation_detected(self, is_saturated: bool, sat_ratio: float):
        self._is_saturated = is_saturated
        self._saturation_ratio = sat_ratio
        if is_saturated:
            pct = int(round(sat_ratio * 100))
            self.lbl_saturation_warning.setText(
                f"⚠️ [AVISO] Disco solar sobreexpuesto (Canal Rojo saturado a 255 en {pct}% del ROI): reduce velocidad o ISO para métrica precisa."
            )
            self.lbl_saturation_warning.setVisible(True)
        else:
            self.lbl_saturation_warning.setVisible(False)

    def is_saturation_detected(self) -> bool:
        """Indica si el frame actual de Live View presenta saturación en el canal rojo."""
        return getattr(self, "_is_saturated", False)

    def get_saturation_ratio(self) -> float:
        """Retorna la proporción (0.0 a 1.0) de píxeles saturados en el ROI."""
        return getattr(self, "_saturation_ratio", 0.0)

    def _on_frame_ready(self, frame_img: QImage, score: float, peak: float, norm_pct: float):
        pixmap = QPixmap.fromImage(frame_img)
        self.live_view_label.set_display_pixmap(pixmap)
        self.lbl_current_score.setText(f"Score Actual: {score:.1f}")
        self.lbl_peak_score.setText(f"Pico Máximo: {peak:.1f}")
        self.lbl_efficiency.setText(f"Eficiencia: {norm_pct:.1f}%")

        if hasattr(self, "history_graph"):
            self.history_graph.add_sample(score)

        pct_val = max(0, min(100, int(norm_pct)))
        self.bar_sharpness.setValue(pct_val)

        # Alerta visual de nuevo pico
        if score >= peak and peak > 0 and score > 5.0:
            self.lbl_focus_badge.setText("⭐ ¡NUEVO PICO MÁXIMO!")
            self.lbl_focus_badge.setStyleSheet("background-color: #064E3B; color: #34D399; font-weight: bold; padding: 4px 10px; border-radius: 4px;")
            self.bar_sharpness.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #10B981;
                    border-radius: 4px;
                    background-color: #111827;
                    text-align: center;
                    color: #FFFFFF;
                    font-weight: bold;
                    font-size: 11px;
                }
                QProgressBar::chunk {
                    background-color: #34D399;
                    border-radius: 3px;
                }
            """)
        else:
            self.lbl_focus_badge.setText("● ENFOCANDO...")
            self.lbl_focus_badge.setStyleSheet("background-color: #1E293B; color: #38BDF8; font-weight: bold; padding: 4px 10px; border-radius: 4px;")
            self.bar_sharpness.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #374151;
                    border-radius: 4px;
                    background-color: #111827;
                    text-align: center;
                    color: #FFFFFF;
                    font-weight: bold;
                    font-size: 11px;
                }
                QProgressBar::chunk {
                    background-color: #10B981;
                    border-radius: 3px;
                }
            """)

    def _on_worker_stopped(self):
        pass

    def _on_worker_error(self, err_msg: str):
        self.lbl_focus_badge.setText(f"● ERROR: {err_msg[:20]}")
        self.lbl_focus_badge.setStyleSheet("background-color: #7F1D1D; color: #FCA5A5; font-weight: bold; padding: 4px 10px; border-radius: 4px;")
