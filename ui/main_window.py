"""
Interfaz Gráfica de Usuario (GUI) para eclipZe en PySide6 / Qt.
Diseño oscuro de alto contraste optimizado para campo y bajo consumo de batería.
"""

import time
import datetime
import threading
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QTextEdit, QGroupBox, QFrame, QMessageBox, QDialog,
    QTabWidget, QProgressBar, QLineEdit, QInputDialog
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QThread
from PySide6.QtGui import QFont, QColor, QPixmap
from PySide6.QtWebEngineWidgets import QWebEngineView

from core.camera import (
    CameraDriver, MockCameraDriver, GPhotoCameraDriver, NikonPTPDriver,
    NikonSdkDriver, NikonD750SdkDriver, create_camera_driver
)
from core.dispatcher import MultiCameraDispatcher, PriorityArbiter
from core.equipment import EquipmentManager, CameraSlot, DiscoveredCamera
from core.sequencer import EclipseSequencer, adjust_shutter_ev
from core.presets import (
    EclipseEvent,
    is_notice_event,
    get_solar_eclipse_2027_preset,
    get_solar_eclipse_annular_preset,
    get_lunar_eclipse_bracket_preset,
    get_quick_rehearsal_preset,
    get_eclipse_test_preset,
    get_bkt_hardware_preset,
    get_full_rehearsal_preset
)
from core.audio import AudioNotifier
from core.gps import GPSReader, GPSData
from core.map_manager import MapTileManager, MapServer
from core.eclipse_db import EclipseCatalogManager, EclipseInfo
from core.astronomy import calculate_local_eclipse, LocalEclipseResult
from ui.focus_view import FocusViewWidget
from ui.timeline_widget import EclipseTimelineWidget
from ui.execution_log import ExecutionLogWidget
from ui.next_banner import NextBannerWidget
from ui.calendar_view import EclipseCalendarWidget


class SequencerSignals(QObject):
    """Puente de señales entre el hilo del secuenciador y la interfaz Qt."""
    shot_triggered = Signal(object, str, str)  # event, shutter, iso
    shot_skipped = Signal(object, float)       # event, delay
    tick = Signal(float, object, float)        # now, event, time_to_shot
    finished = Signal()


class MapDownloadWorker(QObject):
    """Worker en segundo plano para descarga no bloqueante de teselas."""
    progress = Signal(int, int)
    finished = Signal(int, dict)
    error = Signal(str)

    def __init__(self, manager: MapTileManager, lat: float, lon: float, radius_km: float, zoom_levels: list[int], zone_name: Optional[str] = None):
        super().__init__()
        self.manager = manager
        self.lat = lat
        self.lon = lon
        self.radius_km = radius_km
        self.zoom_levels = zoom_levels
        self.zone_name = zone_name
        self.stop_event = threading.Event()

    def run(self):
        try:
            downloaded = self.manager.download_region(
                self.lat, self.lon, self.radius_km, self.zoom_levels,
                progress_cb=lambda curr, total: self.progress.emit(curr, total),
                stop_event=self.stop_event,
                zone_name=self.zone_name
            )
            meta = self.manager.get_metadata() or {}
            self.finished.emit(downloaded, meta)
        except Exception as e:
            self.error.emit(str(e))

    def cancel(self):
        self.stop_event.set()


class MapCacheManagerDialog(QDialog):
    """Diálogo para la gestión individual de zonas de mapas guardadas y purgado por antigüedad."""

    def __init__(self, tile_manager: MapTileManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.tile_manager = tile_manager
        self.setWindowTitle("Gestor y Purgado de Mapas Offline")
        self.resize(720, 430)
        self.setStyleSheet("""
            QDialog {
                background-color: #121418;
                color: #E0E0E0;
            }
            QGroupBox {
                border: 1px solid #2D323B;
                border-radius: 6px;
                margin-top: 10px;
                font-weight: bold;
                color: #4DA3FF;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QTableWidget {
                background-color: #16191F;
                gridline-color: #262B34;
                color: #E5E9F0;
                border: 1px solid #2D323B;
            }
            QHeaderView::section {
                background-color: #1E222A;
                color: #9CA3AF;
                border: 1px solid #262B34;
                padding: 4px;
                font-weight: bold;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Resumen general superior
        self.lbl_summary = QLabel()
        self.lbl_summary.setStyleSheet("font-size: 13px; font-weight: bold; color: #10B981;")
        layout.addWidget(self.lbl_summary)

        # Grupo: Zonas Registradas
        zones_group = QGroupBox("Zonas Cartográficas Guardadas")
        zones_layout = QVBoxLayout(zones_group)

        self.table_zones = QTableWidget()
        self.table_zones.setColumnCount(5)
        self.table_zones.setHorizontalHeaderLabels(["Nombre / Ubicación", "Fecha Guardada", "Radio", "Teselas", "Acción"])
        self.table_zones.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_zones.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_zones.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_zones.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_zones.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        zones_layout.addWidget(self.table_zones)

        layout.addWidget(zones_group)

        # Grupo: Purgado por Antigüedad
        purge_group = QGroupBox("Limpieza Rápida por Antigüedad")
        purge_layout = QHBoxLayout(purge_group)

        purge_layout.addWidget(QLabel("Eliminar teselas más antiguas de:"))
        self.combo_purge_days = QComboBox()
        self.combo_purge_days.addItems(["30 días", "60 días", "90 días", "7 días"])
        purge_layout.addWidget(self.combo_purge_days)

        self.btn_purge_age = QPushButton("🧹 Purgar Teselas Antiguas")
        self.btn_purge_age.setStyleSheet("background-color: #DC2626; color: white; font-weight: bold;")
        self.btn_purge_age.clicked.connect(self._on_purge_by_age)
        purge_layout.addWidget(self.btn_purge_age)

        purge_layout.addStretch()
        layout.addWidget(purge_group)

        # Botón inferior para cerrar
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)

        self._populate_zones()

    def _populate_zones(self):
        zones = self.tile_manager.get_zones()
        count, mb = self.tile_manager.count_cached_tiles()
        self.lbl_summary.setText(f"💾 Almacenamiento total en caché: {count} teselas ({mb:.2f} MB)")

        self.table_zones.setRowCount(len(zones))
        for row, z in enumerate(zones):
            name = z.get("name", "Zona sin nombre")
            date = z.get("date", "--")
            rad = f"{z.get('radius_km', 0):.0f} km"
            tiles = f"{z.get('tile_count', len(z.get('tiles', [])))} teselas"

            item_name = QTableWidgetItem(name)
            item_date = QTableWidgetItem(date)
            item_rad = QTableWidgetItem(rad)
            item_tiles = QTableWidgetItem(tiles)

            for item in (item_name, item_date, item_rad, item_tiles):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            self.table_zones.setItem(row, 0, item_name)
            self.table_zones.setItem(row, 1, item_date)
            self.table_zones.setItem(row, 2, item_rad)
            self.table_zones.setItem(row, 3, item_tiles)

            # Botonera de acciones: Renombrar y Eliminar
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(6)

            zone_id = z.get("id")

            btn_rename = QPushButton("✏️ Renombrar")
            btn_rename.setStyleSheet("background-color: #1E3A8A; color: #93C5FD; padding: 4px 8px; font-size: 11px;")
            btn_rename.clicked.connect(lambda checked=False, zid=zone_id, zn=name: self._rename_zone(zid, zn))
            action_layout.addWidget(btn_rename)

            btn_del = QPushButton("🗑️ Eliminar")
            btn_del.setStyleSheet("background-color: #7F1D1D; color: #FCA5A5; padding: 4px 8px; font-size: 11px;")
            btn_del.clicked.connect(lambda checked=False, zid=zone_id, zn=name: self._delete_zone(zid, zn))
            action_layout.addWidget(btn_del)

            self.table_zones.setCellWidget(row, 4, action_widget)

    def _rename_zone(self, zone_id: str, current_name: str):
        new_name, ok = QInputDialog.getText(
            self,
            "Renombrar Zona de Mapa",
            "Introduce el nuevo nombre para esta zona cartográfica:",
            text=current_name
        )
        if ok and new_name.strip():
            self.tile_manager.rename_zone(zone_id, new_name.strip())
            self._populate_zones()

    def _delete_zone(self, zone_id: str, zone_name: str):
        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Estás seguro de eliminar '{zone_name}'?\nSe borrarán las teselas del mapa que no sean compartidas con otras zonas.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            deleted_count, freed_mb = self.tile_manager.delete_zone(zone_id)
            self._populate_zones()
            QMessageBox.information(
                self,
                "Zona eliminada",
                f"Se han eliminado {deleted_count} teselas liberando {freed_mb:.2f} MB de disco."
            )

    def _on_purge_by_age(self):
        text = self.combo_purge_days.currentText()
        days = int(text.split()[0])
        reply = QMessageBox.question(
            self,
            "Confirmar purgado",
            f"¿Deseas purgar todas las teselas descargadas hace más de {days} días?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            deleted_count, freed_mb = self.tile_manager.purge_older_than(days)
            self._populate_zones()
            QMessageBox.information(
                self,
                "Purgado completado",
                f"Se han purgado {deleted_count} teselas liberando {freed_mb:.2f} MB de disco."
            )


class EmergencyStopButton(QPushButton):
    """
    Botón de parada de emergencia con protección anti-activación accidental en campo.
    Requiere un doble clic rápido (<500ms) o una pulsación sostenida de 1 segundo para disparar
    el aborto de secuencia. Una pulsación simple muestra advertencia visual interactiva sin abortar.
    """
    emergency_triggered = Signal()

    def __init__(self, text: str = "⏹ PARADA EMERGENCIA", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self._default_text = text
        self._hold_timer = QTimer(self)
        self._hold_timer.setSingleShot(True)
        self._hold_timer.setInterval(1000)
        self._hold_timer.timeout.connect(self._on_hold_timeout)

        self._reset_timer = QTimer(self)
        self._reset_timer.setSingleShot(True)
        self._reset_timer.setInterval(1500)
        self._reset_timer.timeout.connect(self._reset_prompt)

        self._last_click_time = 0.0
        self._held_fired = False

        self.setToolTip("Protección de campo: Doble clic rápido o mantener pulsado 1s para abortar la secuencia.")

    def _on_hold_timeout(self):
        if self.isEnabled():
            self._held_fired = True
            self._fire_emergency()

    def _reset_prompt(self):
        if self.isEnabled():
            self.setText(self._default_text)

    def _fire_emergency(self):
        self._hold_timer.stop()
        self._reset_timer.stop()
        self.setText(self._default_text)
        self.emergency_triggered.emit()

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        if not enabled:
            self._hold_timer.stop()
            self._reset_timer.stop()
            self.setText(self._default_text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.isEnabled():
            self._held_fired = False
            now = time.time()
            if now - self._last_click_time <= 0.5:
                self._last_click_time = 0.0
                self._fire_emergency()
                event.accept()
                return
            self._last_click_time = now
            self._hold_timer.start(1000)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and self.isEnabled():
            self._fire_emergency()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def mouseReleaseEvent(self, event):
        self._hold_timer.stop()
        if self._held_fired:
            self._held_fired = False
            event.accept()
            return
        if self.isEnabled() and self._last_click_time > 0:
            self.setText("⚠️ PULSA OTRA VEZ O MANTÉN 1s")
            self._reset_timer.start(1500)
        super().mouseReleaseEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("eclipZe — Control Automatizado de Eclipses")
        self.resize(1100, 750)

        # Estado del sistema y Gestor de Equipamiento Multi-Cámara
        self.equipment_manager = EquipmentManager()
        self.dispatcher = self.equipment_manager.dispatcher
        self.audio = AudioNotifier(enabled=True)
        self.gps_reader = GPSReader()
        self.sequencer: Optional[EclipseSequencer] = None
        self.current_schedule: list[EclipseEvent] = []
        self.current_ev_offset: int = 0

        # Gestor de mapas offline y servidor HTTP local de teselas
        self.tile_manager = MapTileManager()
        self.map_server = MapServer(self.tile_manager)
        self.map_server.start()
        self._download_thread: Optional[QThread] = None
        self._download_worker: Optional[MapDownloadWorker] = None
        self._last_js_gps_update: float = 0.0
        self.download_target_lat: float = 40.65406
        self.download_target_lon: float = -3.76918
        self.download_target_radius: float = 10.0

        # Eclipse Activo y Motor Astronómico (Fase 4 v2.0)
        self.active_eclipse_info: Optional[EclipseInfo] = None
        self.active_eclipse_result: Optional[LocalEclipseResult] = None
        self.active_contacts: Optional[dict] = None
        self.is_simulation_mode: bool = False
        self.active_preset_name: str = ""

        self.signals = SequencerSignals()
        self.signals.shot_triggered.connect(self._on_shot_triggered)
        self.signals.shot_skipped.connect(self._on_shot_skipped)
        self.signals.tick.connect(self._on_tick)
        self.signals.finished.connect(self._on_finished)

        self._setup_style()
        self._init_ui()

        # Timer de actualización de reloj y telemetría (10 Hz)
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self._update_clock_bar)
        self.ui_timer.start(100)

        # Estado inicial limpio: sin eclipse precargado (debe cargarse desde el Calendario)
        self.current_schedule = []
        self._populate_table()
        if hasattr(self, "next_banner") and self.next_banner:
            self.next_banner.set_idle("Ningún eclipse cargado — Selecciona un evento en el Calendario")

        self.camera.connect()
        self.gps_reader.start()
        self._log("Sistema eclipZe inicializado en modo seguro (esperando carga de eclipse desde Calendario).")

    @property
    def camera(self) -> CameraDriver:
        drv = self.dispatcher.get_master_driver()
        return drv if drv is not None else self.equipment_manager.slot_a.driver

    @camera.setter
    def camera(self, drv: CameraDriver):
        self.equipment_manager.slot_a.driver = drv
        self.dispatcher.set_driver("A", drv)

    def _setup_style(self):
        """Tema oscuro de alto contraste tipo cabina de astronomía."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121418;
                color: #E0E0E0;
            }
            QGroupBox {
                border: 1px solid #2D323B;
                border-radius: 6px;
                margin-top: 10px;
                font-weight: bold;
                color: #4DA3FF;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #D1D5DB;
            }
            QPushButton {
                background-color: #242933;
                border: 1px solid #3B4252;
                border-radius: 4px;
                color: #ECEFF4;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #383E4A;
                border-color: #4DA3FF;
            }
            QPushButton:pressed {
                background-color: #4DA3FF;
                color: #121418;
            }
            QComboBox {
                background-color: #1E222A;
                border: 1px solid #3B4252;
                border-radius: 4px;
                color: #ECEFF4;
                padding: 5px 10px;
            }
            QTableWidget {
                background-color: #16191F;
                gridline-color: #262B34;
                color: #E5E9F0;
                border: 1px solid #2D323B;
                selection-background-color: #2D3748;
            }
            QHeaderView::section {
                background-color: #1E222A;
                color: #9CA3AF;
                border: 1px solid #262B34;
                padding: 4px;
                font-weight: bold;
            }
            QTextEdit {
                background-color: #0E1013;
                color: #A0AEC0;
                border: 1px solid #262B34;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
            QTabWidget::pane {
                border: 1px solid #2D323B;
                background-color: #121418;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #181B22;
                color: #9CA3AF;
                padding: 7px 18px;
                border: 1px solid #2D323B;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 3px;
                font-weight: bold;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background-color: #2563EB;
                color: #FFFFFF;
            }
            QTabBar::tab:hover:!selected {
                background-color: #283040;
                color: #E2E8F0;
            }
            QProgressBar {
                border: 1px solid #374151;
                border-radius: 4px;
                background-color: #111827;
                text-align: center;
                color: #E5E9F0;
                font-size: 11px;
                height: 18px;
            }
            QProgressBar::chunk {
                background-color: #10B981;
                border-radius: 3px;
            }
        """)

    def _init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        root_layout = QVBoxLayout(main_widget)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(10)

        # 1. Barra Superior de Telemetría Pasiva (HUD)
        top_group = QGroupBox("Telemetría del Sistema")
        top_layout = QHBoxLayout(top_group)
        top_layout.setContentsMargins(12, 6, 12, 6)
        top_layout.setSpacing(12)

        self.lbl_top_slot_a = QLabel("● Cámara Principal [⭐ Master]: Nikon Z5 II (Simulada) (95%)")
        self.lbl_top_slot_a.setStyleSheet("color: #94A3B8; font-weight: bold; font-size: 11px;")
        top_layout.addWidget(self.lbl_top_slot_a)

        self.lbl_top_slot_b = QLabel("● Cámara Secundaria: Nikon D750 (Simulada) (88%)")
        self.lbl_top_slot_b.setStyleSheet("color: #60A5FA; font-size: 11px;")
        top_layout.addWidget(self.lbl_top_slot_b)

        # Compatibilidad hacia atrás con referencias directas al estado de cámara
        self.lbl_camera_status = self.lbl_top_slot_a

        # Separador visual
        sep1 = QLabel("|")
        sep1.setStyleSheet("color: #374151; font-weight: bold;")
        top_layout.addWidget(sep1)

        # Indicador de Modo Silencioso pasivo
        self.lbl_top_silent = QLabel("🔇 Silencioso: ON")
        self.lbl_top_silent.setStyleSheet("color: #10B981; font-size: 11px; font-weight: bold;")
        top_layout.addWidget(self.lbl_top_silent)

        sep2 = QLabel("|")
        sep2.setStyleSheet("color: #374151; font-weight: bold;")
        top_layout.addWidget(sep2)

        # Telemetría GPS: Estado + Offset de Sincronización
        self.lbl_gps_status = QLabel("GPS: Buscando fix...")
        self.lbl_gps_status.setStyleSheet("color: #F59E0B; font-size: 11px;")
        top_layout.addWidget(self.lbl_gps_status)

        self.lbl_gps_sync = QLabel("Reloj Local PC (Sin corrección GPS)")
        self.lbl_gps_sync.setStyleSheet("color: #9CA3AF; font-size: 11px; font-family: Consolas;")
        top_layout.addWidget(self.lbl_gps_sync)

        top_layout.addStretch()

        # Reloj UTC / Local
        self.lbl_clock = QLabel("UTC: --:--:-- | Local: --:--:--")
        self.lbl_clock.setFont(QFont("Consolas", 12, QFont.Bold))
        self.lbl_clock.setStyleSheet("color: #60A5FA;")
        top_layout.addWidget(self.lbl_clock)

        root_layout.addWidget(top_group)

        # 2. Panel Central con Pestañas (Equipamiento, Enfoque, Secuencia y Mapa GPS)
        self.tabs = QTabWidget()

        # Pestaña 0: Gestión de Equipamiento (Fase 1 v2.0)
        self.tab_equipment = self._init_equipment_tab()
        self.tabs.addTab(self.tab_equipment, "📷 Gestión de Equipamiento")

        # Pestaña 1: Asistente de Enfoque y Live View (Fase 2 v2.0)
        self.tab_focus = FocusViewWidget(self.equipment_manager, parent=self)
        self.tabs.addTab(self.tab_focus, "👁️ Enfoque (Live View)")

        # Pestaña 2: Secuencia & Control (Fase 3 v2.0 - Timeline, NEXT Banner y Execution Log)
        tab_sequence = QWidget()
        seq_layout = QVBoxLayout(tab_sequence)
        seq_layout.setContentsMargins(8, 8, 8, 8)
        seq_layout.setSpacing(8)

        # 1. Barra de control superior (Perfil Activo, Acceso a Calendario, EV Offset, Disparo Único)
        top_ctrl_layout = QHBoxLayout()
        top_ctrl_layout.addWidget(QLabel("Perfil Activo:"))
        self.lbl_loaded_profile = QLabel("⚠️ Sin eclipse cargado")
        self.lbl_loaded_profile.setStyleSheet("font-weight: bold; color: #F59E0B; font-size: 11px;")
        top_ctrl_layout.addWidget(self.lbl_loaded_profile)

        self.btn_go_calendar = QPushButton("📅 Ir al Calendario")
        self.btn_go_calendar.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #38BDF8;
                font-weight: bold;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                border: 1px solid #38BDF8;
            }
            QPushButton:hover {
                background-color: #0F172A;
                color: #FFFFFF;
            }
        """)
        self.btn_go_calendar.clicked.connect(lambda: self.tabs.setCurrentIndex(4))
        top_ctrl_layout.addWidget(self.btn_go_calendar)

        # Mantenemos combo_preset para compatibilidad con tests y suites automáticas
        self.combo_preset = QComboBox()
        self.combo_preset.addItems([
            "(Cargado desde Calendario)",
            "ECLIPSE_TEST (Estrés 2.5 min)",
            "Simulacro BKT Hardware (7 tomas AE Bracketing 1.7 EV)",
            "Simulacro Real (C2 - 5m a C3 + 5m)",
            "Simulacro Rápido (12 seg de prueba)",
            "Eclipse Solar 2027 (Totalidad Cádiz / Luxor)",
            "Eclipse Solar Anular 2028 (Con filtro solar continuo)",
            "Eclipse Lunar (Horquillado HDR)"
        ])
        self.combo_preset.setVisible(False)
        self.combo_preset.currentTextChanged.connect(self._on_preset_changed)
        top_ctrl_layout.addWidget(self.combo_preset)

        top_ctrl_layout.addSpacing(10)

        # Compensación EV en vivo
        top_ctrl_layout.addWidget(QLabel("Offset EV:"))
        self.lbl_current_ev = QLabel("0 EV")
        self.lbl_current_ev.setStyleSheet("font-weight: bold; color: #38BDF8; font-size: 11px;")
        top_ctrl_layout.addWidget(self.lbl_current_ev)

        for offset_val, label in [(-2, "-2 EV"), (-1, "-1 EV"), (0, "0 EV"), (+1, "+1 EV"), (+2, "+2 EV")]:
            btn = QPushButton(label)
            btn.setFixedHeight(26)
            btn.clicked.connect(lambda checked=False, val=offset_val: self._set_ev_offset(val))
            top_ctrl_layout.addWidget(btn)

        top_ctrl_layout.addStretch()

        # Botones de prueba
        self.btn_single_shot = QPushButton("⚡ Disparo Único")
        self.btn_single_shot.setFixedHeight(26)
        self.btn_single_shot.clicked.connect(self._trigger_single_test_shot)
        top_ctrl_layout.addWidget(self.btn_single_shot)

        self.btn_burst_shot = QPushButton("🔥 Ráfaga BKT")
        self.btn_burst_shot.setStyleSheet("background-color: #6D28D9; color: white; font-weight: bold;")
        self.btn_burst_shot.setFixedHeight(26)
        self.btn_burst_shot.clicked.connect(self._trigger_burst_shot)
        top_ctrl_layout.addWidget(self.btn_burst_shot)

        self.btn_burst_baily = QPushButton("⚡ Ráfaga Baily (18x)")
        self.btn_burst_baily.setStyleSheet("background-color: #D97706; color: white; font-weight: bold;")
        self.btn_burst_baily.setFixedHeight(26)
        self.btn_burst_baily.clicked.connect(self._trigger_burst_baily)
        top_ctrl_layout.addWidget(self.btn_burst_baily)

        self.btn_manual_plan = QPushButton("📋 Plan Manual Impreso")
        self.btn_manual_plan.setStyleSheet("background-color: #1E293B; color: #38BDF8; font-weight: bold; border: 1px solid #38BDF8;")
        self.btn_manual_plan.setFixedHeight(26)
        self.btn_manual_plan.setToolTip("Genera una hoja de ruta formal (A4/A5) para imprimir o seguir a mano si falla el PC")
        self.btn_manual_plan.clicked.connect(self._generate_active_backup_plan)
        top_ctrl_layout.addWidget(self.btn_manual_plan)

        seq_layout.addLayout(top_ctrl_layout)

        # 2. Timeline Gráfico Vectorial con Pistas Paralelas A y B (EclipseTimelineWidget)
        self.timeline_widget = EclipseTimelineWidget(self)
        seq_layout.addWidget(self.timeline_widget)

        # 3. Banner Horizontal NEXT Dinámico con cuenta atrás milimétrica
        self.next_banner = NextBannerWidget(self)
        seq_layout.addWidget(self.next_banner)

        # Conectar widgets legacy para compatibilidad
        self.lbl_countdown = QLabel("00:00.0")
        self.lbl_countdown.setVisible(False)
        self.lbl_target_info = QLabel("")
        self.lbl_target_info.setVisible(False)

        # 4. Cuerpo inferior: ExecutionLogWidget (70%) + Visor de Foto SD (30%)
        body_layout = QHBoxLayout()
        body_layout.setSpacing(8)

        # Execution Log con telemetría de jitter y badges de cámara
        self.execution_log = ExecutionLogWidget(self)
        body_layout.addWidget(self.execution_log, stretch=7)

        # Visor de tarjeta SD y foto de prueba (lateral derecho compacto)
        preview_group = QGroupBox("Visor SD / Encuadre")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(6, 12, 6, 6)
        preview_layout.setSpacing(6)

        slot_layout = QHBoxLayout()
        slot_layout.addWidget(QLabel("Ranura:"))
        self.combo_slot = QComboBox()
        self.combo_slot.addItems(["Ranura SD 1", "Ranura SD 2"])
        slot_layout.addWidget(self.combo_slot)
        preview_layout.addLayout(slot_layout)

        self.lbl_preview_img = QLabel("Sin foto cargada")
        self.lbl_preview_img.setAlignment(Qt.AlignCenter)
        self.lbl_preview_img.setMinimumHeight(110)
        self.lbl_preview_img.setStyleSheet("""
            QLabel {
                background-color: #0A0C0F;
                border: 1px dashed #374151;
                border-radius: 4px;
                color: #6B7280;
                font-size: 11px;
            }
        """)
        self.lbl_preview_img.mousePressEvent = self._on_preview_clicked
        preview_layout.addWidget(self.lbl_preview_img)

        preview_btn_layout = QHBoxLayout()
        self.btn_shoot_and_preview = QPushButton("📸 Disparar y Ver")
        self.btn_shoot_and_preview.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold;")
        self.btn_shoot_and_preview.clicked.connect(self._trigger_shot_and_preview)
        preview_btn_layout.addWidget(self.btn_shoot_and_preview)

        self.btn_load_last = QPushButton("🔄 Leer SD")
        self.btn_load_last.clicked.connect(self._load_last_photo_preview)
        preview_btn_layout.addWidget(self.btn_load_last)

        preview_layout.addLayout(preview_btn_layout)
        body_layout.addWidget(preview_group, stretch=3)

        seq_layout.addLayout(body_layout, stretch=1)

        # Tabla de eventos legacy para compatibilidad total con tests existentes
        self.table_events = QTableWidget()
        self.table_events.setColumnCount(5)
        self.table_events.setHorizontalHeaderLabels(["Contacto / Offset", "Velocidad", "ISO", "Descripción", "Estado"])
        self.table_events.setVisible(False)

        self.tabs.addTab(tab_sequence, "⚡ Secuencia & Control")

        # Pestaña 3: Mapa GPS & Coordenadas
        tab_map = self._init_map_tab()
        self.tabs.addTab(tab_map, "🗺️ Mapa GPS & Coordenadas")

        # Pestaña 4: Calendario de Eclipses (Fase 4 v2.0)
        self.tab_calendar = EclipseCalendarWidget(parent=self, map_server=self.map_server)
        self.tab_calendar.eclipse_selected_as_active.connect(self._on_eclipse_activated)
        self.tabs.addTab(self.tab_calendar, "📅 Calendario de Eclipses")

        root_layout.addWidget(self.tabs, stretch=7)

        # 3. Panel Inferior: Botonera Principal y Log de Eventos
        bottom_layout = QHBoxLayout()

        # Log en consola
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumHeight(130)
        bottom_layout.addWidget(self.txt_log, stretch=7)

        # Botones de control de secuencia
        btn_control_layout = QVBoxLayout()
        self.btn_start = QPushButton("▶ INICIAR SECUENCIA")
        self.btn_start.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #10B981;
            }
            QPushButton:disabled {
                background-color: #1E293B;
                color: #94A3B8;
                border: 1px solid #334155;
            }
        """)
        self.btn_start.clicked.connect(self._start_sequence)
        btn_control_layout.addWidget(self.btn_start)

        self.btn_stop = EmergencyStopButton("⏹ PARADA EMERGENCIA")
        self.btn_stop.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #DC2626;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #EF4444;
            }
            QPushButton:disabled {
                background-color: #374151;
                color: #6B7280;
                border: 1px solid #4B5563;
            }
        """)
        self.btn_stop.emergency_triggered.connect(self._stop_sequence)
        self.btn_stop.setEnabled(False)
        btn_control_layout.addWidget(self.btn_stop)

        bottom_layout.addLayout(btn_control_layout, stretch=3)
        root_layout.addLayout(bottom_layout, stretch=3)

    def _init_map_tab(self) -> QWidget:
        tab_map = QWidget()
        map_layout = QHBoxLayout(tab_map)
        map_layout.setContentsMargins(6, 6, 6, 6)
        map_layout.setSpacing(10)

        # Panel izquierdo: Telemetría GNSS y Gestor Offline (35% ancho)
        sidebar = QVBoxLayout()
        sidebar.setSpacing(10)

        # Grupo 1: Telemetría GNSS en Vivo
        gps_group = QGroupBox("Telemetría Satelital GNSS")
        gps_layout = QVBoxLayout(gps_group)
        gps_layout.setSpacing(6)

        self.lbl_map_gps_status = QLabel("Estado: Conectando con u-blox...")
        self.lbl_map_gps_status.setStyleSheet("font-weight: bold; color: #F59E0B;")
        gps_layout.addWidget(self.lbl_map_gps_status)

        self.lbl_map_coords = QLabel("Coordenadas: --.----°, --.----°")
        self.lbl_map_coords.setStyleSheet("font-family: Consolas; font-size: 12px; color: #60A5FA; font-weight: bold;")
        gps_layout.addWidget(self.lbl_map_coords)

        self.lbl_map_alt = QLabel("Altitud: -- m  |  Satélites: --")
        gps_layout.addWidget(self.lbl_map_alt)

        self.lbl_map_offset = QLabel("Desfase Reloj UTC: -- s")
        gps_layout.addWidget(self.lbl_map_offset)

        self.btn_center_map = QPushButton("🎯 Centrar Mapa en mi GPS")
        self.btn_center_map.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold;")
        self.btn_center_map.clicked.connect(self._center_map_on_gps)
        gps_layout.addWidget(self.btn_center_map)

        sidebar.addWidget(gps_group)

        # Grupo 2: Gestor de Mapas Offline
        offline_group = QGroupBox("Gestor de Zona Cartográfica Offline")
        offline_layout = QVBoxLayout(offline_group)
        offline_layout.setSpacing(7)

        # Información de última descarga guardada
        self.lbl_offline_meta = QLabel("Cargando información de caché...")
        self.lbl_offline_meta.setStyleSheet("font-size: 11px; color: #9CA3AF;")
        self.lbl_offline_meta.setWordWrap(True)
        offline_layout.addWidget(self.lbl_offline_meta)

        # Indicador de centro de descarga seleccionado
        self.lbl_download_target = QLabel("Zona objetivo: 40.65406°, -3.76918° (Radio 10 km)")
        self.lbl_download_target.setStyleSheet("font-family: Consolas; font-size: 11px; color: #38BDF8; font-weight: bold;")
        self.lbl_download_target.setWordWrap(True)
        offline_layout.addWidget(self.lbl_download_target)

        # Botones para ubicar el centro de descarga
        target_btns_row = QHBoxLayout()
        self.btn_target_my_gps = QPushButton("📍 Fijar en mi GPS")
        self.btn_target_my_gps.setToolTip("Mueve el centro de descarga a la ubicación GPS actual")
        self.btn_target_my_gps.clicked.connect(self._set_download_target_to_gps)
        target_btns_row.addWidget(self.btn_target_my_gps)

        self.btn_target_view_center = QPushButton("🔍 Fijar en centro vista")
        self.btn_target_view_center.setToolTip("Mueve el centro de descarga al centro visible en la pantalla")
        self.btn_target_view_center.clicked.connect(self._set_download_target_to_view)
        target_btns_row.addWidget(self.btn_target_view_center)
        offline_layout.addLayout(target_btns_row)

        # Campo para nombre personalizado de la zona
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Nombre zona:"))
        self.txt_zone_name = QLineEdit()
        self.txt_zone_name.setPlaceholderText("Opcional (ej: Playa Bolonia, Sierra Norte...)")
        self.txt_zone_name.setStyleSheet("background-color: #1E222A; border: 1px solid #3B4252; color: #ECEFF4; padding: 4px 8px; border-radius: 4px;")
        name_row.addWidget(self.txt_zone_name)
        offline_layout.addLayout(name_row)

        # Selector de radio
        radius_row = QHBoxLayout()
        radius_row.addWidget(QLabel("Radio a descargar:"))
        self.combo_map_radius = QComboBox()
        self.combo_map_radius.addItems([
            "5 km (Rápido ~70 teselas)",
            "10 km (Recomendado ~210 teselas)",
            "20 km (Extenso ~600 teselas)"
        ])
        self.combo_map_radius.setCurrentIndex(1)
        self.combo_map_radius.currentTextChanged.connect(self._on_map_radius_changed)
        radius_row.addWidget(self.combo_map_radius)
        offline_layout.addLayout(radius_row)

        btn_dl_row = QHBoxLayout()
        self.btn_download_offline = QPushButton("📥 Descargar Zona Seleccionada")
        self.btn_download_offline.setStyleSheet("background-color: #059669; color: white; font-weight: bold;")
        self.btn_download_offline.clicked.connect(self._start_offline_download)
        btn_dl_row.addWidget(self.btn_download_offline)

        self.btn_cancel_download = QPushButton("⏹ Cancelar")
        self.btn_cancel_download.setStyleSheet("background-color: #DC2626; color: white;")
        self.btn_cancel_download.setEnabled(False)
        self.btn_cancel_download.clicked.connect(self._cancel_offline_download)
        btn_dl_row.addWidget(self.btn_cancel_download)
        offline_layout.addLayout(btn_dl_row)

        self.progress_map_download = QProgressBar()
        self.progress_map_download.setValue(0)
        self.progress_map_download.setTextVisible(True)
        offline_layout.addWidget(self.progress_map_download)

        self.lbl_download_status = QLabel("Haz clic en cualquier punto del mapa para mover la zona a descargar.")
        self.lbl_download_status.setStyleSheet("font-size: 11px; color: #9CA3AF;")
        self.lbl_download_status.setWordWrap(True)
        offline_layout.addWidget(self.lbl_download_status)

        self.btn_manage_zones = QPushButton("🗂️ Gestionar y Purgar Zonas Guardadas...")
        self.btn_manage_zones.setStyleSheet("background-color: #374151; color: #E5E9F0; font-weight: bold;")
        self.btn_manage_zones.clicked.connect(self._open_map_cache_dialog)
        offline_layout.addWidget(self.btn_manage_zones)

        sidebar.addWidget(offline_group)
        sidebar.addStretch()

        map_layout.addLayout(sidebar, stretch=3)

        # Panel derecho: Visor WebEngine con mapa interactivo Leaflet / OSM (65% ancho)
        self.web_map_view = QWebEngineView()
        self.web_map_view.setUrl(self.map_server.url)
        self.web_map_view.titleChanged.connect(self._on_map_title_changed)
        map_layout.addWidget(self.web_map_view, stretch=7)

        self._refresh_offline_metadata_display()
        return tab_map

    def _open_map_cache_dialog(self):
        dialog = MapCacheManagerDialog(self.tile_manager, parent=self)
        dialog.exec()
        self._refresh_offline_metadata_display()

    def _refresh_offline_metadata_display(self):
        meta = self.tile_manager.get_metadata()
        zones = self.tile_manager.get_zones()
        count, mb = self.tile_manager.count_cached_tiles()
        if len(zones) > 0:
            last_zone = zones[-1]
            date_str = last_zone.get("date", "--")
            name = last_zone.get("name", "Zona")
            self.lbl_offline_meta.setText(
                f"📅 Zonas guardadas: {len(zones)} ({count} teselas, {mb:.2f} MB)\n"
                f"📍 Última: {name} ({date_str})"
            )
        elif count > 0:
            self.lbl_offline_meta.setText(f"💾 Caché en disco: {count} teselas ({mb:.2f} MB)")
        else:
            self.lbl_offline_meta.setText("⚠️ Sin mapa offline guardado aún.\nPulsa 'Descargar Zona Seleccionada' para guardarlo.")

    def _center_map_on_gps(self):
        d = self.gps_reader.data
        lat = d.latitude if (d.has_fix and d.latitude != 0) else 40.65406
        lon = d.longitude if (d.has_fix and d.longitude != 0) else -3.76918
        self.web_map_view.page().runJavaScript(f"centerMap({lat}, {lon}, 15);")

    def _on_map_title_changed(self, title: str):
        if title.startswith("TARGET:"):
            raw = title[len("TARGET:"):].strip()
            parts = raw.split(",")
            if len(parts) == 3:
                try:
                    self.download_target_lat = float(parts[0])
                    self.download_target_lon = float(parts[1])
                    self.download_target_radius = float(parts[2])
                    if hasattr(self, "lbl_download_target"):
                        self.lbl_download_target.setText(
                            f"Zona objetivo: {self.download_target_lat:.5f}°, {self.download_target_lon:.5f}° ({self.download_target_radius:.0f} km)"
                        )
                    if hasattr(self, "tab_calendar") and self.tab_calendar and not self.gps_reader.data.has_fix:
                        self.tab_calendar.update_coordinates(self.download_target_lat, self.download_target_lon, 0.0)
                except ValueError:
                    pass

    def _on_map_radius_changed(self, text: str):
        if "5 km" in text:
            rad = 5.0
        elif "20 km" in text:
            rad = 20.0
        else:
            rad = 10.0
        self.download_target_radius = rad
        self.web_map_view.page().runJavaScript(f"setDownloadRadius({rad});")

    def _set_download_target_to_gps(self):
        d = self.gps_reader.data
        lat = d.latitude if (d.has_fix and d.latitude != 0) else 40.65406
        lon = d.longitude if (d.has_fix and d.longitude != 0) else -3.76918
        self.download_target_lat = lat
        self.download_target_lon = lon
        self.web_map_view.page().runJavaScript(
            f"setDownloadTarget({lat}, {lon}, {self.download_target_radius}); centerMap({lat}, {lon});"
        )

    def _set_download_target_to_view(self):
        self.web_map_view.page().runJavaScript("centerDownloadOnView();")

    def _start_offline_download(self):
        lat = self.download_target_lat
        lon = self.download_target_lon
        radius_km = self.download_target_radius

        if radius_km <= 5.0:
            zooms = [12, 13, 14]
        elif radius_km >= 20.0:
            zooms = [11, 12, 13, 14]
        else:
            zooms = [12, 13, 14, 15]

        self.btn_download_offline.setEnabled(False)
        self.btn_cancel_download.setEnabled(True)
        self.progress_map_download.setValue(0)
        self.lbl_download_status.setText(f"Iniciando descarga en {lat:.4f}°, {lon:.4f}° (Radio {radius_km:.0f} km)...")

        zone_name = self.txt_zone_name.text().strip() or None
        self._download_thread = QThread()
        self._download_worker = MapDownloadWorker(self.tile_manager, lat, lon, radius_km, zooms, zone_name=zone_name)
        self._download_worker.moveToThread(self._download_thread)

        self._download_thread.started.connect(self._download_worker.run)
        self._download_worker.progress.connect(self._on_download_progress)
        self._download_worker.finished.connect(self._on_download_finished)
        self._download_worker.error.connect(self._on_download_error)

        self._download_thread.start()

    def _on_download_progress(self, current: int, total: int):
        pct = int((current / max(1, total)) * 100)
        self.progress_map_download.setValue(pct)
        self.lbl_download_status.setText(f"Descargando teselas: {current} / {total} ({pct}%)")

    def _on_download_finished(self, count: int, meta: dict):
        self.btn_download_offline.setEnabled(True)
        self.btn_cancel_download.setEnabled(False)
        self.progress_map_download.setValue(100)
        self.lbl_download_status.setText(f"✓ Descarga completada: {count} teselas listas para uso offline.")
        self.txt_zone_name.clear()
        self._refresh_offline_metadata_display()
        self._cleanup_download_thread()
        self._log(f"Mapa offline actualizado con éxito ({count} teselas).")

    def _on_download_error(self, err_msg: str):
        self.btn_download_offline.setEnabled(True)
        self.btn_cancel_download.setEnabled(False)
        self.lbl_download_status.setText(f"Error en la descarga: {err_msg}")
        self._cleanup_download_thread()

    def _cancel_offline_download(self):
        if hasattr(self, "_download_worker") and self._download_worker:
            self._download_worker.cancel()
            self.lbl_download_status.setText("Cancelando descarga...")
            self.btn_cancel_download.setEnabled(False)

    def _cleanup_download_thread(self):
        if hasattr(self, "_download_thread") and self._download_thread:
            self._download_thread.quit()
            self._download_thread.wait(500)
            self._download_thread = None
            self._download_worker = None

    def _log(self, text: str):
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        self.txt_log.append(f"[{now_str}] {text}")

    def _update_clock_bar(self):
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        now_loc = datetime.datetime.now()
        self.lbl_clock.setText(f"UTC: {now_utc.strftime('%H:%M:%S')}  |  Local: {now_loc.strftime('%H:%M:%S')}")
        d = self.gps_reader.data
        if d.has_fix:
            sats = d.satellites
            offset = d.clock_offset_seconds
            self.lbl_gps_status.setText(f"GPS: Fix ({sats} sats)")
            self.lbl_gps_status.setStyleSheet("color: #10B981; font-weight: bold; font-size: 11px;")
            if hasattr(self, "lbl_gps_sync") and self.lbl_gps_sync:
                self.lbl_gps_sync.setText(f"GPS Sync: {offset:+.3f}s [OK]")
                self.lbl_gps_sync.setStyleSheet("color: #10B981; font-weight: bold; font-size: 11px; font-family: Consolas;")

            # Telemetría en pestaña de mapa
            if hasattr(self, "lbl_map_gps_status"):
                self.lbl_map_gps_status.setText(f"Estado: Fix satelital activo ({sats} satélites)")
                self.lbl_map_gps_status.setStyleSheet("font-weight: bold; color: #10B981;")
                self.lbl_map_coords.setText(f"Coordenadas: {d.latitude:.5f}°, {d.longitude:.5f}°")
                self.lbl_map_alt.setText(f"Altitud: {d.altitude_m:.1f} m  |  Satélites: {sats}")
                self.lbl_map_offset.setText(f"Desfase Reloj UTC: {offset:+.3f} s")

                # Actualización de marcador en mapa web (1 vez por segundo máx)
                if (time.time() - self._last_js_gps_update) > 1.0:
                    self._last_js_gps_update = time.time()
                    self.web_map_view.page().runJavaScript(
                        f"updateGPSPosition({d.latitude}, {d.longitude}, true, {sats});"
                    )

            # Sincronización con el Evaluador Astronómico del Calendario
            if hasattr(self, "tab_calendar") and self.tab_calendar:
                if abs(self.tab_calendar.current_lat - d.latitude) > 0.0001 or abs(self.tab_calendar.current_lon - d.longitude) > 0.0001:
                    self.tab_calendar.update_coordinates(d.latitude, d.longitude, d.altitude_m)
        elif d.connected:
            self.lbl_gps_status.setText("GPS: Buscando fix...")
            self.lbl_gps_status.setStyleSheet("color: #F59E0B; font-size: 11px;")
            if hasattr(self, "lbl_gps_sync") and self.lbl_gps_sync:
                self.lbl_gps_sync.setText("Reloj Local PC (Sin corrección GPS)")
                self.lbl_gps_sync.setStyleSheet("color: #F59E0B; font-size: 11px; font-family: Consolas;")
            if hasattr(self, "lbl_map_gps_status"):
                self.lbl_map_gps_status.setText("Estado: Buscando satélites...")
                self.lbl_map_gps_status.setStyleSheet("font-weight: bold; color: #F59E0B;")
        else:
            self.lbl_gps_status.setText("GPS VK-162: Desconectado")
            self.lbl_gps_status.setStyleSheet("color: #9CA3AF; font-size: 11px;")
            if hasattr(self, "lbl_gps_sync") and self.lbl_gps_sync:
                self.lbl_gps_sync.setText("Reloj Local PC (Sin corrección GPS)")
                self.lbl_gps_sync.setStyleSheet("color: #9CA3AF; font-size: 11px; font-family: Consolas;")
            if hasattr(self, "lbl_map_gps_status"):
                self.lbl_map_gps_status.setText("Estado: GPS no detectado en COM3")
                self.lbl_map_gps_status.setStyleSheet("font-weight: bold; color: #EF4444;")

        # Telemetría de cámaras en la barra superior
        if hasattr(self, "lbl_top_slot_a") and hasattr(self, "equipment_manager"):
            tel_a = self.equipment_manager.get_telemetry("A")
            tel_b = self.equipment_manager.get_telemetry("B")
            m_a = " [⭐ Master]" if tel_a["is_priority_master"] else ""
            dot_a = "●" if "Conectada" in tel_a["status"] else "○"
            self.lbl_top_slot_a.setText(f"{dot_a} Cámara Principal{m_a}: {tel_a['camera_name']} ({tel_a['battery_level']}%)")

            if not self.equipment_manager.slot_b.enabled:
                self.lbl_top_slot_b.setText("○ Cámara Secundaria: Deshabilitada")
                self.lbl_top_slot_b.setStyleSheet("color: #6B7280; font-size: 11px;")
            else:
                m_b = " [⭐ Master]" if tel_b["is_priority_master"] else ""
                dot_b = "●" if "Conectada" in tel_b["status"] else "○"
                self.lbl_top_slot_b.setText(f"{dot_b} Cámara Secundaria{m_b}: {tel_b['camera_name']} ({tel_b['battery_level']}%)")
                self.lbl_top_slot_b.setStyleSheet("color: #60A5FA; font-size: 11px;")

        # Actualización de telemetría de reloj en vivo para Ranura A y B
        if hasattr(self, "lbl_clock_cam_a") and hasattr(self, "equipment_manager"):
            slot_a = self.equipment_manager.slot_a
            if slot_a.enabled and slot_a.driver and slot_a.driver.connected:
                if slot_a.clock_time_str == "--:--:--":
                    self.equipment_manager.read_camera_clock("A", self.gps_reader.data)
                now_loc = datetime.datetime.now()
                cam_curr = now_loc + datetime.timedelta(seconds=slot_a.clock_delta_sec)
                slot_a.clock_time_str = cam_curr.strftime("%H:%M:%S")
                color_a = "#10B981" if slot_a.clock_sync_status == "synced" else ("#F59E0B" if slot_a.clock_sync_status == "drift" else "#EF4444")
                self.lbl_clock_cam_a.setText(f"🕒 Reloj: {slot_a.clock_time_str}")
                self.lbl_clock_delta_a.setText(f"[Δ GPS: {slot_a.clock_delta_sec:+.2f}s]")
                self.lbl_clock_delta_a.setStyleSheet(f"color: {color_a}; font-family: Consolas; font-size: 11px; font-weight: bold;")

        if hasattr(self, "lbl_clock_cam_b") and hasattr(self, "equipment_manager"):
            slot_b = self.equipment_manager.slot_b
            if not slot_b.enabled:
                self.lbl_clock_cam_b.setText("🕒 Reloj: Inactiva")
                self.lbl_clock_delta_b.setText("[--]")
                self.lbl_clock_delta_b.setStyleSheet("color: #6B7280; font-family: Consolas; font-size: 11px;")
            elif slot_b.driver and slot_b.driver.connected:
                if slot_b.clock_time_str == "--:--:--":
                    self.equipment_manager.read_camera_clock("B", self.gps_reader.data)
                now_loc = datetime.datetime.now()
                cam_curr = now_loc + datetime.timedelta(seconds=slot_b.clock_delta_sec)
                slot_b.clock_time_str = cam_curr.strftime("%H:%M:%S")
                color_b = "#10B981" if slot_b.clock_sync_status == "synced" else ("#F59E0B" if slot_b.clock_sync_status == "drift" else "#EF4444")
                self.lbl_clock_cam_b.setText(f"🕒 Reloj: {slot_b.clock_time_str}")
                self.lbl_clock_delta_b.setText(f"[Δ GPS: {slot_b.clock_delta_sec:+.2f}s]")
                self.lbl_clock_delta_b.setStyleSheet(f"color: {color_b}; font-family: Consolas; font-size: 11px; font-weight: bold;")

    def _init_equipment_tab(self) -> QWidget:
        """Construye la vista de Gestión de Equipamiento (Fase 1 v2.0)."""
        tab_eq = QWidget()
        layout = QVBoxLayout(tab_eq)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # 1. Barra de Control Global y Arbitraje de Prioridad
        bar_group = QGroupBox("Control Global de Equipamiento y Prioridad Temporal")
        bar_layout = QHBoxLayout(bar_group)

        self.btn_scan_usb = QPushButton("🔍 Escanear Dispositivos USB Nikon")
        self.btn_scan_usb.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold;")
        self.btn_scan_usb.clicked.connect(self._on_scan_usb)
        bar_layout.addWidget(self.btn_scan_usb)

        bar_layout.addSpacing(15)
        bar_layout.addWidget(QLabel("⭐ Cámara Principal (Prioridad en empate temporal):"))
        self.combo_master_priority = QComboBox()
        self.combo_master_priority.addItems([
            "⭐ Cámara Principal (Master / T_0 prioritario)",
            "⭐ Cámara Secundaria (Master / T_0 prioritario)"
        ])
        self.combo_master_priority.currentIndexChanged.connect(self._on_master_priority_changed)
        bar_layout.addWidget(self.combo_master_priority)

        bar_layout.addSpacing(15)
        bar_layout.addWidget(QLabel("Ref. Horaria:"))
        self.combo_time_mode = QComboBox()
        self.combo_time_mode.addItems([
            "🕒 Hora Local (con GPS)",
            "🌐 Hora UTC Satelital"
        ])
        bar_layout.addWidget(self.combo_time_mode)

        self.btn_sync_all_clocks = QPushButton("⏱️ Sincronizar Relojes GPS")
        self.btn_sync_all_clocks.setStyleSheet("background-color: #0D9488; color: white; font-weight: bold;")
        self.btn_sync_all_clocks.clicked.connect(self._on_sync_all_clocks)
        bar_layout.addWidget(self.btn_sync_all_clocks)

        bar_layout.addStretch()

        self.btn_silent_mode = QPushButton("🔇 Silent Mode: ON")
        self.btn_silent_mode.setStyleSheet("background-color: #065F46; color: #6EE7B7; font-weight: bold;")
        self.btn_silent_mode.clicked.connect(self._toggle_silent_mode)
        bar_layout.addWidget(self.btn_silent_mode)

        self.btn_eq_reconnect = QPushButton("🔄 Reconectar Todo")
        self.btn_eq_reconnect.clicked.connect(self._reconnect_all_cameras)
        bar_layout.addWidget(self.btn_eq_reconnect)

        self.btn_eq_release = QPushButton("🔓 Liberar Controles (Ambas)")
        self.btn_eq_release.setStyleSheet("background-color: #4B5563; color: white;")
        self.btn_eq_release.clicked.connect(self._toggle_camera_screen)
        bar_layout.addWidget(self.btn_eq_release)

        # Referencias de compatibilidad
        self.btn_reconnect = self.btn_eq_reconnect
        self.btn_toggle_screen = self.btn_eq_release

        layout.addWidget(bar_group)

        # 2. Tarjetas Independientes para Cámara Principal y Cámara Secundaria
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        # --- Tarjeta Cámara Principal ---
        self.group_slot_a = QGroupBox("Cámara Principal")
        slot_a_layout = QVBoxLayout(self.group_slot_a)
        slot_a_layout.setSpacing(8)

        self.lbl_badge_a = QLabel("⭐ MASTER / PRIORIDAD MÁXIMA (T_0)")
        self.lbl_badge_a.setStyleSheet("background-color: #064E3B; color: #34D399; font-weight: bold; padding: 4px 8px; border-radius: 4px;")
        slot_a_layout.addWidget(self.lbl_badge_a)

        slot_a_layout.addWidget(QLabel("Cámara / Controlador:"))
        self.combo_dev_a = QComboBox()
        self.combo_dev_a.addItems([
            "Nikon Z5 II (Simulada)",
            "Nikon Z5 II (SDK Oficial Plug&Play)",
            "Nikon Z5 II (USB PTP WinUSB)",
            "Nikon D750 (SDK Oficial Plug&Play)",
            "Nikon D750 (Simulada DSLR)",
            "Nikon Legacy (libgphoto2)"
        ])
        self.combo_dev_a.currentTextChanged.connect(self._on_device_a_changed)
        slot_a_layout.addWidget(self.combo_dev_a)

        # Asignación de compatibilidad con selector PoC para tests existentes
        self.combo_camera = self.combo_dev_a

        slot_a_layout.addWidget(QLabel("Configuración Óptica:"))
        self.txt_optic_a = QLineEdit("Telescopio ED80 600mm f/7.5")
        self.txt_optic_a.setStyleSheet("background-color: #1E222A; color: #ECEFF4; padding: 5px;")
        self.txt_optic_a.textChanged.connect(self._on_optic_a_changed)
        slot_a_layout.addWidget(self.txt_optic_a)

        # Telemetría Cámara Principal
        tele_a_layout = QHBoxLayout()
        self.lbl_status_a = QLabel("● Estado: Conectada")
        self.lbl_status_a.setStyleSheet("color: #10B981; font-weight: bold;")
        self.lbl_battery_a = QLabel("🔋 Batería: 95%")
        self.lbl_battery_a.setStyleSheet("color: #60A5FA;")
        self.lbl_sd_a = QLabel("💾 SD: ~1420 disparos")
        self.lbl_sd_a.setStyleSheet("color: #9CA3AF;")
        tele_a_layout.addWidget(self.lbl_status_a)
        tele_a_layout.addWidget(self.lbl_battery_a)
        tele_a_layout.addWidget(self.lbl_sd_a)
        slot_a_layout.addLayout(tele_a_layout)

        # Telemetría de Reloj Cámara Principal
        clock_a_layout = QHBoxLayout()
        self.lbl_clock_cam_a = QLabel("🕒 Reloj: --:--:--")
        self.lbl_clock_cam_a.setStyleSheet("color: #E2E8F0; font-family: Consolas; font-size: 11px;")
        self.lbl_clock_delta_a = QLabel("[Δ GPS: --s]")
        self.lbl_clock_delta_a.setStyleSheet("color: #F59E0B; font-family: Consolas; font-size: 11px; font-weight: bold;")
        self.btn_sync_clock_a = QPushButton("⏱️ Sincronizar Reloj")
        self.btn_sync_clock_a.setStyleSheet("background-color: #0F766E; color: white; font-size: 11px; padding: 3px 8px;")
        self.btn_sync_clock_a.clicked.connect(self._on_sync_clock_a)
        clock_a_layout.addWidget(self.lbl_clock_cam_a)
        clock_a_layout.addWidget(self.lbl_clock_delta_a)
        clock_a_layout.addStretch()
        clock_a_layout.addWidget(self.btn_sync_clock_a)
        slot_a_layout.addLayout(clock_a_layout)

        # Botones Cámara Principal
        btn_a_layout = QHBoxLayout()
        self.btn_test_shot_a = QPushButton("⚡ Disparo de Prueba (Principal)")
        self.btn_test_shot_a.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold;")
        self.btn_test_shot_a.clicked.connect(self._on_test_shot_a)
        btn_a_layout.addWidget(self.btn_test_shot_a)

        self.btn_liveview_a = QPushButton("👁️ Abrir Live View")
        self.btn_liveview_a.setStyleSheet("background-color: #059669; color: white; font-weight: bold;")
        self.btn_liveview_a.clicked.connect(self._goto_liveview_a)
        btn_a_layout.addWidget(self.btn_liveview_a)

        self.btn_release_a = QPushButton("🔓 Liberar Cámara Principal")
        self.btn_release_a.clicked.connect(self._on_release_a)
        btn_a_layout.addWidget(self.btn_release_a)
        slot_a_layout.addLayout(btn_a_layout)

        cards_layout.addWidget(self.group_slot_a, stretch=1)

        # --- Tarjeta Cámara Secundaria ---
        self.group_slot_b = QGroupBox("Cámara Secundaria (Habilitada)")
        self.group_slot_b.setCheckable(True)
        self.group_slot_b.setChecked(True)
        self.group_slot_b.toggled.connect(self._on_slot_b_toggled)
        slot_b_layout = QVBoxLayout(self.group_slot_b)
        slot_b_layout.setSpacing(8)

        self.lbl_badge_b = QLabel("SLAVE / MICRO-ESCALONAMIENTO (+30 ms)")
        self.lbl_badge_b.setStyleSheet("background-color: #1E293B; color: #94A3B8; font-weight: bold; padding: 4px 8px; border-radius: 4px;")
        slot_b_layout.addWidget(self.lbl_badge_b)

        slot_b_layout.addWidget(QLabel("Cámara / Controlador:"))
        self.combo_dev_b = QComboBox()
        self.combo_dev_b.addItems([
            "Nikon D750 (Simulada DSLR)",
            "Nikon D750 (SDK Oficial Plug&Play)",
            "Nikon Z5 II (Simulada)",
            "Nikon Z5 II (SDK Oficial Plug&Play)",
            "Nikon Z5 II (USB PTP WinUSB)",
            "Nikon Legacy (libgphoto2)"
        ])
        self.combo_dev_b.currentTextChanged.connect(self._on_device_b_changed)
        slot_b_layout.addWidget(self.combo_dev_b)

        slot_b_layout.addWidget(QLabel("Configuración Óptica:"))
        self.txt_optic_b = QLineEdit("Nikkor 24-70mm @ 24mm f/5.6")
        self.txt_optic_b.setStyleSheet("background-color: #1E222A; color: #ECEFF4; padding: 5px;")
        self.txt_optic_b.textChanged.connect(self._on_optic_b_changed)
        slot_b_layout.addWidget(self.txt_optic_b)

        # Telemetría Cámara Secundaria
        tele_b_layout = QHBoxLayout()
        self.lbl_status_b = QLabel("● Estado: Conectada")
        self.lbl_status_b.setStyleSheet("color: #10B981; font-weight: bold;")
        self.lbl_battery_b = QLabel("🔋 Batería: 88%")
        self.lbl_battery_b.setStyleSheet("color: #60A5FA;")
        self.lbl_sd_b = QLabel("💾 SD: ~850 disparos")
        self.lbl_sd_b.setStyleSheet("color: #9CA3AF;")
        tele_b_layout.addWidget(self.lbl_status_b)
        tele_b_layout.addWidget(self.lbl_battery_b)
        tele_b_layout.addWidget(self.lbl_sd_b)
        slot_b_layout.addLayout(tele_b_layout)

        # Telemetría de Reloj Cámara Secundaria
        clock_b_layout = QHBoxLayout()
        self.lbl_clock_cam_b = QLabel("🕒 Reloj: --:--:--")
        self.lbl_clock_cam_b.setStyleSheet("color: #E2E8F0; font-family: Consolas; font-size: 11px;")
        self.lbl_clock_delta_b = QLabel("[Δ GPS: --s]")
        self.lbl_clock_delta_b.setStyleSheet("color: #F59E0B; font-family: Consolas; font-size: 11px; font-weight: bold;")
        self.btn_sync_clock_b = QPushButton("⏱️ Sincronizar Reloj")
        self.btn_sync_clock_b.setStyleSheet("background-color: #0F766E; color: white; font-size: 11px; padding: 3px 8px;")
        self.btn_sync_clock_b.clicked.connect(self._on_sync_clock_b)
        clock_b_layout.addWidget(self.lbl_clock_cam_b)
        clock_b_layout.addWidget(self.lbl_clock_delta_b)
        clock_b_layout.addStretch()
        clock_b_layout.addWidget(self.btn_sync_clock_b)
        slot_b_layout.addLayout(clock_b_layout)

        # Botones Cámara Secundaria
        btn_b_layout = QHBoxLayout()
        self.btn_test_shot_b = QPushButton("⚡ Disparo de Prueba (Secundaria)")
        self.btn_test_shot_b.setStyleSheet("background-color: #4338CA; color: white; font-weight: bold;")
        self.btn_test_shot_b.clicked.connect(self._on_test_shot_b)
        btn_b_layout.addWidget(self.btn_test_shot_b)

        self.btn_liveview_b = QPushButton("👁️ Abrir Live View")
        self.btn_liveview_b.setStyleSheet("background-color: #059669; color: white; font-weight: bold;")
        self.btn_liveview_b.clicked.connect(self._goto_liveview_b)
        btn_b_layout.addWidget(self.btn_liveview_b)

        self.btn_release_b = QPushButton("🔓 Liberar Cámara Secundaria")
        self.btn_release_b.clicked.connect(self._on_release_b)
        btn_b_layout.addWidget(self.btn_release_b)
        slot_b_layout.addLayout(btn_b_layout)

        cards_layout.addWidget(self.group_slot_b, stretch=1)
        layout.addLayout(cards_layout)

        # 3. Módulo Inferior: Verificación de Disparo Dual y Arbitraje
        dual_group = QGroupBox("Verificación de Concurrencia y Árbitro de Prioridad")
        dual_layout = QVBoxLayout(dual_group)

        self.btn_test_dual = QPushButton("⚡ Disparo Dual Simultáneo (Verificar Micro-escalonamiento +30 ms)")
        self.btn_test_dual.setStyleSheet("background-color: #6D28D9; color: white; font-weight: bold; padding: 10px;")
        self.btn_test_dual.clicked.connect(self._on_test_dual_shot)
        dual_layout.addWidget(self.btn_test_dual)

        self.lbl_dual_result = QLabel("Sin disparos duales realizados aún.")
        self.lbl_dual_result.setStyleSheet("color: #A0AEC0; font-family: Consolas; font-size: 11px;")
        dual_layout.addWidget(self.lbl_dual_result)

        layout.addWidget(dual_group)
        layout.addStretch()
        return tab_eq

    def _goto_equipment_tab(self):
        self.tabs.setCurrentWidget(self.tab_equipment)

    def _on_scan_usb(self):
        devs = self.equipment_manager.scan_usb_devices()
        self._log(f"Escaneo USB completado: {len(devs)} dispositivos Nikon detectados.")
        if devs:
            for d in devs:
                self._log(f"  -> {d.display_name} ({d.driver_type})")
                name = d.display_name
                if self.combo_dev_a.findText(name) == -1:
                    self.combo_dev_a.addItem(name)
                if self.combo_dev_b.findText(name) == -1:
                    self.combo_dev_b.addItem(name)
            QMessageBox.information(
                self,
                "Dispositivos USB Detectados",
                f"Se han detectado {len(devs)} dispositivos Nikon en el bus USB:\n" +
                "\n".join([f"• {d.display_name}" for d in devs])
            )
        else:
            self._log("Escaneo USB: No se detectaron dispositivos Nikon físicos conectados. Utilizando modo simulado.")
            QMessageBox.information(
                self,
                "Escaneo USB Nikon",
                "No se detectaron cámaras Nikon físicas conectadas por USB.\n"
                "Puede continuar utilizando los modos simulados para pruebas de secuencia."
            )

    def _on_slot_b_toggled(self, checked: bool):
        self.equipment_manager.set_slot_enabled("B", checked)
        title = "Cámara Secundaria (Habilitada)" if checked else "Cámara Secundaria (Deshabilitada)"
        self.group_slot_b.setTitle(title)

        # Deshabilitar controles duales si solo hay 1 cámara activa
        self.btn_test_dual.setEnabled(checked)
        self.combo_master_priority.setEnabled(checked)

        if not checked:
            self._log("[EQUIPAMIENTO] Cámara Secundaria desactivada.")
        else:
            self._log("[EQUIPAMIENTO] Cámara Secundaria reactivada.")
            self._reconnect_all_cameras()

        # Actualizar visualización en el timeline
        if hasattr(self, "timeline_widget") and self.timeline_widget:
            self.timeline_widget.set_track_b_enabled(checked)

        # Refrescar eventos activos en Secuencia & Control
        self._refresh_active_schedule_views()
        self._update_equipment_ui()

    def _get_active_schedule(self) -> list[EclipseEvent]:
        """Devuelve los eventos activos según si Ranura B está habilitada o no."""
        if getattr(self.equipment_manager.slot_b, "enabled", True):
            return self.current_schedule
        return [ev for ev in self.current_schedule if getattr(ev, "camera_slot", "A").upper().strip() != "B"]

    def _refresh_active_schedule_views(self):
        active = self._get_active_schedule()
        contacts = getattr(self, "active_contacts", None)
        if not contacts:
            now = time.time()
            contacts = {
                "C1": now - 30.0,
                "C2": now + 5.0,
                "MAX": now + 10.0,
                "C3": now + 15.0,
                "C4": now + 45.0,
                "U2": now + 5.0,
                "U3": now + 30.0,
            }
        if hasattr(self, "timeline_widget") and self.timeline_widget:
            self.timeline_widget.set_events(active, contacts)
        if hasattr(self, "execution_log") and self.execution_log:
            self.execution_log.set_schedule(active, contacts)
        self._populate_table()

    def _on_master_priority_changed(self, idx: int):
        if not self.equipment_manager.slot_b.enabled:
            self.combo_master_priority.blockSignals(True)
            self.combo_master_priority.setCurrentIndex(0)
            self.combo_master_priority.blockSignals(False)
            return
        master_slot = "A" if idx == 0 else "B"
        self.equipment_manager.set_priority_master(master_slot)
        cam_name = "Cámara Principal" if master_slot == "A" else "Cámara Secundaria"
        self._log(f"Prioridad Master de disparo asignada a {cam_name} (T_0 garantizado).")
        self._update_equipment_ui()

    def _on_optic_a_changed(self, text: str):
        self.equipment_manager.slot_a.optical_setup = text

    def _on_optic_b_changed(self, text: str):
        self.equipment_manager.slot_b.optical_setup = text

    def _on_device_a_changed(self, text: str):
        self._apply_device_to_slot("A", text)

    def _on_device_b_changed(self, text: str):
        self._apply_device_to_slot("B", text)

    def _apply_device_to_slot(self, slot_id: str, choice: str):
        dev_type = "mock_z"
        if "D750 (SDK Oficial)" in choice or ("D750" in choice and "SDK" in choice):
            dev_type = "nikon_d750_sdk"
        elif "SDK Oficial" in choice or ("Z5" in choice and "SDK" in choice):
            dev_type = "nikon_z_sdk"
        elif "WinUSB" in choice or "PTP" in choice:
            dev_type = "ptp"
        elif "D750" in choice:
            dev_type = "mock_d750"
        elif "gphoto" in choice:
            dev_type = "gphoto"
        else:
            dev_type = "mock_z"

        discovered = None
        for d in self.equipment_manager.discovered_devices:
            if d.display_name == choice:
                discovered = d
                dev_type = d.driver_type
                break

        ok = self.equipment_manager.assign_camera(slot_id, dev_type, camera_name=choice, discovered_dev=discovered)
        cam_label = "Cámara Principal" if slot_id == "A" else "Cámara Secundaria"
        if ok:
            self._log(f"{cam_label}: Conectada con {choice}.")
        else:
            self._log(f"[AVISO] {cam_label}: No se pudo conectar con {choice}.")
        self._update_equipment_ui()

    def _on_test_shot_a(self):
        self._log(f"Disparo de prueba individual en Cámara Principal ({self.equipment_manager.slot_a.optical_setup})...")
        ok = self.equipment_manager.test_shot("A")
        if ok:
            self._log("Disparo Cámara Principal exitoso.")
            self.audio.beep()
        else:
            self._log("[ERROR] Fallo en disparo Cámara Principal.")
        self._update_equipment_ui()

    def _on_test_shot_b(self):
        if not self.equipment_manager.slot_b.enabled:
            self._log("[AVISO] Cámara Secundaria está deshabilitada.")
            return
        self._log(f"Disparo de prueba individual en Cámara Secundaria ({self.equipment_manager.slot_b.optical_setup})...")
        ok = self.equipment_manager.test_shot("B")
        if ok:
            self._log("Disparo Cámara Secundaria exitoso.")
            self.audio.beep()
        else:
            self._log("[ERROR] Fallo en disparo Cámara Secundaria.")
        self._update_equipment_ui()

    def _on_release_a(self):
        drv = self.equipment_manager.slot_a.driver
        if drv and drv.connected:
            drv.disconnect()
            self.equipment_manager.slot_a.status = "Liberada (Manual)"
            self._log("Cámara Principal liberada (menús / LCD activos).")
        else:
            if drv and drv.connect():
                self.equipment_manager.slot_a.status = "Conectada"
                self._log("Cámara Principal reconectada.")
        self._update_equipment_ui()

    def _on_release_b(self):
        if not self.equipment_manager.slot_b.enabled:
            return
        drv = self.equipment_manager.slot_b.driver
        if drv and drv.connected:
            drv.disconnect()
            self.equipment_manager.slot_b.status = "Liberada (Manual)"
            self._log("Cámara Secundaria liberada (menús / LCD activos).")
        else:
            if drv and drv.connect():
                self.equipment_manager.slot_b.status = "Conectada"
                self._log("Cámara Secundaria reconectada.")
        self._update_equipment_ui()

    def _on_test_dual_shot(self):
        self._log("Ejecutando disparo dual simultáneo con Árbitro de Prioridad...")
        report = self.dispatcher.trigger_dual_simultaneous()
        m_slot = report["master_slot"]
        s_slot = report["slave_slot"]
        delta = report["delta_ms"]
        res_str = (
            f"✔ Disparo Dual: Master ({m_slot}) ejecutado en T_0. "
            f"Secundaria ({s_slot}) ejecutada tras +{delta:.1f} ms. "
            f"Arbitraje anti-colisión USB xHCI OK."
        )
        self.lbl_dual_result.setText(res_str)
        self.lbl_dual_result.setStyleSheet("color: #10B981; font-weight: bold; font-family: Consolas;")
        self._log(res_str)
        self.audio.beep()
        self._update_equipment_ui()

    def _reconnect_all_cameras(self):
        self.equipment_manager.reconnect_camera_controls()
        self._log("Reconexión de todas las cámaras solicitada.")
        self._update_equipment_ui()

    def _on_sync_clock_a(self):
        use_utc = self.combo_time_mode.currentIndex() == 1 if hasattr(self, "combo_time_mode") else False
        ok, msg, delta = self.equipment_manager.sync_camera_clock("A", self.gps_reader.data, use_utc=use_utc)
        self._log(f"[Equipamiento] Cámara Principal: {msg}")
        self._update_equipment_ui()

    def _on_sync_clock_b(self):
        use_utc = self.combo_time_mode.currentIndex() == 1 if hasattr(self, "combo_time_mode") else False
        ok, msg, delta = self.equipment_manager.sync_camera_clock("B", self.gps_reader.data, use_utc=use_utc)
        self._log(f"[Equipamiento] Cámara Secundaria: {msg}")
        self._update_equipment_ui()

    def _on_sync_all_clocks(self):
        use_utc = self.combo_time_mode.currentIndex() == 1 if hasattr(self, "combo_time_mode") else False
        results = self.equipment_manager.sync_all_cameras(self.gps_reader.data, use_utc=use_utc)
        for slot_id, (ok, msg, delta) in results.items():
            cam_lbl = "Cámara Principal" if slot_id == "A" else "Cámara Secundaria"
            self._log(f"[Equipamiento] {cam_lbl}: {msg}")
        self._update_equipment_ui()

    def _update_equipment_ui(self):
        if not hasattr(self, "lbl_status_a"):
            return
        tel_a = self.equipment_manager.get_telemetry("A")
        self.lbl_status_a.setText(f"● Estado: {tel_a['status']}")
        self.lbl_status_a.setStyleSheet(
            "color: #10B981; font-weight: bold;" if "Conectada" in tel_a["status"] else "color: #EF4444; font-weight: bold;"
        )
        self.lbl_battery_a.setText(f"🔋 Batería: {tel_a['battery_level']}%")
        self.lbl_sd_a.setText(f"💾 SD: ~{tel_a['sd_free_shots']} disparos")
        if hasattr(self, "lbl_clock_cam_a") and tel_a.get("clock_time_str") and tel_a["clock_time_str"] != "--:--:--":
            color_a = "#10B981" if tel_a.get("clock_sync_status") == "synced" else ("#F59E0B" if tel_a.get("clock_sync_status") == "drift" else "#EF4444")
            self.lbl_clock_cam_a.setText(f"🕒 Reloj: {tel_a['clock_time_str']}")
            self.lbl_clock_delta_a.setText(f"[Δ GPS: {tel_a.get('clock_delta_sec', 0.0):+.2f}s]")
            self.lbl_clock_delta_a.setStyleSheet(f"color: {color_a}; font-family: Consolas; font-size: 11px; font-weight: bold;")

        is_b_enabled = self.equipment_manager.slot_b.enabled
        tel_b = self.equipment_manager.get_telemetry("B")

        if not is_b_enabled:
            self.lbl_status_b.setText("○ Estado: Deshabilitada")
            self.lbl_status_b.setStyleSheet("color: #6B7280; font-weight: bold;")
            self.lbl_battery_b.setText("🔋 Batería: --")
            self.lbl_sd_b.setText("💾 SD: --")
            if hasattr(self, "lbl_clock_cam_b"):
                self.lbl_clock_cam_b.setText("🕒 Reloj: Inactiva")
                self.lbl_clock_delta_b.setText("[--]")
                self.lbl_clock_delta_b.setStyleSheet("color: #6B7280; font-family: Consolas; font-size: 11px;")
                if hasattr(self, "btn_sync_clock_b"):
                    self.btn_sync_clock_b.setEnabled(False)
            self.btn_test_dual.setEnabled(False)
            self.combo_master_priority.setEnabled(False)
            self.lbl_top_slot_b.setText("○ Cámara Secundaria: Deshabilitada")
            self.lbl_top_slot_b.setStyleSheet("color: #6B7280; font-size: 11px;")
        else:
            self.lbl_status_b.setText(f"● Estado: {tel_b['status']}")
            self.lbl_status_b.setStyleSheet(
                "color: #10B981; font-weight: bold;" if "Conectada" in tel_b["status"] else "color: #EF4444; font-weight: bold;"
            )
            self.lbl_battery_b.setText(f"🔋 Batería: {tel_b['battery_level']}%")
            self.lbl_sd_b.setText(f"💾 SD: ~{tel_b['sd_free_shots']} disparos")
            if hasattr(self, "lbl_clock_cam_b"):
                if hasattr(self, "btn_sync_clock_b"):
                    self.btn_sync_clock_b.setEnabled(True)
                if tel_b.get("clock_time_str") and tel_b["clock_time_str"] != "--:--:--":
                    color_b = "#10B981" if tel_b.get("clock_sync_status") == "synced" else ("#F59E0B" if tel_b.get("clock_sync_status") == "drift" else "#EF4444")
                    self.lbl_clock_cam_b.setText(f"🕒 Reloj: {tel_b['clock_time_str']}")
                    self.lbl_clock_delta_b.setText(f"[Δ GPS: {tel_b.get('clock_delta_sec', 0.0):+.2f}s]")
                    self.lbl_clock_delta_b.setStyleSheet(f"color: {color_b}; font-family: Consolas; font-size: 11px; font-weight: bold;")
            self.btn_test_dual.setEnabled(True)
            self.combo_master_priority.setEnabled(True)

        if tel_a["is_priority_master"] or not is_b_enabled:
            self.lbl_badge_a.setText("⭐ MASTER / PRIORIDAD MÁXIMA (T_0)")
            self.lbl_badge_a.setStyleSheet("background-color: #064E3B; color: #34D399; font-weight: bold; padding: 4px 8px; border-radius: 4px;")
            self.lbl_badge_b.setText("SLAVE / MICRO-ESCALONAMIENTO (+30 ms)")
            self.lbl_badge_b.setStyleSheet("background-color: #1E293B; color: #94A3B8; font-weight: bold; padding: 4px 8px; border-radius: 4px;")
            self.combo_master_priority.blockSignals(True)
            self.combo_master_priority.setCurrentIndex(0)
            self.combo_master_priority.blockSignals(False)
            self.lbl_top_slot_a.setText(f"● Cámara Principal [⭐ Master]: {tel_a['camera_name']} ({tel_a['battery_level']}%)")
            if not is_b_enabled:
                self.lbl_top_slot_b.setText("○ Cámara Secundaria: Deshabilitada")
                self.lbl_top_slot_b.setStyleSheet("color: #6B7280; font-size: 11px;")
            else:
                self.lbl_top_slot_b.setText(f"● Cámara Secundaria: {tel_b['camera_name']} ({tel_b['battery_level']}%)")
                self.lbl_top_slot_b.setStyleSheet("color: #60A5FA; font-size: 11px;")
        else:
            self.lbl_badge_b.setText("⭐ MASTER / PRIORIDAD MÁXIMA (T_0)")
            self.lbl_badge_b.setStyleSheet("background-color: #064E3B; color: #34D399; font-weight: bold; padding: 4px 8px; border-radius: 4px;")
            self.lbl_badge_a.setText("SLAVE / MICRO-ESCALONAMIENTO (+30 ms)")
            self.lbl_badge_a.setStyleSheet("background-color: #1E293B; color: #94A3B8; font-weight: bold; padding: 4px 8px; border-radius: 4px;")
            self.combo_master_priority.blockSignals(True)
            self.combo_master_priority.setCurrentIndex(1)
            self.combo_master_priority.blockSignals(False)
            self.lbl_top_slot_a.setText(f"● Cámara Principal: {tel_a['camera_name']} ({tel_a['battery_level']}%)")
            self.lbl_top_slot_b.setText(f"● Cámara Secundaria [⭐ Master]: {tel_b['camera_name']} ({tel_b['battery_level']}%)")
            self.lbl_top_slot_b.setStyleSheet("color: #60A5FA; font-size: 11px;")

        if hasattr(self, "tab_focus") and self.tab_focus:
            self.tab_focus.refresh_cameras()

    def _goto_liveview_a(self):
        """Conmuta a la pestaña de Enfoque y activa el Live View para Cámara Principal."""
        self.tab_focus.set_camera_slot("A")
        self.tabs.setCurrentWidget(self.tab_focus)
        self.tab_focus.start_liveview()

    def _goto_liveview_b(self):
        """Conmuta a la pestaña de Enfoque y activa el Live View para Cámara Secundaria."""
        if not self.equipment_manager.slot_b.enabled:
            self._log("[AVISO] Cámara Secundaria está deshabilitada.")
            return
        self.tab_focus.set_camera_slot("B")
        self.tabs.setCurrentWidget(self.tab_focus)
        self.tab_focus.start_liveview()

    def _on_camera_selection_changed(self, choice: str):
        """Método de compatibilidad con código PoC."""
        self._apply_device_to_slot("A", choice)

    def _reconnect_camera(self):
        """Método de compatibilidad con código PoC."""
        self._reconnect_all_cameras()

    def _get_preset_contacts(self, choice: str, now: float) -> dict:
        """Calcula los contactos astronómicos de simulación según el perfil seleccionado."""
        if "ECLIPSE_TEST" in choice or "Estrés" in choice or "BKT Hardware" in choice:
            return {
                "C1": now - 300.0,
                "C2": now + 60.0,
                "MAX": now + 90.0,
                "C3": now + 120.0,
                "C4": now + 400.0,
                "U2": now + 60.0,
                "U3": now + 120.0,
            }
        elif "Simulacro Real" in choice:
            return {
                "C1": now - 600.0,
                "C2": now + 300.0,
                "MAX": now + 450.0,
                "C3": now + 600.0,
                "C4": now + 1200.0,
                "U2": now + 300.0,
                "U3": now + 600.0,
            }
        elif "Simulacro" in choice:
            return {
                "C1": now - 30.0,
                "C2": now + 5.0,
                "MAX": now + 10.0,
                "C3": now + 15.0,
                "C4": now + 45.0,
                "U2": now + 5.0,
                "U3": now + 30.0,
            }
        elif self.active_contacts and "C2" in self.active_contacts:
            c2_raw = self.active_contacts["C2"]
            if abs(c2_raw - now) > 600.0:
                totality_dur = self.active_eclipse_result.totality_duration_s if self.active_eclipse_result else 120.0
                return {
                    "C1": now - 30.0,
                    "C2": now + 5.0,
                    "MAX": now + 5.0 + (totality_dur / 2.0),
                    "C3": now + 5.0 + totality_dur,
                    "C4": now + 5.0 + totality_dur + 30.0,
                    "U2": now + 5.0,
                    "U3": now + 5.0 + totality_dur,
                }
            return dict(self.active_contacts)
        else:
            return {
                "C1": now - 30.0,
                "C2": now + 5.0,
                "MAX": now + 10.0,
                "C3": now + 15.0,
                "C4": now + 45.0,
                "U2": now + 5.0,
                "U3": now + 30.0,
            }

    def _on_preset_changed(self, choice: str):
        if choice == "(Cargado desde Calendario)":
            return

        if "Anular" in choice:
            self.current_schedule = get_solar_eclipse_annular_preset()
        elif "BKT Hardware" in choice:
            self.current_schedule = get_bkt_hardware_preset()
        elif "ECLIPSE_TEST" in choice or "Estrés" in choice:
            self.current_schedule = get_eclipse_test_preset()
        elif "Simulacro Real" in choice:
            self.current_schedule = get_full_rehearsal_preset()
        elif "Simulacro" in choice:
            self.current_schedule = get_quick_rehearsal_preset()
        elif "Solar" in choice:
            self.current_schedule = get_solar_eclipse_2027_preset()
        else:
            self.current_schedule = get_lunar_eclipse_bracket_preset()

        now = time.time()
        contacts = self._get_preset_contacts(choice, now)
        is_annular = "Anular" in choice
        self.active_contacts = dict(contacts)
        self.is_simulation_mode = True
        self.active_preset_name = choice
        active_sched = self._get_active_schedule()
        if hasattr(self, "timeline_widget") and self.timeline_widget:
            self.timeline_widget.set_contacts(contacts, is_annular=is_annular)
            self.timeline_widget.set_events(active_sched, contacts)
        if hasattr(self, "execution_log") and self.execution_log:
            self.execution_log.set_schedule(active_sched, contacts)
        if hasattr(self, "next_banner") and self.next_banner:
            self.next_banner.set_contacts(contacts, is_annular=is_annular)
            self.next_banner.set_idle(f"Perfil: {choice}")
        if hasattr(self, "lbl_loaded_profile"):
            self.lbl_loaded_profile.setText(f"🧪 [SIMULACIÓN MANUAL] {choice}")
            self.lbl_loaded_profile.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 11px;")

        self._populate_table()
        self._log(f"Perfil cargado: {choice} ({len(active_sched)} disparos programados).")

    def _on_eclipse_activated(
        self,
        contacts: dict,
        eclipse_info: EclipseInfo,
        result: LocalEclipseResult,
        is_simulation: bool = False,
        preset_name: str = ""
    ):
        """Inyecta los contactos calculados directamente en el Secuenciador, Timeline y ExecutionLog."""
        self.active_eclipse_info = eclipse_info
        self.active_eclipse_result = result
        self.active_contacts = dict(contacts)
        self.is_simulation_mode = is_simulation
        self.active_preset_name = preset_name

        is_annular = (
            getattr(eclipse_info, "is_annular", False) or
            getattr(result, "visibility", "") == "annularity" or
            "anular" in getattr(eclipse_info, "name", "").lower() or
            "annular" in getattr(eclipse_info, "type", "").lower() or
            "Anular" in preset_name
        )

        # Asignar la secuencia de disparos según si es preset de simulación o eclipse solar/lunar/anular
        if preset_name:
            if "Anular" in preset_name:
                self.current_schedule = get_solar_eclipse_annular_preset()
            elif "BKT Hardware" in preset_name:
                self.current_schedule = get_bkt_hardware_preset()
            elif "ECLIPSE_TEST" in preset_name or "Estrés" in preset_name:
                self.current_schedule = get_eclipse_test_preset()
            elif "Simulacro Real" in preset_name:
                self.current_schedule = get_full_rehearsal_preset()
            elif "Simulacro Rápido" in preset_name or "12 seg" in preset_name:
                self.current_schedule = get_quick_rehearsal_preset()
            elif "Solar" in preset_name:
                self.current_schedule = get_solar_eclipse_2027_preset()
            elif "Lunar" in preset_name:
                self.current_schedule = get_lunar_eclipse_bracket_preset()
            else:
                self.current_schedule = get_quick_rehearsal_preset()
        elif getattr(eclipse_info, "is_simulation", False):
            self.current_schedule = get_quick_rehearsal_preset()
        elif is_annular:
            self.current_schedule = get_solar_eclipse_annular_preset()
        elif eclipse_info.is_lunar:
            self.current_schedule = get_lunar_eclipse_bracket_preset()
        else:
            self.current_schedule = get_solar_eclipse_2027_preset()

        active_sched = self._get_active_schedule()

        # 1. Actualizar Timeline
        if hasattr(self, "timeline_widget") and self.timeline_widget:
            self.timeline_widget.set_contacts(contacts, is_annular=is_annular)
            self.timeline_widget.set_events(active_sched, contacts)

        # 2. Actualizar Execution Log
        if hasattr(self, "execution_log") and self.execution_log:
            self.execution_log.set_schedule(active_sched, contacts)

        # 3. Actualizar Secuenciador si ya está activo
        if self.sequencer:
            self.sequencer.contacts = dict(contacts)

        # 4. Actualizar Banner NEXT
        if hasattr(self, "next_banner") and self.next_banner:
            self.next_banner.set_contacts(contacts, is_annular=is_annular)
            if is_simulation:
                p_txt = f" [{preset_name}]" if preset_name else ""
                self.next_banner.set_idle(f"🔴 SIMULACIÓN (C2 en 5m): {eclipse_info.name}{p_txt}")
            else:
                self.next_banner.set_idle(f"Eclipse: {eclipse_info.name} ({result.formatted_totality})")

        # 5. Actualizar etiqueta en cabecera de Secuencia
        if hasattr(self, "lbl_loaded_profile"):
            if is_simulation:
                p_txt = f" ({preset_name})" if preset_name else " (C2 en 5m)"
                self.lbl_loaded_profile.setText(f"🔴 [SIMULACIÓN 5m] {eclipse_info.name}{p_txt}")
                self.lbl_loaded_profile.setStyleSheet("color: #EA580C; font-weight: bold; font-size: 11px;")
            else:
                self.lbl_loaded_profile.setText(f"🟢 [ACTIVO REAL] {eclipse_info.name} ({result.formatted_totality})")
                self.lbl_loaded_profile.setStyleSheet("color: #10B981; font-weight: bold; font-size: 11px;")

        self._populate_table()

        # 6. Registro en consola
        c2_str = result.c2_iso if result.c2_iso else "--:--:--"
        dur_str = result.formatted_totality
        mode_str = "SIMULACIÓN (T+5min)" if is_simulation else "ACTIVO REAL"
        self._log(
            f"⚡ [CALENDARIO] Eclipse cargado en 1-clic ({mode_str}): {eclipse_info.name}. "
            f"Visibilidad: {result.visibility_label} | C2: {c2_str} | Duración: {dur_str} | {len(active_sched)} disparos."
        )

        # 7. Cambiar a la pestaña de Secuencia & Control
        if hasattr(self, "tabs"):
            self.tabs.setCurrentIndex(2)

    def _populate_table(self):
        active_sched = self._get_active_schedule()
        self.table_events.setRowCount(len(active_sched))
        for row, ev in enumerate(active_sched):
            contact_str = f"{ev.contact_ref} {ev.offset_seconds:+.1f}s"
            is_notice = not getattr(ev, "is_shot", True) or is_notice_event(ev)
            self.table_events.setItem(row, 0, QTableWidgetItem(contact_str))
            
            if is_notice:
                self.table_events.setItem(row, 1, QTableWidgetItem("--"))
                self.table_events.setItem(row, 2, QTableWidgetItem("--"))
            else:
                eff_shutter = adjust_shutter_ev(ev.shutter_speed, self.current_ev_offset)
                self.table_events.setItem(row, 1, QTableWidgetItem(eff_shutter))
                self.table_events.setItem(row, 2, QTableWidgetItem(f"ISO {ev.iso}"))
            self.table_events.setItem(row, 3, QTableWidgetItem(ev.description))

            status_item = QTableWidgetItem("Pendiente")
            status_item.setForeground(QColor("#9CA3AF"))
            self.table_events.setItem(row, 4, status_item)

    def _set_ev_offset(self, val: int):
        self.current_ev_offset = val
        sign = f"{val:+d}" if val != 0 else "0"
        self.lbl_current_ev.setText(f"Offset Activo: {sign} EV")
        if self.sequencer:
            self.sequencer.set_ev_offset(val)
        self._log(f"Compensación de exposición cambiada a {sign} EV.")
        # Actualizar velocidades en la tabla
        for row, ev in enumerate(self._get_active_schedule()):
            if not getattr(ev, "is_shot", True) or is_notice_event(ev):
                continue
            eff_shutter = adjust_shutter_ev(ev.shutter_speed, self.current_ev_offset)
            self.table_events.setItem(row, 1, QTableWidgetItem(eff_shutter))

    def _trigger_single_test_shot(self):
        self.camera.trigger_capture()
        self.audio.beep()
        self._log("Disparo de prueba manual ejecutado con éxito.")

    def _trigger_burst_shot(self):
        """Emite una ráfaga de 9 disparos rápidos (ideal para horquillado BKT)."""
        self._log("⚡ Iniciando ráfaga rápida de 9 tomas consecutivas...")
        self.audio.beep()
        success = self.camera.trigger_burst(count=9)
        if success:
            self._log("✔ Ráfaga completada con éxito. Actualizando visor de tarjeta...")
            QTimer.singleShot(1000, self._load_last_photo_preview)
        else:
            self._log("[AVISO] Ráfaga finalizada con avisos en algunos fotogramas.")

    def _trigger_burst_baily(self):
        """Emite una ráfaga de 18 tomas rápidas para Perlas de Baily a 1/4000s directas a tarjeta SD."""
        self._log("⚡ [BAILY] Iniciando ráfaga de 18 tomas a 1/4000s (ISO 100, SaveMedia=Card)...")
        self.audio.beep()
        self.camera.set_shutter_speed("1/4000")
        self.camera.set_iso("100")
        success = self.camera.trigger_burst(count=18)
        if success:
            self._log("✔ [BAILY] Ráfaga de 18 tomas completada con éxito.")
            QTimer.singleShot(1000, self._load_last_photo_preview)
        else:
            self._log("[AVISO] Ráfaga de Baily finalizada con avisos.")

    def _generate_active_backup_plan(self):
        """Genera y abre el Plan Manual de Emergencia del eclipse o perfil actualmente activo."""
        import os
        import webbrowser
        from core.backup_plan import generate_backup_plan_html

        eclipse_name = self.active_eclipse_info.name if self.active_eclipse_info else self.combo_preset.currentText()
        contacts = dict(self.active_contacts) if self.active_contacts else {}

        lat = self.download_target_lat
        lon = self.download_target_lon
        alt_m = 850.0
        vis = "totality"
        totality_s = 120.0
        sun_alt = 15.0
        sun_az = 280.0

        if self.active_eclipse_result:
            lat = self.active_eclipse_result.lat
            lon = self.active_eclipse_result.lon
            alt_m = self.active_eclipse_result.alt_m
            vis = self.active_eclipse_result.visibility
            totality_s = self.active_eclipse_result.totality_duration_s
            sun_alt = self.active_eclipse_result.sun_altitude_deg
            sun_az = self.active_eclipse_result.sun_azimuth_deg
        else:
            if "Anular" in eclipse_name or "annular" in eclipse_name.lower():
                vis = "annularity"
            if contacts and "C2" in contacts and "C3" in contacts:
                totality_s = max(0.0, contacts["C3"] - contacts["C2"])

        cam_name = "Nikon Z5 II"
        lens_info = "500mm f/8"
        if hasattr(self, "equipment_manager") and self.equipment_manager:
            slot_a = self.equipment_manager.slot_a
            if slot_a:
                if slot_a.driver and getattr(slot_a.driver, "camera_name", None):
                    cam_name = slot_a.driver.camera_name
                elif slot_a.assigned_device and getattr(slot_a.assigned_device, "model_name", None):
                    cam_name = slot_a.assigned_device.model_name
                if getattr(slot_a, "optical_setup", None):
                    lens_info = slot_a.optical_setup

        filename = "plan_manual_campo.html"
        out_dir = os.path.join(os.getcwd(), "plans")
        out_path = os.path.join(out_dir, filename)

        generate_backup_plan_html(
            eclipse_name=eclipse_name,
            location_name=f"Campamento eclipZe (Lat {lat:.4f}°, Lon {lon:.4f}°)",
            lat=lat,
            lon=lon,
            alt_m=alt_m,
            visibility=vis,
            totality_duration_s=totality_s,
            sun_altitude_deg=sun_alt,
            sun_azimuth_deg=sun_az,
            contacts=contacts,
            camera_name=cam_name,
            lens_info=lens_info,
            output_path=out_path
        )

        webbrowser.open(os.path.abspath(out_path))
        self._log(f"📄 [PLAN MANUAL] Hoja de ruta formal generada: {out_path}")
        QMessageBox.information(
            self,
            "Plan Manual Generado",
            f"El plan manual formal de emergencia se ha abierto en tu navegador:\n\n"
            f"{out_path}\n\n"
            "Pulsa Ctrl + P en el navegador para imprimirlo en 1 página A4 o guardarlo en PDF."
        )

    def _toggle_silent_mode(self):
        """Activa o desactiva el modo silencioso (Silent Photography) en la cámara."""
        current_silent = getattr(self.camera, "is_silent_mode", False)
        new_state = not current_silent
        if hasattr(self.camera, "set_silent_mode"):
            self.camera.set_silent_mode(new_state)
        if new_state:
            if hasattr(self, "btn_silent_mode") and self.btn_silent_mode:
                self.btn_silent_mode.setText("🔇 Silent Mode: ON")
                self.btn_silent_mode.setStyleSheet("background-color: #065F46; color: #6EE7B7; font-weight: bold;")
            if hasattr(self, "lbl_top_silent") and self.lbl_top_silent:
                self.lbl_top_silent.setText("🔇 Silencioso: ON")
                self.lbl_top_silent.setStyleSheet("color: #10B981; font-size: 11px; font-weight: bold;")
            self._log("[CÁMARA] Modo silencioso (Obturador Electrónico) ACTIVADO para prevenir trepidación a 500mm.")
        else:
            if hasattr(self, "btn_silent_mode") and self.btn_silent_mode:
                self.btn_silent_mode.setText("🔊 Silent Mode: OFF")
                self.btn_silent_mode.setStyleSheet("background-color: #4B5563; color: #D1D5DB;")
            if hasattr(self, "lbl_top_silent") and self.lbl_top_silent:
                self.lbl_top_silent.setText("🔊 Silencioso: OFF")
                self.lbl_top_silent.setStyleSheet("color: #9CA3AF; font-size: 11px;")
            self._log("[CÁMARA] Modo silencioso DESACTIVADO.")

    def _toggle_camera_screen(self):
        """Libera o reconecta la sesión PTP para permitir usar la pantalla y botón Play de la cámara."""
        if self.camera.connected:
            self.camera.disconnect()
            self.lbl_camera_status.setText("○ Liberada (Play / Menú Activo)")
            self.lbl_camera_status.setStyleSheet("color: #F59E0B; font-weight: bold;")
            if hasattr(self, "btn_eq_release") and self.btn_eq_release:
                self.btn_eq_release.setText("🔒 Conectar Cámara (Modo Disparo)")
                self.btn_eq_release.setStyleSheet("background-color: #059669; color: white; font-weight: bold;")
            self._log("CÁMARA LIBERADA: Sesión PTP cerrada. Ya puedes pulsar 'Play', ver fotos y usar la pantalla trasera.")
        else:
            if self.camera.connect():
                self.lbl_camera_status.setText("● Conectada (PTP)")
                self.lbl_camera_status.setStyleSheet("color: #10B981; font-weight: bold;")
                if hasattr(self, "btn_eq_release") and self.btn_eq_release:
                    self.btn_eq_release.setText("🔓 Liberar Controles (Ambas)")
                    self.btn_eq_release.setStyleSheet("background-color: #4B5563; color: white;")
                self._log("CÁMARA BLOQUEADA: Sesión PTP reabierta y lista para disparar.")
            else:
                self._log("[ERROR] No se pudo reconectar la cámara.")

    def _trigger_shot_and_preview(self):
        """Ejecuta un disparo de prueba y descarga automáticamente la vista previa."""
        if not self.camera.connected:
            self._toggle_camera_screen()

        # En modo SDK, activar temporalmente SaveMedia = 2 (Card + SDRAM) para transferir copia a PC
        if hasattr(self.camera, "set_save_media"):
            self.camera.set_save_media(2)

        success = self.camera.trigger_capture()

        # Restaurar a modo Card exclusivo (0) para no ralentizar futuras secuencias
        if hasattr(self.camera, "set_save_media"):
            self.camera.set_save_media(0)

        if success:
            self.audio.beep()
            self._log("Disparo de prueba emitido y guardado en tarjeta SD. Cargando miniatura...")
            QTimer.singleShot(900, self._load_last_photo_preview)
        else:
            self._log("[ERROR] Fallo al emitir disparo de prueba.")

    def _load_last_photo_preview(self):
        """Consulta la última foto en la tarjeta especificada y la renderiza en el visor."""
        slot = 1 if "1" in self.combo_slot.currentText() else 2
        self._log(f"Consultando última toma en la Ranura SD {slot} vía PTP...")
        thumb_bytes = self.camera.get_last_thumb(slot=slot)
        if thumb_bytes:
            pixmap = QPixmap()
            if pixmap.loadFromData(thumb_bytes):
                self._last_pixmap = pixmap
                scaled = pixmap.scaled(
                    self.lbl_preview_img.size().width() - 8,
                    self.lbl_preview_img.size().height() - 8,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.lbl_preview_img.setPixmap(scaled)
                self._log(f"¡Miniatura cargada de la Ranura SD {slot}! Haz clic sobre la imagen para ampliar.")
                return
        self._log(f"No se pudo cargar la vista previa de la Ranura SD {slot} (comprueba si hay fotos en esa tarjeta).")

    def _on_preview_clicked(self, event):
        """Abre un diálogo modal con la imagen ampliada al hacer clic en el visor."""
        if hasattr(self, "_last_pixmap") and self._last_pixmap and not self._last_pixmap.isNull():
            dialog = QDialog(self)
            dialog.setWindowTitle("eclipZe — Previsualización Ampliada")
            dialog.resize(850, 620)
            layout = QVBoxLayout(dialog)
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setPixmap(self._last_pixmap.scaled(820, 580, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            layout.addWidget(lbl)
            dialog.exec()

    def _start_sequence(self):
        # Corte de seguridad mandatorio: Live View debe apagarse inmediatamente ante cualquier intento de iniciar secuencia
        if hasattr(self, "tab_focus") and self.tab_focus and self.tab_focus.is_liveview_active():
            self.tab_focus.stop_liveview()
            self._log("[SEGURIDAD] Live View apagado automáticamente antes de iniciar la secuencia para enfriamiento de sensor.")

        if not self.current_schedule:
            self._log("[AVISO] No hay ningún eclipse ni secuencia cargada. Por favor, carga un evento desde el Calendario.")
            if self.isVisible():
                QMessageBox.warning(
                    self,
                    "Aviso",
                    "No hay ningún eclipse ni secuencia cargada.\n\nPor favor, dirígete a la pestaña '📅 Calendario de Eclipses' para cargar un evento astronómico o simulación."
                )
            return

        now = time.time()
        # Si ya hay contactos activos inyectados desde el Calendario (real o simulación a 5 min), respetarlos
        if self.active_contacts and "C2" in self.active_contacts:
            contacts = dict(self.active_contacts)
        else:
            choice = self.combo_preset.currentText()
            contacts = self._get_preset_contacts(choice, now)
            self.active_contacts = dict(contacts)

        if getattr(self, "is_simulation_mode", False):
            lead_time = max(0.0, contacts.get("C2", now) - now)
            totality_dur = contacts.get("C3", now + 120.0) - contacts.get("C2", now)
            self._log(f"[SIMULACIÓN] C2 programado a T+{lead_time:.0f}s con duración de {totality_dur:.1f}s.")
        elif self.active_eclipse_info:
            c2_ts = contacts.get("C2", now)
            dt_str = datetime.fromtimestamp(c2_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            self._log(f"[SECUENCIA REAL] Secuencia activa para {self.active_eclipse_info.name}: C2 programado a las {dt_str}.")

        active_schedule = self._get_active_schedule()
        if not active_schedule:
            self._log("[AVISO] No hay eventos activos en la secuencia.")
            if self.isVisible():
                QMessageBox.warning(self, "Error", "No hay eventos activos en la secuencia.")
            return

        # Reiniciar estados de eventos
        for ev in active_schedule:
            ev.executed = False
            ev.skipped = False

        self._populate_table()

        # Preparar Timeline y ExecutionLog en UI
        if hasattr(self, "timeline_widget") and self.timeline_widget:
            self.timeline_widget.set_contacts(contacts)
            self.timeline_widget.set_events(active_schedule, contacts)
            self.timeline_widget.start_animation(now)
        if hasattr(self, "execution_log") and self.execution_log:
            self.execution_log.set_schedule(active_schedule, contacts)

        self.sequencer = EclipseSequencer(
            contacts=contacts,
            schedule=active_schedule,
            camera=self.dispatcher,  # Control dual Cámara A y Cámara B
            audio=self.audio
        )
        self.sequencer.set_ev_offset(self.current_ev_offset)

        # Conectar callbacks del secuenciador a señales Qt
        self.sequencer.on_event_triggered = lambda ev, s, i: self.signals.shot_triggered.emit(ev, s, i)
        self.sequencer.on_event_skipped = lambda ev, d: self.signals.shot_skipped.emit(ev, d)
        self.sequencer.on_tick = lambda n, ev, t: self.signals.tick.emit(n, ev, t)
        self.sequencer.on_finished = lambda: self.signals.finished.emit()

        self.btn_start.setEnabled(False)
        self.btn_start.setText("⏳ SECUENCIA EN CURSO")
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #94A3B8;
                padding: 12px 20px;
                border-radius: 6px;
                border: 1px solid #334155;
                font-weight: bold;
            }
        """)
        self.btn_stop.setEnabled(True)
        self.combo_preset.setEnabled(False)
        self._log("▶ Secuencia iniciada.")
        self.sequencer.start()

    def _stop_sequence(self):
        if self.sequencer:
            self.sequencer.stop()
        if hasattr(self, "timeline_widget") and self.timeline_widget:
            self.timeline_widget.stop_animation()
        if hasattr(self, "next_banner") and self.next_banner:
            self.next_banner.set_idle("Secuencia detenida por el usuario.")
        self._on_finished()
        self._log("⏹ Secuencia detenida por el usuario.")

    def _on_shot_triggered(self, event: EclipseEvent, speed: str, iso: str):
        now = time.time()
        slot = getattr(event, "camera_slot", "A").upper()
        is_real_shot = getattr(event, "is_shot", True)

        if not is_real_shot:
            self._log(f"📢 AVISO [{slot}]: {event.description}")
        else:
            self.audio.beep()
            self._log(f"📸 DISPARO [{slot}]: {event.description} [{speed}, ISO {iso}]")

        # Telemetría en ExecutionLog y Timeline
        if hasattr(self, "execution_log") and self.execution_log:
            self.execution_log.record_shot(event, now, success=True, shutter=speed, iso=iso, camera_slot=slot)
        if hasattr(self, "timeline_widget") and self.timeline_widget:
            ev_id = getattr(event, "event_id", "") or event.description
            self.timeline_widget.update_event_status(ev_id, "executed")

        # Actualizar fila en tabla legacy para compatibilidad
        for row, ev in enumerate(self._get_active_schedule()):
            if ev == event:
                status_text = "✔ Aviso emitido" if not is_real_shot else "✔ Disparada"
                status_color = "#38BDF8" if not is_real_shot else "#10B981"
                status_item = QTableWidgetItem(status_text)
                status_item.setForeground(QColor(status_color))
                self.table_events.setItem(row, 4, status_item)
                break

    def _on_shot_skipped(self, event: EclipseEvent, delay: float):
        slot = getattr(event, "camera_slot", "A").upper()
        self._log(f"⚠ DROP-AND-SKIP [{slot}]: Omitida por retraso (+{delay*1000:.0f}ms): {event.description}")
        if hasattr(self, "execution_log") and self.execution_log:
            self.execution_log.record_skip(event, delay, camera_slot=slot)
        if hasattr(self, "timeline_widget") and self.timeline_widget:
            ev_id = getattr(event, "event_id", "") or event.description
            self.timeline_widget.update_event_status(ev_id, "skipped")

        for row, ev in enumerate(self._get_active_schedule()):
            if ev == event:
                status_item = QTableWidgetItem("⏭ Omitida")
                status_item.setForeground(QColor("#F59E0B"))
                self.table_events.setItem(row, 4, status_item)
                break

    def _on_tick(self, now: float, event: Optional[EclipseEvent], time_to_shot: float):
        # Actualización de Timeline Playhead y Banner NEXT dinámico
        if hasattr(self, "timeline_widget") and self.timeline_widget:
            # Si el timeline ya está animándose a 30 FPS de forma suave, no forzar saltos salvo desfase severo
            if not getattr(self.timeline_widget, "_is_animating", False):
                self.timeline_widget.set_playhead_time(now)
            else:
                drift = abs(self.timeline_widget.current_playhead_time - now)
                if drift > 2.5:
                    self.timeline_widget.set_playhead_time(now)
        if hasattr(self, "next_banner") and self.next_banner:
            contacts = getattr(self.sequencer, "contacts", None) or getattr(self, "active_contacts", None)
            self.next_banner.update_countdown(time_to_shot, event, now=now, contacts=contacts)

        if event:
            if time_to_shot > 0:
                self.lbl_countdown.setText(f"{time_to_shot:04.1f}s")
                self.lbl_countdown.setStyleSheet("color: #10B981;")
                self.lbl_target_info.setText(f"Próxima: {event.description} ({event.shutter_speed})")
            else:
                self.lbl_countdown.setText("DISPARANDO")
                self.lbl_countdown.setStyleSheet("color: #F59E0B;")

            # Corte de seguridad de Live View 2 min antes del disparo
            if hasattr(self, "tab_focus") and self.tab_focus and self.tab_focus.is_liveview_active():
                if self.tab_focus.check_safety_timeout(time_to_shot):
                    self._log("[SEGURIDAD] Live View apagado automáticamente (T - 2 min) para enfriar sensor y proteger batería.")

    def closeEvent(self, event):
        """Limpieza segura de timers y procesos al cerrar la ventana."""
        self.ui_timer.stop()
        if hasattr(self, "timeline_widget") and self.timeline_widget:
            self.timeline_widget.stop_animation()
        if hasattr(self, "tab_focus") and self.tab_focus:
            self.tab_focus.stop_liveview()
        if self.sequencer:
            self.sequencer.stop()
        self.gps_reader.stop()
        if hasattr(self, "_download_worker") and self._download_worker:
            self._download_worker.cancel()
        if hasattr(self, "_download_thread") and self._download_thread:
            self._download_thread.quit()
            self._download_thread.wait(500)
        self.map_server.stop()
        if hasattr(self, "equipment_manager") and self.equipment_manager:
            self.equipment_manager.release_camera_controls()
        event.accept()

    def _on_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_start.setText("▶ INICIAR SECUENCIA")
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #10B981;
            }
            QPushButton:disabled {
                background-color: #1E293B;
                color: #94A3B8;
                border: 1px solid #334155;
            }
        """)
        self.btn_stop.setEnabled(False)
        self.combo_preset.setEnabled(True)
        self.lbl_countdown.setText("COMPLETADO")
        self.lbl_countdown.setStyleSheet("color: #38BDF8;")
        self.lbl_target_info.setText("Secuencia finalizada.")
        if hasattr(self, "timeline_widget") and self.timeline_widget:
            self.timeline_widget.stop_animation()
        if hasattr(self, "next_banner") and self.next_banner:
            self.next_banner.set_finished()
        self._log("Secuencia completada con éxito.")
