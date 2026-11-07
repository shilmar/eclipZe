"""
Pestaña de Calendario de Eclipses (2026–2035) para eclipZe v2.0.
Permite explorar los grandes eventos de la década, evaluar la visibilidad y contactos locales
según las coordenadas activas del GPS/Mapa, y cargar el eclipse en 1-clic al secuenciador y timeline.
"""

from typing import Optional, List, Dict, Any
import json
from datetime import datetime, timezone
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QListWidget, QListWidgetItem,
    QFrame, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QMessageBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QFont, QColor
from PySide6.QtWebEngineWidgets import QWebEngineView

from core.eclipse_db import EclipseCatalogManager, EclipseInfo
from core.astronomy import calculate_local_eclipse, LocalEclipseResult
from core.map_manager import get_calendar_map_html


class EclipseCalendarWidget(QWidget):
    """
    Widget de Calendario y Evaluador Astronómico de Eclipses.
    """
    # Señal emitida cuando el usuario pulsa Cargar (Activo o Simulación)
    # Envía: (contacts_dict, eclipse_info, local_result, is_simulation, preset_name)
    eclipse_selected_as_active = Signal(dict, object, object, bool, str)

    def __init__(
        self,
        catalog_manager: Optional[EclipseCatalogManager] = None,
        parent: Optional[QWidget] = None,
        reference_date: Optional[str] = None,
        map_server: Optional[Any] = None
    ):
        super().__init__(parent)
        self.catalog = catalog_manager or EclipseCatalogManager()
        self.reference_date = reference_date
        self.map_server = map_server or (getattr(parent, "map_server", None) if parent else None)
        self.current_lat: float = 40.65406
        self.current_lon: float = -3.76918
        self.current_alt: float = 850.0
        self.selected_eclipse: Optional[EclipseInfo] = None
        self.last_result: Optional[LocalEclipseResult] = None
        self._map_ready: bool = False
        self._pending_eclipse_update: bool = False

        self._init_ui()
        self._load_eclipses_list()
        
        # Seleccionar por defecto el primer eclipse futuro disponible
        self._select_default_eclipse()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #262B34;
                width: 3px;
            }
        """)

        # Panel Izquierdo: Catálogo y Filtros (~20% ancho)
        left_panel = self._build_left_catalog_panel()
        splitter.addWidget(left_panel)

        # Panel Central: Visor de Mapa Interactivo con Capa de Trayectoria (~48% ancho)
        center_panel = self._build_center_map_panel()
        splitter.addWidget(center_panel)

        # Panel Derecho: Evaluador de Ubicación y Carga en 1-Clic (~32% ancho)
        right_panel = self._build_right_evaluator_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 5)
        splitter.setStretchFactor(2, 3)
        splitter.setSizes([260, 640, 420])
        main_layout.addWidget(splitter)

    # -------------------------------------------------------------------------
    # Panel Central: Visor de Mapa Interactivo Leaflet
    # -------------------------------------------------------------------------
    def _build_center_map_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # Cabecera del visor de mapa
        header = QHBoxLayout()
        lbl_map_title = QLabel("🗺️ Trayectoria y Franja del Eclipse")
        lbl_map_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl_map_title.setStyleSheet("color: #F3F4F6;")
        header.addWidget(lbl_map_title)

        header.addStretch()

        self.btn_recenter_map = QPushButton("🎯 Centrar en mi Posición")
        self.btn_recenter_map.setToolTip("Centra el mapa en tus coordenadas de observación actuales")
        self.btn_recenter_map.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #38BDF8;
                border: 1px solid #38BDF8;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0F172A;
                color: #FFFFFF;
            }
        """)
        self.btn_recenter_map.clicked.connect(self._recenter_map_on_observer)
        header.addWidget(self.btn_recenter_map)
        layout.addLayout(header)

        # Visor QWebEngineView con el mapa Leaflet
        self.web_map_view = QWebEngineView()
        self.web_map_view.setStyleSheet("border: 1px solid #2D323B; border-radius: 6px;")
        self.web_map_view.titleChanged.connect(self._on_map_title_changed)
        self.web_map_view.loadFinished.connect(self._on_map_load_finished)

        # Cargar URL del servidor o fallback HTML
        if self.map_server and hasattr(self.map_server, "calendar_url"):
            self.web_map_view.setUrl(QUrl(self.map_server.calendar_url))
        else:
            self.web_map_view.setHtml(get_calendar_map_html(), QUrl("http://127.0.0.1/"))

        layout.addWidget(self.web_map_view, stretch=1)

        # Leyenda / Hint interactivo
        lbl_hint = QLabel("💡 Clic en cualquier punto del mapa para mover tu punto de observación y recalcular al instante.")
        lbl_hint.setStyleSheet("color: #9CA3AF; font-size: 10px; font-style: italic;")
        lbl_hint.setWordWrap(True)
        layout.addWidget(lbl_hint)

        return panel

    # -------------------------------------------------------------------------
    # Panel Izquierdo: Catálogo
    # -------------------------------------------------------------------------
    def _build_left_catalog_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # Título
        title_box = QHBoxLayout()
        lbl_title = QLabel("📅 Catálogo de Eclipses 2026–2035")
        lbl_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_title.setStyleSheet("color: #F3F4F6;")
        title_box.addWidget(lbl_title)
        layout.addLayout(title_box)

        # Barra de búsqueda y filtro
        search_row = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Buscar por país, año o nombre...")
        self.txt_search.setStyleSheet("""
            QLineEdit {
                background-color: #16191F;
                border: 1px solid #2D323B;
                border-radius: 4px;
                color: #ECEFF4;
                padding: 6px 10px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #38BDF8;
            }
        """)
        self.txt_search.textChanged.connect(self._on_search_changed)
        search_row.addWidget(self.txt_search)

        self.combo_filter = QComboBox()
        self.combo_filter.setStyleSheet("""
            QComboBox {
                background-color: #16191F;
                border: 1px solid #2D323B;
                border-radius: 4px;
                color: #ECEFF4;
                padding: 5px 8px;
                font-size: 11px;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        self.combo_filter.addItems([
            "Todos los Eventos",
            "🇪🇸 Eclipses España",
            "☀️ Solares Totales",
            "🟡 Solares Anulares",
            "🌙 Eclipses Lunares",
            "🧪 Modo Simulación"
        ])
        self.combo_filter.currentIndexChanged.connect(self._on_filter_changed)
        search_row.addWidget(self.combo_filter)
        layout.addLayout(search_row)

        # Lista de tarjetas de eclipses
        self.list_eclipses = QListWidget()
        self.list_eclipses.setStyleSheet("""
            QListWidget {
                background-color: #121418;
                border: 1px solid #262B34;
                border-radius: 6px;
                padding: 4px;
                color: #E5E9F0;
            }
            QListWidget::item {
                background-color: #16191F;
                border: 1px solid #2D323B;
                border-radius: 6px;
                margin-bottom: 6px;
                padding: 8px;
            }
            QListWidget::item:hover {
                background-color: #1E232D;
                border-color: #4B5563;
            }
            QListWidget::item:selected {
                background-color: #1E293B;
                border: 1px solid #38BDF8;
            }
        """)
        self.list_eclipses.currentItemChanged.connect(self._on_eclipse_item_selected)
        layout.addWidget(self.list_eclipses)

        # Contador inferior
        self.lbl_count = QLabel("Eclipses cargados: --")
        self.lbl_count.setStyleSheet("color: #9CA3AF; font-size: 10px;")
        layout.addWidget(self.lbl_count)

        return panel

    # -------------------------------------------------------------------------
    # Panel Derecho: Evaluador de Ubicación
    # -------------------------------------------------------------------------
    def _build_right_evaluator_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(10)

        # Grupo: Coordenadas de Observación (1 sola fila horizontal)
        pos_group = QGroupBox("📍 Coordenadas de Observación (GPS / Mapa)")
        pos_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #2D323B;
                border-radius: 6px;
                margin-top: 6px;
                font-weight: bold;
                color: #38BDF8;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
        """)
        pos_layout = QHBoxLayout(pos_group)
        pos_layout.setContentsMargins(8, 8, 8, 8)
        pos_layout.setSpacing(6)

        # Latitud
        pos_layout.addWidget(QLabel("Lat:"))
        self.spin_lat = QDoubleSpinBox()
        self.spin_lat.setRange(-90.0, 90.0)
        self.spin_lat.setDecimals(5)
        self.spin_lat.setValue(self.current_lat)
        self.spin_lat.setSingleStep(0.01)
        self.spin_lat.setStyleSheet("background-color: #16191F; color: #ECEFF4; border: 1px solid #374151; padding: 3px;")
        self.spin_lat.valueChanged.connect(self._on_coords_edited)
        pos_layout.addWidget(self.spin_lat)

        # Longitud
        pos_layout.addWidget(QLabel("Lon:"))
        self.spin_lon = QDoubleSpinBox()
        self.spin_lon.setRange(-180.0, 180.0)
        self.spin_lon.setDecimals(5)
        self.spin_lon.setValue(self.current_lon)
        self.spin_lon.setSingleStep(0.01)
        self.spin_lon.setStyleSheet("background-color: #16191F; color: #ECEFF4; border: 1px solid #374151; padding: 3px;")
        self.spin_lon.valueChanged.connect(self._on_coords_edited)
        pos_layout.addWidget(self.spin_lon)

        # Altitud
        pos_layout.addWidget(QLabel("Alt:"))
        self.spin_alt = QDoubleSpinBox()
        self.spin_alt.setRange(-100.0, 9000.0)
        self.spin_alt.setDecimals(0)
        self.spin_alt.setSuffix(" m")
        self.spin_alt.setValue(self.current_alt)
        self.spin_alt.setSingleStep(50.0)
        self.spin_alt.setStyleSheet("background-color: #16191F; color: #ECEFF4; border: 1px solid #374151; padding: 3px;")
        self.spin_alt.valueChanged.connect(self._on_coords_edited)
        pos_layout.addWidget(self.spin_alt)

        # Botón para sincronizar desde coordenadas activas
        self.btn_sync_gps = QPushButton("📡 GPS")
        self.btn_sync_gps.setToolTip("Sincronizar con GPS o mapa activo")
        self.btn_sync_gps.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #3B82F6;
            }
        """)
        self.btn_sync_gps.clicked.connect(self._sync_with_parent_coords)
        pos_layout.addWidget(self.btn_sync_gps)

        layout.addWidget(pos_group)

        # Banner de Estado de Visibilidad Local
        self.banner_status = QFrame()
        self.banner_status.setStyleSheet("""
            QFrame {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        banner_layout = QHBoxLayout(self.banner_status)
        banner_layout.setContentsMargins(8, 6, 8, 6)

        self.lbl_vis_badge = QLabel("ESTADO VISIBILIDAD")
        self.lbl_vis_badge.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.lbl_vis_badge.setStyleSheet("""
            background-color: #A855F7;
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
        """)
        banner_layout.addWidget(self.lbl_vis_badge)

        self.lbl_vis_details = QLabel("Calculando contactos astronómicos locales...")
        self.lbl_vis_details.setStyleSheet("color: #E5E9F0; font-size: 12px; font-weight: 500;")
        self.lbl_vis_details.setWordWrap(True)
        banner_layout.addWidget(self.lbl_vis_details, stretch=1)

        layout.addWidget(self.banner_status)

        # Panel de Telemetría Astronómica (1 sola fila horizontal de 4 tarjetas)
        telemetry_box = QHBoxLayout()
        telemetry_box.setSpacing(6)

        # Tarjeta 1: Duración en Campamento / Totalidad
        self.card_duration = self._create_metric_card("DURACIÓN TOTALIDAD", "--", "#A855F7")
        telemetry_box.addWidget(self.card_duration)

        # Tarjeta 2: Altura del Sol
        self.card_sun_alt = self._create_metric_card("ELEVACIÓN SOLAR", "--", "#F59E0B")
        telemetry_box.addWidget(self.card_sun_alt)

        # Tarjeta 3: Oscurecimiento / Magnitud
        self.card_obscuration = self._create_metric_card("OSCURECIMIENTO", "--", "#38BDF8")
        telemetry_box.addWidget(self.card_obscuration)

        # Tarjeta 4: Azimut y Orientación
        self.card_azimuth = self._create_metric_card("AZIMUT SOLAR", "--", "#10B981")
        telemetry_box.addWidget(self.card_azimuth)

        layout.addLayout(telemetry_box)

        # Advertencia de sol bajo
        self.lbl_horizon_warning = QLabel("")
        self.lbl_horizon_warning.setStyleSheet("color: #F59E0B; font-weight: bold; font-size: 11px;")
        self.lbl_horizon_warning.setWordWrap(True)
        layout.addWidget(self.lbl_horizon_warning)

        # Tabla de Contactos Astronómicos UTC
        contacts_group = QGroupBox("Tiempos de Contacto Calculados (UTC y Local)")
        contacts_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #2D323B;
                border-radius: 6px;
                margin-top: 6px;
                font-weight: bold;
                color: #9CA3AF;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
        """)
        tbl_layout = QVBoxLayout(contacts_group)
        tbl_layout.setContentsMargins(6, 6, 6, 6)

        self.table_contacts = QTableWidget()
        self.table_contacts.setColumnCount(4)
        self.table_contacts.setHorizontalHeaderLabels(["Contacto", "Hora UTC", "Fase Física", "Duración / Detalle"])
        self.table_contacts.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_contacts.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_contacts.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_contacts.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_contacts.setStyleSheet("""
            QTableWidget {
                background-color: #121418;
                gridline-color: #262B34;
                color: #E5E9F0;
                border: 1px solid #2D323B;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #1E222A;
                color: #9CA3AF;
                border: 1px solid #262B34;
                padding: 4px;
                font-weight: bold;
            }
        """)
        tbl_layout.addWidget(self.table_contacts)

        # Nota de corrección topográfica
        self.lbl_alt_note = QLabel("🏔️ Corrección topográfica: 0.0s")
        self.lbl_alt_note.setStyleSheet("color: #9CA3AF; font-size: 11px;")
        tbl_layout.addWidget(self.lbl_alt_note)

        layout.addWidget(contacts_group)

        # Grupo: Banco de Ensayos y Modos de Prueba (visible si es Simulación)
        self.sim_config_group = QGroupBox("🧪 Configuración de Modos de Ensayo")
        self.sim_config_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #EF4444;
                border-radius: 6px;
                margin-top: 6px;
                font-weight: bold;
                color: #F87171;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
        """)
        sim_layout = QVBoxLayout(self.sim_config_group)
        sim_layout.setContentsMargins(8, 6, 8, 6)
        sim_layout.setSpacing(6)

        lbl_sim_alert = QLabel("⚠️ MODO SIMULACIÓN: Exclusivo para test de obturador, búfer SD y ráfagas.")
        lbl_sim_alert.setStyleSheet("color: #EF4444; font-weight: bold; font-size: 11px;")
        sim_layout.addWidget(lbl_sim_alert)

        sim_row = QHBoxLayout()
        sim_row.addWidget(QLabel("Modo de ensayo:"))
        self.combo_test_mode = QComboBox()
        self.combo_test_mode.addItems([
            "Simulacro Rápido (12 seg de prueba)",
            "ECLIPSE_TEST (Estrés 2.5 min)",
            "Simulacro BKT Hardware (7 tomas AE Bracketing 1.7 EV)",
            "Simulacro Real (C2 - 5m a C3 + 5m)",
            "Eclipse Solar 2027 (Totalidad Cádiz / Luxor)",
            "Eclipse Lunar (Horquillado HDR)"
        ])
        self.combo_test_mode.setStyleSheet("""
            QComboBox {
                background-color: #16191F;
                border: 1px solid #EF4444;
                border-radius: 4px;
                color: #ECEFF4;
                padding: 4px 8px;
                font-size: 11px;
            }
        """)
        sim_row.addWidget(self.combo_test_mode, stretch=1)
        sim_layout.addLayout(sim_row)

        layout.addWidget(self.sim_config_group)
        self.sim_config_group.setVisible(False)

        # Botonera de Carga: Activo (1-Clic) y Simulación (en 5 min)
        load_btns_layout = QHBoxLayout()
        load_btns_layout.setSpacing(8)

        self.btn_load_active = QPushButton("⚡ Cargar como Eclipse Activo")
        self.btn_load_active.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.btn_load_active.setCursor(Qt.PointingHandCursor)
        self.btn_load_active.setStyleSheet("""
            QPushButton {
                background-color: #7C3AED;
                color: white;
                padding: 10px 14px;
                border-radius: 6px;
                border: 1px solid #8B5CF6;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8B5CF6;
                border-color: #C084FC;
            }
            QPushButton:disabled {
                background-color: #374151;
                color: #6B7280;
                border-color: #4B5563;
            }
        """)
        self.btn_load_active.clicked.connect(self._on_load_as_active_clicked)
        load_btns_layout.addWidget(self.btn_load_active, stretch=3)

        self.btn_load_sim = QPushButton("🧪 Simulación (en 5 min)")
        self.btn_load_sim.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.btn_load_sim.setCursor(Qt.PointingHandCursor)
        self.btn_load_sim.setStyleSheet("""
            QPushButton {
                background-color: #EA580C;
                color: white;
                padding: 10px 12px;
                border-radius: 6px;
                border: 1px solid #F97316;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F97316;
                border-color: #FB923C;
            }
            QPushButton:disabled {
                background-color: #374151;
                color: #6B7280;
                border-color: #4B5563;
            }
        """)
        self.btn_load_sim.clicked.connect(self._on_load_as_simulation_clicked)
        load_btns_layout.addWidget(self.btn_load_sim, stretch=2)

        layout.addLayout(load_btns_layout)

        # Botón para Imprimir / Generar Plan Manual Formal
        self.btn_print_plan = QPushButton("📄 Generar Plan Manual Formal (Imprimir / PDF)")
        self.btn_print_plan.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.btn_print_plan.setCursor(Qt.PointingHandCursor)
        self.btn_print_plan.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #38BDF8;
                padding: 10px 16px;
                border-radius: 6px;
                border: 1px solid #38BDF8;
            }
            QPushButton:hover {
                background-color: #0F172A;
                border-color: #7DD3FC;
                color: #FFFFFF;
            }
            QPushButton:disabled {
                background-color: #1F2937;
                color: #4B5563;
                border-color: #374151;
            }
        """)
        self.btn_print_plan.clicked.connect(self._on_print_manual_plan)
        layout.addWidget(self.btn_print_plan)

        return panel

    def _create_metric_card(self, title: str, initial_value: str, color_hex: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #16191F;
                border: 1px solid #2D323B;
                border-radius: 6px;
                padding: 3px;
            }
        """)
        l = QVBoxLayout(card)
        l.setContentsMargins(6, 4, 6, 4)
        l.setSpacing(2)

        lbl_t = QLabel(title)
        lbl_t.setAlignment(Qt.AlignCenter)
        lbl_t.setStyleSheet("font-size: 9px; font-weight: bold; color: #9CA3AF;")
        l.addWidget(lbl_t)

        lbl_v = QLabel(initial_value)
        lbl_v.setObjectName("val")
        lbl_v.setAlignment(Qt.AlignCenter)
        lbl_v.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_v.setStyleSheet(f"color: {color_hex};")
        l.addWidget(lbl_v)

        return card

    def _update_card(self, card: QFrame, value_text: str, color_hex: Optional[str] = None):
        lbl = card.findChild(QLabel, "val")
        if lbl:
            lbl.setText(value_text)
            if color_hex:
                lbl.setStyleSheet(f"color: {color_hex};")

    # -------------------------------------------------------------------------
    # Gestión de Datos y Filtros
    # -------------------------------------------------------------------------
    def _load_eclipses_list(self):
        query = self.txt_search.text().strip()
        f_idx = self.combo_filter.currentIndex()

        if f_idx == 1:
            items = self.catalog.filter_spain_eclipses()
        elif f_idx == 2:
            items = self.catalog.filter_by_type("solar_total")
        elif f_idx == 3:
            items = self.catalog.filter_by_type("solar_annular")
        elif f_idx == 4:
            items = [e for e in self.catalog.get_all() if e.is_lunar]
        elif f_idx == 5:
            items = [e for e in self.catalog.get_all() if getattr(e, "is_simulation", False)]
        else:
            items = self.catalog.get_all()

        # Omitir eventos pasados respecto a la fecha actual o de referencia
        ref_date = self.reference_date or datetime.now().strftime("%Y-%m-%d")
        items = [e for e in items if e.date >= ref_date]

        if query:
            items = [
                e for e in items
                if query.lower() in e.name.lower()
                or query.lower() in e.id.lower()
                or query in e.date
                or any(query.lower() in r.lower() for r in e.regions)
            ]

        prev_id = self.selected_eclipse.id if self.selected_eclipse else None
        self.list_eclipses.clear()
        idx_to_select = 0
        for i, e in enumerate(items):
            widget = self._create_eclipse_card_widget(e)
            item = QListWidgetItem(self.list_eclipses)
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.UserRole, e)
            self.list_eclipses.addItem(item)
            self.list_eclipses.setItemWidget(item, widget)
            if prev_id and e.id == prev_id:
                idx_to_select = i

        total_future = len(self.catalog.filter_future(ref_date))
        self.lbl_count.setText(f"Mostrando {len(items)} de {total_future} eventos futuros.")

        if self.list_eclipses.count() > 0:
            self.list_eclipses.setCurrentRow(idx_to_select)
        else:
            self.selected_eclipse = None

    def _create_eclipse_card_widget(self, eclipse: EclipseInfo) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(6, 4, 6, 4)
        l.setSpacing(3)

        is_sim = getattr(eclipse, "is_simulation", False)
        if is_sim:
            w.setStyleSheet("background-color: #201313; border: 1px solid #EF4444; border-radius: 4px;")

        # Fila superior: Fecha + Badge tipo + Duración central
        top_row = QHBoxLayout()
        date_str = "SIMULADOR" if is_sim else eclipse.date
        lbl_date = QLabel(date_str)
        lbl_date.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl_date.setStyleSheet("color: #EF4444;" if is_sim else "color: #FFFFFF;")
        top_row.addWidget(lbl_date)

        lbl_badge = QLabel(f" {eclipse.type_label} ")
        lbl_badge.setFont(QFont("Segoe UI", 9, QFont.Bold))
        lbl_badge.setStyleSheet(f"""
            background-color: {eclipse.badge_color};
            color: #FFFFFF;
            border-radius: 3px;
            padding: 2px 6px;
        """)
        top_row.addWidget(lbl_badge)

        top_row.addStretch()

        dur_text = "Configurable" if is_sim else f"⏱️ {eclipse.formatted_max_duration}"
        lbl_dur = QLabel(dur_text)
        lbl_dur.setStyleSheet("color: #EF4444; font-weight: bold; font-size: 11px;" if is_sim else "color: #38BDF8; font-weight: bold; font-size: 11px;")
        top_row.addWidget(lbl_dur)
        l.addLayout(top_row)

        # Nombre del eclipse
        lbl_name = QLabel(eclipse.name)
        lbl_name.setFont(QFont("Segoe UI", 10, QFont.Bold))
        lbl_name.setStyleSheet("color: #FCA5A5;" if is_sim else "color: #E2E8F0;")
        lbl_name.setWordWrap(True)
        l.addWidget(lbl_name)

        # Países / Regiones clave
        regions_str = ", ".join(eclipse.regions[:4])
        if len(eclipse.regions) > 4:
            regions_str += "..."
        lbl_reg = QLabel(f"🌍 {regions_str}")
        lbl_reg.setStyleSheet("color: #9CA3AF; font-size: 10px;")
        lbl_reg.setWordWrap(True)
        l.addWidget(lbl_reg)

        return w

    def _select_default_eclipse(self):
        """Selecciona el primer eclipse futuro disponible si no hay selección activa."""
        if self.list_eclipses.count() > 0 and self.list_eclipses.currentRow() < 0:
            self.list_eclipses.setCurrentRow(0)

    def _on_search_changed(self, text: str):
        self._load_eclipses_list()

    def _on_filter_changed(self, idx: int):
        self._load_eclipses_list()

    def _on_eclipse_item_selected(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]):
        if not current:
            self.selected_eclipse = None
            self._update_map_eclipse()
            return
        self.selected_eclipse = current.data(Qt.UserRole)
        self._update_map_eclipse()
        self.recalculate()

    # -------------------------------------------------------------------------
    # Sincronización de Coordenadas y Recálculo
    # -------------------------------------------------------------------------
    def update_coordinates(self, lat: float, lon: float, alt_m: float = 0.0, update_map: bool = True):
        """Actualiza las coordenadas de cálculo desde el GPS o Mapa y recalcula."""
        self.current_lat = lat
        self.current_lon = lon
        self.current_alt = alt_m

        self.spin_lat.blockSignals(True)
        self.spin_lon.blockSignals(True)
        self.spin_alt.blockSignals(True)

        self.spin_lat.setValue(lat)
        self.spin_lon.setValue(lon)
        self.spin_alt.setValue(alt_m)

        self.spin_lat.blockSignals(False)
        self.spin_lon.blockSignals(False)
        self.spin_alt.blockSignals(False)

        if update_map:
            self._update_map_observer()

        self.recalculate()

    def _on_coords_edited(self):
        self.current_lat = self.spin_lat.value()
        self.current_lon = self.spin_lon.value()
        self.current_alt = self.spin_alt.value()
        self._update_map_observer()
        self.recalculate()

    def _sync_with_parent_coords(self):
        """Intenta sincronizar con MainWindow si existe."""
        parent = self.parent()
        while parent and not hasattr(parent, "gps_reader"):
            parent = parent.parent()

        if parent and hasattr(parent, "gps_reader"):
            d = parent.gps_reader.data
            if d.has_fix and d.latitude != 0:
                self.update_coordinates(d.latitude, d.longitude, d.altitude_m)
                return
            elif hasattr(parent, "download_target_lat"):
                self.update_coordinates(parent.download_target_lat, parent.download_target_lon, 0.0)
                return

        # Si no hay fix real, recalcular con las actuales
        self.recalculate()

    def recalculate(self):
        """Ejecuta el evaluador astronómico con el eclipse y ubicación activos."""
        if not self.selected_eclipse:
            return

        res = calculate_local_eclipse(
            self.selected_eclipse,
            self.current_lat,
            self.current_lon,
            self.current_alt
        )
        self.last_result = res

        is_sim = getattr(self.selected_eclipse, "is_simulation", False)
        if hasattr(self, "sim_config_group"):
            self.sim_config_group.setVisible(is_sim)

        if is_sim:
            # 1. Configuración de Simulación
            self.lbl_vis_badge.setText(" SOLO SIMULACIÓN ")
            self.lbl_vis_badge.setStyleSheet("""
                background-color: #DC2626;
                color: white;
                padding: 4px 12px;
                border-radius: 4px;
                font-weight: bold;
            """)
            self.lbl_vis_details.setText("⚠️ Perfil para pruebas de campo, obturador y hardware. Cargar como simulación para ejecutar en 5 min.")
            self._update_card(self.card_duration, "Ajustable", "#EF4444")
            self._update_card(self.card_sun_alt, "45.0° (Test)", "#F59E0B")
            self._update_card(self.card_obscuration, "100% (Simulado)", "#38BDF8")
            self._update_card(self.card_azimuth, "180° (S)", "#10B981")
            self.lbl_alt_note.setText("Modo Simulación: temporizadores de prueba desacoplados de coordenadas geográficas.")
            self.lbl_horizon_warning.setVisible(False)

            self.btn_load_active.setEnabled(False)
            self.btn_load_active.setToolTip("El banco de pruebas solo se ejecuta en modo simulación.")
            self.btn_load_sim.setEnabled(True)
            self.btn_load_sim.setToolTip("Carga la simulación seleccionada para ejecutarse dentro de 5 minutos.")
        else:
            # 1. Actualizar Badge y Estado
            self.lbl_vis_badge.setText(f" {res.visibility_label.upper()} ")
            self.lbl_vis_badge.setStyleSheet(f"""
                background-color: {res.badge_color};
                color: white;
                padding: 4px 12px;
                border-radius: 4px;
                font-weight: bold;
            """)
            self.lbl_vis_details.setText(res.description)

            # 2. Actualizar Tarjetas
            if res.visibility in ("totality", "annularity"):
                dur_str = res.formatted_totality
                dur_color = "#A855F7" if res.visibility == "totality" else "#F59E0B"
            else:
                dur_str = "0s (Fuera)"
                dur_color = "#6B7280"
            self._update_card(self.card_duration, dur_str, dur_color)

            alt_str = f"{res.sun_altitude_deg:.1f}°"
            self._update_card(self.card_sun_alt, alt_str, "#F59E0B")

            obsc_str = f"{res.obscuration_pct:.1f}%"
            self._update_card(self.card_obscuration, obsc_str, "#38BDF8")

            card_dir = self._cardinal_from_azimuth(res.sun_azimuth_deg)
            az_str = f"{res.sun_azimuth_deg:.0f}° {card_dir}"
            self._update_card(self.card_azimuth, az_str, "#10B981")

            # 3. Alerta de Sol Bajo en el Horizonte (< 15°)
            if res.is_visible and res.sun_altitude_deg < 15.0:
                self.lbl_horizon_warning.setText(
                    f"⚠️ ATENCIÓN HORIZONTE: Sol muy bajo ({res.sun_altitude_deg:.1f}°). "
                    f"Comprueba montañas, árboles o edificios hacia el {card_dir}."
                )
                self.lbl_horizon_warning.setVisible(True)
            else:
                self.lbl_horizon_warning.setVisible(False)

            # 5. Corrección topográfica
            if res.visibility in ("totality", "annularity") and self.current_alt > 0:
                self.lbl_alt_note.setText(
                    f"🏔️ Corrección topográfica: {abs(res.alt_correction_s):.2f}s de adelanto en C2 "
                    f"(a {self.current_alt:.0f} m de altitud sobre el nivel del mar)."
                )
            else:
                self.lbl_alt_note.setText("🏔️ Corrección topográfica: nivel de referencia del mar (0.0s).")

            # 6. Habilitar o deshabilitar botón de carga y plan manual
            self.btn_load_active.setEnabled(res.is_visible)
            self.btn_load_active.setToolTip("Carga el eclipse astronómico en su fecha y hora UTC real")
            self.btn_load_sim.setEnabled(res.is_visible)
            self.btn_load_sim.setToolTip("Simula este eclipse en los próximos 5 minutos manteniendo su duración calculada")

        # 4. Tabla de Contactos
        self._populate_contacts_table(res)

        if hasattr(self, "btn_print_plan"):
            self.btn_print_plan.setEnabled(res.is_visible and not is_sim)

        # 7. Actualizar tooltip / descripción del observador en el mapa
        self._update_map_observer()

    # -------------------------------------------------------------------------
    # Integración con el Visor de Mapas Leaflet
    # -------------------------------------------------------------------------
    def _on_map_load_finished(self, ok: bool):
        """Notificación de carga completa del DOM de Leaflet."""
        self._map_ready = True
        self._update_map_observer()
        if self._pending_eclipse_update or self.selected_eclipse:
            self._update_map_eclipse()
            self._pending_eclipse_update = False

    def _on_map_title_changed(self, title: str):
        """Receptor de clics y eventos emitidos por el mapa Leaflet mediante document.title."""
        if title.startswith("OBSERVER:"):
            raw = title[len("OBSERVER:"):].strip()
            parts = raw.split(",")
            if len(parts) == 2:
                try:
                    lat = float(parts[0])
                    lon = float(parts[1])
                    # Sincronizar coordenadas sin re-disparar movimiento en el mapa
                    self.update_coordinates(lat, lon, self.current_alt, update_map=False)
                except ValueError:
                    pass

    def _recenter_map_on_observer(self):
        """Centra la vista del mapa en las coordenadas activas del observador."""
        if hasattr(self, "web_map_view") and self._map_ready:
            js = f"map.panTo([{self.current_lat}, {self.current_lon}]);"
            self.web_map_view.page().runJavaScript(js)

    def _update_map_eclipse(self):
        """Envía la geometría de trayectoria y franja del eclipse activo al visor Leaflet."""
        if not hasattr(self, "web_map_view") or not self._map_ready:
            self._pending_eclipse_update = True
            return

        if not self.selected_eclipse:
            self.web_map_view.page().runJavaScript("setEclipsePath(null);")
            return

        e_dict = {
            "id": self.selected_eclipse.id,
            "name": self.selected_eclipse.name,
            "type": self.selected_eclipse.type,
            "badge_color": self.selected_eclipse.badge_color,
            "path_width_km": self.selected_eclipse.path_width_km,
            "centerline": self.selected_eclipse.centerline,
            "path_polygon": self.selected_eclipse.path_polygon,
            "northern_limit": self.selected_eclipse.northern_limit,
            "southern_limit": self.selected_eclipse.southern_limit,
        }
        json_data = json.dumps(e_dict)
        js = f"setEclipsePath({json_data});"
        self.web_map_view.page().runJavaScript(js)

    def _update_map_observer(self):
        """Actualiza el marcador del observador en Leaflet con la telemetría local calculada."""
        if not hasattr(self, "web_map_view") or not self._map_ready:
            return

        desc = ""
        if self.last_result and self.selected_eclipse:
            if self.last_result.visibility in ("totality", "annularity"):
                desc = f"{self.last_result.visibility_label}: {self.last_result.formatted_totality}"
            elif self.last_result.is_visible:
                desc = f"Parcial: {self.last_result.obscuration_pct:.1f}%"
            else:
                desc = "Fuera de zona visible"

        safe_desc = desc.replace("'", "\\'")
        js = f"setObserverPosition({self.current_lat}, {self.current_lon}, '{safe_desc}');"
        self.web_map_view.page().runJavaScript(js)

    def _cardinal_from_azimuth(self, az: float) -> str:
        dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        idx = int((az + 11.25) / 22.5) % 16
        return dirs[idx]

    def _populate_contacts_table(self, res: LocalEclipseResult):
        is_annular = getattr(self.selected_eclipse, "is_annular", False) or (res.visibility == "annularity")
        c2_title = "Segundo contacto (Inicio de anularidad)" if is_annular else "Segundo contacto (Inicio de totalidad / Anular)"
        c2_desc = "Formación del anillo de fuego y perlas de Baily" if is_annular else "Perlas de Baily y Anillo"
        c3_title = "Tercer contacto (Fin de anularidad)" if is_annular else "Tercer contacto (Fin de totalidad)"
        c3_desc = "Ruptura del anillo de fuego y perlas de Baily" if is_annular else "Anillo de diamante de salida"

        rows = [
            ("C1", res.c1_iso, "Primer contacto parcial (Inicio del eclipse)", "Entrada de la penumbra"),
            ("C2", res.c2_iso, c2_title, c2_desc),
            ("MAX", res.max_iso, "Máximo del eclipse", f"Sol a {res.sun_altitude_deg:.1f}° azimut {res.sun_azimuth_deg:.0f}°"),
            ("C3", res.c3_iso, c3_title, c3_desc),
            ("C4", res.c4_iso, "Cuarto contacto (Fin del eclipse)", "Salida total de la Luna")
        ]
        self.table_contacts.setRowCount(len(rows))
        for row, (c_id, c_time, c_phase, c_desc) in enumerate(rows):
            it_id = QTableWidgetItem(c_id)
            it_id.setForeground(QColor("#38BDF8"))
            it_id.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table_contacts.setItem(row, 0, it_id)

            it_time = QTableWidgetItem(c_time)
            it_time.setFont(QFont("Consolas", 10, QFont.Bold))
            self.table_contacts.setItem(row, 1, it_time)

            it_phase = QTableWidgetItem(c_phase)
            self.table_contacts.setItem(row, 2, it_phase)

            it_desc = QTableWidgetItem(c_desc)
            it_desc.setForeground(QColor("#9CA3AF"))
            self.table_contacts.setItem(row, 3, it_desc)

    def _on_load_as_active_clicked(self):
        """Emite la señal para inyectar los contactos astronómicos reales en MainWindow."""
        if not self.selected_eclipse or not self.last_result:
            return

        contacts = self.last_result.to_contacts_dict()
        self.eclipse_selected_as_active.emit(
            contacts,
            self.selected_eclipse,
            self.last_result,
            False,
            ""
        )

    def _on_load_as_simulation_clicked(self):
        """Emite la señal para inyectar los contactos simulados en los próximos 5 minutos."""
        if not self.selected_eclipse or not self.last_result:
            return

        now = datetime.now(timezone.utc).timestamp()
        c2 = now + 300.0  # T+5 min

        is_sim = getattr(self.selected_eclipse, "is_simulation", False)
        if is_sim:
            preset_name = self.combo_test_mode.currentText()
            if "12 seg" in preset_name or "Rápido" in preset_name:
                totality = 12.0
                contacts = {
                    "C1": c2 - 30.0,
                    "C2": c2,
                    "MAX": c2 + 6.0,
                    "C3": c2 + totality,
                    "C4": c2 + totality + 30.0,
                    "U2": c2,
                    "U3": c2 + totality,
                }
            elif "Estrés" in preset_name or "ECLIPSE_TEST" in preset_name or "BKT" in preset_name:
                totality = 60.0
                contacts = {
                    "C1": c2 - 60.0,
                    "C2": c2,
                    "MAX": c2 + 30.0,
                    "C3": c2 + totality,
                    "C4": c2 + totality + 30.0,
                    "U2": c2,
                    "U3": c2 + totality,
                }
            else:
                totality = 120.0
                contacts = {
                    "C1": c2 - 120.0,
                    "C2": c2,
                    "MAX": c2 + 60.0,
                    "C3": c2 + totality,
                    "C4": c2 + totality + 60.0,
                    "U2": c2,
                    "U3": c2 + totality,
                }
        else:
            preset_name = ""
            totality = self.last_result.totality_duration_s if self.last_result.totality_duration_s > 0 else 120.0
            contacts = {
                "C1": c2 - 120.0,
                "C2": c2,
                "MAX": c2 + (totality / 2.0),
                "C3": c2 + totality,
                "C4": c2 + totality + 60.0,
                "U2": c2,
                "U3": c2 + totality,
            }

        self.eclipse_selected_as_active.emit(
            contacts,
            self.selected_eclipse,
            self.last_result,
            True,
            preset_name
        )

    def _on_print_manual_plan(self):
        """Genera y abre en el navegador el Plan Manual Formal de Emergencia."""
        if not self.selected_eclipse or not self.last_result:
            return

        import os
        import webbrowser
        from core.backup_plan import generate_backup_plan_html

        res = self.last_result
        contacts = res.to_contacts_dict()

        # Determinar cámara y óptica del equipo si está disponible
        cam_name = "Nikon Z5 II"
        lens_info = "500mm f/8"
        parent_mw = self.window()
        if hasattr(parent_mw, "equipment_manager") and parent_mw.equipment_manager:
            slot_a = parent_mw.equipment_manager.slot_a
            if slot_a:
                if slot_a.driver and getattr(slot_a.driver, "camera_name", None):
                    cam_name = slot_a.driver.camera_name
                elif slot_a.assigned_device and getattr(slot_a.assigned_device, "model_name", None):
                    cam_name = slot_a.assigned_device.model_name
                if getattr(slot_a, "optical_setup", None):
                    lens_info = slot_a.optical_setup

        filename = f"plan_manual_{self.selected_eclipse.id}.html"
        out_dir = os.path.join(os.getcwd(), "plans")
        out_path = os.path.join(out_dir, filename)

        generate_backup_plan_html(
            eclipse_name=self.selected_eclipse.name,
            location_name=f"Lat {self.current_lat:.4f}°, Lon {self.current_lon:.4f}° ({self.current_alt:.0f}m)",
            lat=self.current_lat,
            lon=self.current_lon,
            alt_m=self.current_alt,
            visibility=res.visibility,
            totality_duration_s=res.totality_duration_s,
            sun_altitude_deg=res.sun_altitude_deg,
            sun_azimuth_deg=res.sun_azimuth_deg,
            contacts=contacts,
            camera_name=cam_name,
            lens_info=lens_info,
            output_path=out_path
        )

        webbrowser.open(os.path.abspath(out_path))
        if hasattr(parent_mw, "_log"):
            parent_mw._log(f"📄 [PLAN MANUAL] Hoja de ruta generada y abierta en navegador: {out_path}")
