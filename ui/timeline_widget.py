"""
Widget de Timeline Gráfico Vectorial para eclipZe v2.0.
Implementa renderizado con QPainter de alta resolución con doble búfer:
- Bloques coloreados de fases físicas del eclipse (DR, BB, CH, PR).
- Dos pistas paralelas de disparo: Cámara A (Master) y Cámara B (Slave).
- Marcadores de estado (Gris: programado, Verde: ejecutado, Amarillo: skip, Rojo: error).
- Línea de Playhead animada a 30 FPS sincronizada con time.perf_counter().
- Selector de escala temporal: "Vista Completa" vs "Zoom Totalidad".
"""

import time
from typing import Dict, List, Optional, Any
from PySide6.QtWidgets import QWidget, QPushButton, QToolTip
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygonF

from core.presets import EclipseEvent


# Paleta de colores astronómicos oficiales (eclipseClick / eclipZe v2.0)
PHASE_COLORS = {
    "DR": QColor("#3B8288"),       # Diamond Ring (Anillo de Diamante) - Cian / Teal oscuro
    "BB": QColor("#C99A3E"),       # Baily's Beads (Perlas de Baily) - Amarillo Oro / Ocre
    "CH": QColor("#B85338"),       # Chromosphere (Cromosfera) - Teja / Naranja rojizo
    "PR": QColor("#8E527D"),       # Prominences & Totality (Corona y Totalidad) - Púrpura tenue
    "PARCIAL": QColor("#1E242C"),  # Fase Parcial previa/posterior - Gris carbón
}

STATUS_COLORS = {
    "scheduled": QColor("#6B7280"),  # Programado (Gris)
    "executed": QColor("#10B981"),   # Ejecutado OK (Verde)
    "skipped": QColor("#F59E0B"),    # Omitido drop-and-skip (Amarillo)
    "error": QColor("#EF4444"),      # Error / timeout (Rojo)
}


class EclipseTimelineWidget(QWidget):
    """
    Visualizador vectorial del timeline del eclipse y ráfagas multi-cámara.
    """
    zoom_changed = Signal(str)  # "full" o "totality"

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumHeight(165)
        self.setMouseTracking(True)

        self.margin_left = 135.0
        self.margin_right = 20.0
        self.header_height = 36.0

        # Estado del timeline
        self.contacts: Dict[str, float] = {}
        self.is_annular: bool = False
        self.events_a: List[Dict[str, Any]] = []
        self.events_b: List[Dict[str, Any]] = []
        self.show_track_b: bool = True
        self._raw_events: List[EclipseEvent] = []
        self.zoom_mode: str = "totality"  # "full" o "totality"

        self.t_start: float = 0.0
        self.t_end: float = 1.0

        # Playhead e interpolación suave (30 FPS)
        self.current_playhead_time: float = 0.0
        self._perf_base: float = time.perf_counter()
        self._wall_base: float = time.time()
        self._is_animating: bool = False

        self._timer = QTimer(self)
        self._timer.setInterval(33)  # ~30 FPS
        self._timer.timeout.connect(self._on_playhead_tick)

        # Botón selector de escala temporal
        self.btn_zoom = QPushButton("🌐 Vista Completa", self)
        self.btn_zoom.setCursor(Qt.PointingHandCursor)
        self.btn_zoom.setStyleSheet("""
            QPushButton {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 4px;
                color: #9CA3AF;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #374151;
                color: #FFFFFF;
                border-color: #38BDF8;
            }
        """)
        self.btn_zoom.clicked.connect(self.toggle_zoom)

        # Inicialización de tiempos base
        self.set_contacts({})

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Posicionar el botón de alternancia de zoom en la esquina superior derecha
        btn_w, btn_h = 130, 26
        self.btn_zoom.setGeometry(self.width() - btn_w - int(self.margin_right), 5, btn_w, btn_h)

    def set_zoom_mode(self, mode: str):
        """Establece el modo de zoom: 'full' (C1 a C4) o 'totality' (C2-60s a C3+60s)."""
        if mode not in ("full", "totality"):
            mode = "totality"
        self.zoom_mode = mode
        if self.zoom_mode == "full":
            self.btn_zoom.setText("🔍 Zoom Totalidad")
        else:
            self.btn_zoom.setText("🌐 Vista Completa")
        self._recalculate_time_bounds()
        self.zoom_changed.emit(self.zoom_mode)
        self.update()

    def toggle_zoom(self):
        """Alterna entre Vista Completa y Zoom de Totalidad."""
        next_mode = "full" if self.zoom_mode == "totality" else "totality"
        self.set_zoom_mode(next_mode)

    def set_contacts(self, contacts: Dict[str, float], is_annular: bool = False):
        """Actualiza los instantes de contacto (C1, C2, MAX, C3, C4)."""
        self.contacts = dict(contacts)
        self.is_annular = is_annular
        self._recalculate_time_bounds()
        if self.current_playhead_time == 0.0:
            self.current_playhead_time = self.t_start
        self.update()

    def _recalculate_time_bounds(self):
        """Calcula t_start y t_end según el modo de escala activo."""
        c2 = self.contacts.get("C2")
        c3 = self.contacts.get("C3")

        now = time.time()
        ref_c2 = c2 if c2 is not None else now
        ref_c3 = c3 if c3 is not None else (ref_c2 + 120.0)

        if self.zoom_mode == "totality":
            self.t_start = ref_c2 - 60.0
            self.t_end = ref_c3 + 60.0
        else:
            # Vista Completa: C1 a C4 o rango extendido de eventos
            c1 = self.contacts.get("C1", ref_c2 - 3600.0)
            c4 = self.contacts.get("C4", ref_c3 + 3600.0)

            all_times = [ev["time"] for ev in self.events_a + self.events_b]
            if all_times:
                min_ev = min(all_times)
                max_ev = max(all_times)
                self.t_start = min(c1, min_ev - 30.0)
                self.t_end = max(c4, max_ev + 30.0)
            else:
                self.t_start = c1
                self.t_end = c4

        if self.t_end <= self.t_start:
            self.t_end = self.t_start + 1.0

    def set_track_b_enabled(self, enabled: bool):
        """Habilita o deshabilita la visualización y marcadores de la pista B."""
        self.show_track_b = enabled
        if hasattr(self, "_raw_events") and self._raw_events:
            self.set_events(self._raw_events, self.contacts)
        else:
            self.update()

    def set_events(self, events: List[EclipseEvent], contacts: Optional[Dict[str, float]] = None):
        """
        Carga la lista de disparos programados y los separa en pista A y pista B.
        """
        self._raw_events = list(events)
        if contacts is not None:
            self.contacts = dict(contacts)

        self.events_a.clear()
        self.events_b.clear()

        for idx, ev in enumerate(events, start=1):
            ref_name = ev.contact_ref
            t_ref = self.contacts.get(ref_name)
            if t_ref is None:
                # Estimación si falta el contacto específico
                t_ref = self.contacts.get("C2", time.time())
            target_t = t_ref + ev.offset_seconds

            slot = getattr(ev, "camera_slot", "A").upper().strip()
            ev_id = getattr(ev, "event_id", "") or f"L{idx:02d}"
            phase = getattr(ev, "phase", "") or "PR"

            status = "scheduled"
            if ev.executed:
                status = "executed"
            elif ev.skipped:
                status = "skipped"

            record = {
                "id": ev_id,
                "time": target_t,
                "slot": slot,
                "phase": phase,
                "description": ev.description,
                "shutter": ev.shutter_speed,
                "iso": ev.iso,
                "status": status,
                "event_ref": ev,
            }

            if slot == "B":
                if self.show_track_b:
                    self.events_b.append(record)
            else:
                self.events_a.append(record)

        self._recalculate_time_bounds()
        self.update()

    def update_event_status(self, event_identifier: str, status: str):
        """Actualiza el estado de un evento ('executed', 'skipped', 'error', 'scheduled')."""
        clean_id = event_identifier.strip().upper()
        found = False
        for ev in self.events_a + self.events_b:
            if ev["id"].upper() == clean_id or ev["description"] == event_identifier:
                ev["status"] = status
                found = True
        if found:
            self.update()

    def time_to_x(self, t: float) -> float:
        """Convierte un timestamp astronómico a coordenada horizontal de pantalla."""
        usable_w = max(10.0, self.width() - self.margin_left - self.margin_right)
        span = self.t_end - self.t_start
        if span <= 0:
            return self.margin_left
        ratio = (t - self.t_start) / span
        return self.margin_left + ratio * usable_w

    def x_to_time(self, x: float) -> float:
        """Convierte una coordenada X a timestamp astronómico."""
        usable_w = max(10.0, self.width() - self.margin_left - self.margin_right)
        ratio = (x - self.margin_left) / usable_w
        return self.t_start + ratio * (self.t_end - self.t_start)

    def set_playhead_time(self, t: float):
        """Ajusta manualmente el playhead y sincroniza el tiempo de referencia."""
        self.current_playhead_time = t
        self._wall_base = t
        self._perf_base = time.perf_counter()
        self.update()

    def start_animation(self, base_wall_time: Optional[float] = None):
        """Inicia el barrido del Playhead a 30 FPS."""
        self._wall_base = base_wall_time if base_wall_time is not None else time.time()
        self._perf_base = time.perf_counter()
        self.current_playhead_time = self._wall_base
        self._is_animating = True
        self._timer.start()
        self.update()

    def stop_animation(self):
        """Detiene la animación del Playhead."""
        self._is_animating = False
        self._timer.stop()
        self.update()

    def _on_playhead_tick(self):
        """Callback del timer a 30 FPS para interpolación continua y fluida."""
        if not self._is_animating:
            return
        elapsed = time.perf_counter() - self._perf_base
        self.current_playhead_time = self._wall_base + elapsed
        self.update()

    def paintEvent(self, event):
        """Renderizado vectorial de alta precisión mediante QPainter."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        w = float(self.width())
        h = float(self.height())
        usable_w = max(10.0, w - self.margin_left - self.margin_right)

        # 1. Fondo general del widget
        painter.fillRect(QRectF(0, 0, w, h), QColor("#0D1117"))

        # 2. Encabezado y Leyenda
        self._draw_header(painter)

        # 3. Barra de fases físicas (DR, BB, CH, PR)
        phase_y = 38.0
        phase_h = 24.0
        self._draw_phase_bar(painter, phase_y, phase_h, usable_w)

        # 4. Pistas de disparo paralelas
        track_a_y = 68.0
        track_b_y = 96.0
        track_h = 24.0
        self._draw_track(painter, "CAM A (Master)", "#3B82F6", track_a_y, track_h, usable_w, self.events_a)
        if self.show_track_b:
            self._draw_track(painter, "CAM B (Slave)", "#F97316", track_b_y, track_h, usable_w, self.events_b)
        else:
            self._draw_track(painter, "CAM B (Desactivada)", "#6B7280", track_b_y, track_h, usable_w, [])

        # 5. Eje de tiempo y marcas de contacto (C1, C2, MAX, C3, C4)
        axis_y = 124.0
        self._draw_time_axis(painter, axis_y, usable_w)

        # 6. Cursor vertical de Playhead (Rojo Neón #EF4444)
        self._draw_playhead(painter, phase_y, track_b_y + track_h + 4.0)

        painter.end()

    def _draw_header(self, painter: QPainter):
        """Dibuja título del timeline y leyenda de colores de fases."""
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.setPen(QColor("#E5E7EB"))
        painter.drawText(QRectF(10, 8, 200, 22), Qt.AlignLeft | Qt.AlignVCenter, "Eclipse Timeline")

        # Leyenda compacta en cabecera
        legend_items = [
            ("DR", PHASE_COLORS["DR"]),
            ("BB", PHASE_COLORS["BB"]),
            ("CH", PHASE_COLORS["CH"]),
            ("PR", PHASE_COLORS["PR"]),
        ]
        start_x = 160.0
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        for label, color in legend_items:
            # Cuadro de color
            painter.fillRect(QRectF(start_x, 12, 10, 10), color)
            painter.setPen(QColor("#D1D5DB"))
            painter.drawText(QRectF(start_x + 14, 8, 30, 18), Qt.AlignLeft | Qt.AlignVCenter, label)
            start_x += 48.0

    def _draw_phase_bar(self, painter: QPainter, y: float, h: float, usable_w: float):
        """Dibuja los bloques coloreados según las fases físicas del eclipse."""
        content_left = self.margin_left
        content_right = content_left + usable_w

        # Fondo base de la barra (Parcial)
        base_rect = QRectF(content_left, y, usable_w, h)
        painter.fillRect(base_rect, PHASE_COLORS["PARCIAL"])
        painter.setPen(QPen(QColor("#30363D"), 1))
        painter.drawRect(base_rect)

        c2 = self.contacts.get("C2")
        c3 = self.contacts.get("C3")

        if c2 is not None and c3 is not None:
            if getattr(self, "is_annular", False):
                # Intervalos físicos para Eclipse Anular (Anillo de Fuego y Perlas de Baily)
                phase_intervals = [
                    (c2 - 4.0, c2, "BB", PHASE_COLORS["BB"]),
                    (c2, c3, "ANULARIDAD", QColor("#F59E0B")),
                    (c3, c3 + 4.0, "BB", PHASE_COLORS["BB"]),
                ]
            else:
                # Intervalos físicos relativos a C2 y C3
                phase_intervals = [
                    # Pre-C2
                    (c2 - 4.0, c2, "DR", PHASE_COLORS["DR"]),
                    (c2, c2 + 3.0, "BB", PHASE_COLORS["BB"]),
                    (c2 + 3.0, c2 + 8.0, "CH", PHASE_COLORS["CH"]),
                    # Totalidad central
                    (c2 + 8.0, c3 - 8.0, "TOTALITY (PR)", PHASE_COLORS["PR"]),
                    # Post-C3
                    (c3 - 8.0, c3 - 3.0, "CH", PHASE_COLORS["CH"]),
                    (c3 - 3.0, c3, "BB", PHASE_COLORS["BB"]),
                    (c3, c3 + 4.0, "DR", PHASE_COLORS["DR"]),
                ]

            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))

            for t_start_phase, t_end_phase, label, color in phase_intervals:
                # Comprobar si se encuentra dentro del rango de visualización visible
                t_draw_start = max(self.t_start, t_start_phase)
                t_draw_end = min(self.t_end, t_end_phase)

                if t_draw_start < t_draw_end:
                    x1 = self.time_to_x(t_draw_start)
                    x2 = self.time_to_x(t_draw_end)
                    rect = QRectF(x1, y, max(1.0, x2 - x1), h)
                    painter.fillRect(rect, color)
                    painter.setPen(QPen(QColor("#111827"), 0.5))
                    painter.drawRect(rect)

                    # Dibujar etiqueta de texto si hay suficiente anchura
                    if (x2 - x1) >= 22.0:
                        painter.setPen(QColor("#FFFFFF"))
                        display_text = label if (x2 - x1) >= 45.0 else label[:2]
                        painter.drawText(rect, Qt.AlignCenter, display_text)

    def _draw_track(
        self,
        painter: QPainter,
        label: str,
        color_hex: str,
        y: float,
        h: float,
        usable_w: float,
        events: List[Dict[str, Any]]
    ):
        """Dibuja una pista paralela de disparo con sus marcadores de evento."""
        # 1. Badge de la pista a la izquierda
        badge_rect = QRectF(6.0, y, self.margin_left - 12.0, h)
        painter.fillRect(badge_rect, QColor("#161B22"))
        painter.setPen(QPen(QColor(color_hex), 1))
        painter.drawRoundedRect(badge_rect, 3, 3)

        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        painter.setPen(QColor(color_hex))
        painter.drawText(badge_rect, Qt.AlignCenter, label)

        # 2. Fondo de la pista
        track_rect = QRectF(self.margin_left, y, usable_w, h)
        painter.fillRect(track_rect, QColor("#161B22"))
        painter.setPen(QPen(QColor("#21262D"), 1))
        painter.drawRect(track_rect)

        # Línea guía horizontal interna
        center_y = y + h / 2.0
        painter.setPen(QPen(QColor("#30363D"), 1, Qt.DashLine))
        painter.drawLine(QPointF(self.margin_left, center_y), QPointF(self.margin_left + usable_w, center_y))

        # 3. Marcadores de disparo
        for ev in events:
            x = self.time_to_x(ev["time"])
            if self.margin_left <= x <= (self.margin_left + usable_w):
                st_color = STATUS_COLORS.get(ev["status"], STATUS_COLORS["scheduled"])
                painter.setPen(QPen(QColor("#0D1117"), 1.5))
                painter.setBrush(QBrush(st_color))

                # Marcador tipo rombo vectorial de 9x9 px
                diamond = QPolygonF([
                    QPointF(x, center_y - 5.0),
                    QPointF(x + 4.5, center_y),
                    QPointF(x, center_y + 5.0),
                    QPointF(x - 4.5, center_y)
                ])
                painter.drawPolygon(diamond)

    def _draw_time_axis(self, painter: QPainter, y: float, usable_w: float):
        """Dibuja la línea de contactos astronómicos (C1, C2, MAX, C3, C4) y marcas de tiempo."""
        painter.setPen(QPen(QColor("#4B5563"), 1))
        painter.drawLine(
            QPointF(self.margin_left, y),
            QPointF(self.margin_left + usable_w, y)
        )

        painter.setFont(QFont("Consolas", 8, QFont.Bold))

        # Dibujar líneas guía y etiquetas de contactos clave
        contact_tags = [
            ("C1", "#9CA3AF"),
            ("C2", "#38BDF8"),
            ("MAX", "#A855F7"),
            ("C3", "#38BDF8"),
            ("C4", "#9CA3AF")
        ]

        for tag, color_hex in contact_tags:
            t = self.contacts.get(tag)
            if t is not None:
                x = self.time_to_x(t)
                if self.margin_left <= x <= (self.margin_left + usable_w):
                    painter.setPen(QPen(QColor(color_hex), 1, Qt.DotLine))
                    # Línea vertical punteada hasta la barra superior
                    painter.drawLine(QPointF(x, 38.0), QPointF(x, y + 6.0))

                    # Etiqueta de contacto
                    painter.setPen(QColor(color_hex))
                    tag_rect = QRectF(x - 18.0, y + 8.0, 36.0, 16.0)
                    painter.drawText(tag_rect, Qt.AlignCenter, tag)

    def _draw_playhead(self, painter: QPainter, top_y: float, bottom_y: float):
        """Dibuja la línea de Playhead roja neón animada con interpolación suave."""
        x = self.time_to_x(self.current_playhead_time)
        usable_w = max(10.0, self.width() - self.margin_left - self.margin_right)

        if self.margin_left <= x <= (self.margin_left + usable_w):
            # Resplandor neón exterior semi-transparente
            glow_pen = QPen(QColor(239, 68, 68, 70), 5)
            painter.setPen(glow_pen)
            painter.drawLine(QPointF(x, top_y - 3), QPointF(x, bottom_y + 3))

            # Línea central nítida (Rojo neón #EF4444)
            main_pen = QPen(QColor("#EF4444"), 2)
            painter.setPen(main_pen)
            painter.drawLine(QPointF(x, top_y - 2), QPointF(x, bottom_y + 2))

            # Flechas indicadoras en extremos
            painter.setBrush(QBrush(QColor("#EF4444")))
            top_triangle = QPolygonF([
                QPointF(x, top_y + 3.0),
                QPointF(x - 4.5, top_y - 4.0),
                QPointF(x + 4.5, top_y - 4.0)
            ])
            painter.drawPolygon(top_triangle)

            bottom_triangle = QPolygonF([
                QPointF(x, bottom_y - 3.0),
                QPointF(x - 4.5, bottom_y + 4.0),
                QPointF(x + 4.5, bottom_y + 4.0)
            ])
            painter.drawPolygon(bottom_triangle)

    def mouseMoveEvent(self, event):
        """Muestra ToolTip interactivo al pasar el cursor sobre marcadores de disparo."""
        pos = event.position()
        mx, my = pos.x(), pos.y()

        hovered_ev = None
        for ev in self.events_a + self.events_b:
            x = self.time_to_x(ev["time"])
            y = 80.0 if ev["slot"] == "A" else 108.0
            if abs(mx - x) <= 6.0 and abs(my - y) <= 10.0:
                hovered_ev = ev
                break

        if hovered_ev:
            text = (
                f"[{hovered_ev['id']}] {hovered_ev['slot']} — {hovered_ev['description']}\n"
                f"Fase: {hovered_ev['phase']} | Exp: {hovered_ev['shutter']} ISO {hovered_ev['iso']}\n"
                f"Estado: {hovered_ev['status'].upper()}"
            )
            QToolTip.showText(event.globalPosition().toPoint(), text, self)
        else:
            QToolTip.hideText()
        super().mouseMoveEvent(event)
