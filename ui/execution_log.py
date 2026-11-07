"""
Módulo de Log de Ejecución y Telemetría de Jitter para eclipZe v2.0.
Implementa un modelo QAbstractTableModel ligero y de alto rendimiento para
monitorear disparos duales con precisión de milisegundos y cálculo de desfase (Jitter).
"""

import time
import datetime
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableView, QHeaderView, QPushButton
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal
from PySide6.QtGui import QColor, QFont, QBrush

from core.presets import EclipseEvent, is_notice_event


def format_timestamp_ms(t: float) -> str:
    """Formatea un epoch timestamp a HH:MM:SS.mmm con precisión de milisegundos."""
    if not t or t <= 0:
        return "--:--:--.---"
    dt = datetime.datetime.fromtimestamp(t)
    return dt.strftime("%H:%M:%S") + f".{int(dt.microsecond / 1000):03d}"


def calculate_jitter_ms(sched_t: float, actual_t: float) -> float:
    """Calcula la desviación temporal en milisegundos (+X ms / -X ms)."""
    return round((actual_t - sched_t) * 1000.0, 3)


def get_jitter_color(jitter_ms: Optional[float]) -> QColor:
    """
    Retorna el color de telemetría según el umbral de latencia:
      - < 15 ms: Verde (#10B981) - Excelente salud de bus
      - 15 - 50 ms: Amarillo (#F59E0B) - Advertencia de carga/espejo
      - > 50 ms: Rojo (#EF4444) - Desfase crítico
    """
    if jitter_ms is None:
        return QColor("#6B7280")
    abs_j = abs(jitter_ms)
    if abs_j < 15.0:
        return QColor("#10B981")
    elif abs_j <= 50.0:
        return QColor("#F59E0B")
    else:
        return QColor("#EF4444")


@dataclass
class ExecutionRecord:
    event_id: str
    camera_slot: str
    phase: str
    description: str
    shutter: str
    iso: str
    sched_timestamp: float
    real_timestamp: float = 0.0
    jitter_ms: Optional[float] = None
    status: str = "PENDING"  # PENDING, DONE, SKIPPED, FAIL
    event_ref: Optional[EclipseEvent] = None


def is_notice_record(rec: ExecutionRecord) -> bool:
    """Verifica si el registro corresponde a un aviso de voz o sistema (sin exposición real)."""
    if rec.event_ref is not None:
        if not getattr(rec.event_ref, "is_shot", True) or is_notice_event(rec.event_ref):
            return True
    desc = rec.description.lower()
    return (
        "aviso:" in desc or
        "alerta:" in desc or
        "parada preventiva" in desc or
        "vaciado búfer" in desc or
        "fin de " in desc or
        "reporte telemetría" in desc or
        ("filtro" in desc and ("quitar" in desc or "poner" in desc or "colocar" in desc))
    )


class ExecutionTableModel(QAbstractTableModel):
    """Modelo de datos optimizado para la tabla de ejecución y jitter."""

    COLUMNS = [
        "Estado",
        "ID",
        "Cámara",
        "Fase / Objetivo",
        "Exposición",
        "T. Programado",
        "T. Real",
        "Jitter",
        "Resultado"
    ]

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.contacts: Dict[str, float] = {}
        self.records: List[ExecutionRecord] = []

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.records)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.COLUMNS)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self.records):
            return None

        rec = self.records[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                if rec.status == "DONE":
                    return "✔"
                elif rec.status == "SKIPPED":
                    return "⏭"
                elif rec.status in ("FAIL", "ERROR"):
                    return "✖"
                else:
                    return "●"
            elif col == 1:
                return rec.event_id
            elif col == 2:
                slot_clean = rec.camera_slot.upper()
                return f"[CÁMARA {slot_clean}]"
            elif col == 3:
                phase_badge = f"[{rec.phase}] " if rec.phase else ""
                return f"{phase_badge}{rec.description}"
            elif col == 4:
                if rec.shutter == "--" or is_notice_record(rec):
                    return "--"
                return f"{rec.shutter}  ISO {rec.iso}"
            elif col == 5:
                return format_timestamp_ms(rec.sched_timestamp)
            elif col == 6:
                return format_timestamp_ms(rec.real_timestamp)
            elif col == 7:
                if rec.jitter_ms is not None:
                    return f"{rec.jitter_ms:+.0f} ms"
                return "--"
            elif col == 8:
                return rec.status

        elif role == Qt.ForegroundRole:
            if col in (0, 8):
                if rec.status == "DONE":
                    return QBrush(QColor("#10B981"))
                elif rec.status == "SKIPPED":
                    return QBrush(QColor("#F59E0B"))
                elif rec.status in ("FAIL", "ERROR"):
                    return QBrush(QColor("#EF4444"))
                return QBrush(QColor("#6B7280"))
            elif col == 1:
                return QBrush(QColor("#E5E7EB"))
            elif col == 2:
                # Azul para Cámara A, Naranja para Cámara B
                if rec.camera_slot.upper() == "B":
                    return QBrush(QColor("#F97316"))
                return QBrush(QColor("#3B82F6"))
            elif col == 3:
                d_low = rec.description.lower()
                if "filtro" in d_low and ("quitar" in d_low or "poner" in d_low or "colocar" in d_low):
                    return QBrush(QColor("#F59E0B"))  # Ámbar de alto contraste
                return QBrush(QColor("#F3F4F6"))
            elif col == 4:
                if rec.shutter == "--" or is_notice_record(rec):
                    return QBrush(QColor("#6B7280"))
                return QBrush(QColor("#9CA3AF"))
            elif col in (5, 6):
                return QBrush(QColor("#D1D5DB"))
            elif col == 7:
                return QBrush(get_jitter_color(rec.jitter_ms))

        elif role == Qt.TextAlignmentRole:
            if col in (0, 1, 2, 4, 5, 6, 7, 8):
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        elif role == Qt.FontRole:
            if col in (1, 4, 5, 6, 7):
                font = QFont("Consolas", 9)
                if col in (1, 7):
                    font.setBold(True)
                return font
            elif col in (0, 2, 8):
                font = QFont("Segoe UI", 9, QFont.Bold)
                return font

        return None

    def clear(self):
        self.beginResetModel()
        self.records.clear()
        self.endResetModel()

    def set_records(self, records: List[ExecutionRecord]):
        self.beginResetModel()
        self.records = records
        self.endResetModel()

    def update_row(self, row: int):
        if 0 <= row < len(self.records):
            top_left = self.index(row, 0)
            bottom_right = self.index(row, self.columnCount() - 1)
            self.dataChanged.emit(top_left, bottom_right)


class ExecutionLogWidget(QWidget):
    """
    Panel de visualización del Execution Log con telemetría de jitter y badges.
    """
    event_recorded = Signal(dict)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.contacts: Dict[str, float] = {}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)

        # Barra de estado y resumen superior
        top_bar = QHBoxLayout()
        self.lbl_stats = QLabel("0 eventos programados | 0 ejecutados | Jitter medio: --")
        self.lbl_stats.setStyleSheet("font-weight: 600; color: #9CA3AF; font-size: 11px;")
        top_bar.addWidget(self.lbl_stats)

        top_bar.addStretch()

        self.btn_clear = QPushButton("Limpiar Log")
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 4px;
                color: #9CA3AF;
                padding: 3px 8px;
                font-size: 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #374151;
                color: #FFFFFF;
            }
        """)
        self.btn_clear.clicked.connect(self.clear_log)
        top_bar.addWidget(self.btn_clear)

        main_layout.addLayout(top_bar)

        # Tabla de ejecución con QTableView
        self.model = ExecutionTableModel(self)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.setShowGrid(False)

        # Configuración de anchos de columnas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 42)    # Estado icon
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 52)    # ID (L01)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(2, 95)    # Cámara badge
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Descripción
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Exp
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(5, 105)   # T. Prog
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 105)   # T. Real
        header.setSectionResizeMode(7, QHeaderView.Fixed)
        self.table.setColumnWidth(7, 75)    # Jitter
        header.setSectionResizeMode(8, QHeaderView.Fixed)
        self.table.setColumnWidth(8, 70)    # Resultado

        self.table.setStyleSheet("""
            QTableView {
                background-color: #121418;
                alternate-background-color: #16191F;
                color: #E5E9F0;
                gridline-color: #21262D;
                border: 1px solid #2D323B;
                border-radius: 4px;
                selection-background-color: #1F2937;
            }
            QHeaderView::section {
                background-color: #1A1F26;
                color: #9CA3AF;
                padding: 4px 6px;
                border: none;
                border-bottom: 1px solid #2D323B;
                font-weight: bold;
                font-size: 11px;
            }
        """)

        main_layout.addWidget(self.table)

    def set_schedule(self, schedule: List[EclipseEvent], contacts: Dict[str, float]):
        """Carga y prepara la lista completa de eventos antes de iniciar la secuencia."""
        self.contacts = dict(contacts)
        records = []
        for idx, ev in enumerate(schedule, start=1):
            ref_name = ev.contact_ref
            t_ref = contacts.get(ref_name, contacts.get("C2", time.time()))
            sched_t = t_ref + ev.offset_seconds
            is_notice = not getattr(ev, "is_shot", True) or is_notice_event(ev)

            rec = ExecutionRecord(
                event_id=getattr(ev, "event_id", "") or f"L{idx:02d}",
                camera_slot=getattr(ev, "camera_slot", "A").upper(),
                phase=getattr(ev, "phase", ""),
                description=ev.description,
                shutter="--" if is_notice else ev.shutter_speed,
                iso="--" if is_notice else ev.iso,
                sched_timestamp=sched_t,
                status="PENDING",
                event_ref=ev
            )
            records.append(rec)

        self.model.set_records(records)
        self._update_stats()

    def record_shot(
        self,
        event: EclipseEvent,
        real_time: float,
        success: bool = True,
        shutter: str = "",
        iso: str = "",
        camera_slot: str = ""
    ):
        """Registra la ejecución efectiva de un disparo y calcula el jitter en milisegundos."""
        found_idx = self._find_event_index(event)

        if found_idx >= 0:
            rec = self.model.records[found_idx]
            rec.real_timestamp = real_time
            rec.jitter_ms = calculate_jitter_ms(rec.sched_timestamp, real_time)
            rec.status = "DONE" if success else "FAIL"
            if shutter and rec.shutter != "--":
                rec.shutter = shutter
            if iso and rec.iso != "--":
                rec.iso = iso
            if camera_slot:
                rec.camera_slot = camera_slot.upper()
            self.model.update_row(found_idx)
            self.table.scrollTo(self.model.index(found_idx, 0))
        else:
            # Evento imprevisto o manual
            sched_t = real_time
            jitter = 0.0
            is_notice = not getattr(event, "is_shot", True) or is_notice_event(event)
            rec = ExecutionRecord(
                event_id=getattr(event, "event_id", "L??"),
                camera_slot=(camera_slot or getattr(event, "camera_slot", "A")).upper(),
                phase=getattr(event, "phase", "PR"),
                description=event.description,
                shutter="--" if is_notice else (shutter or event.shutter_speed),
                iso="--" if is_notice else (iso or event.iso),
                sched_timestamp=sched_t,
                real_timestamp=real_time,
                jitter_ms=jitter,
                status="DONE" if success else "FAIL",
                event_ref=event
            )
            self.model.records.append(rec)
            self.model.beginResetModel()
            self.model.endResetModel()
            self.table.scrollTo(self.model.index(len(self.model.records) - 1, 0))

        self._update_stats()

    def record_skip(self, event: EclipseEvent, delay_s: float, camera_slot: str = ""):
        """Registra una omisión por política drop-and-skip."""
        found_idx = self._find_event_index(event)
        delay_ms = delay_s * 1000.0

        if found_idx >= 0:
            rec = self.model.records[found_idx]
            rec.jitter_ms = delay_ms
            rec.status = "SKIPPED"
            if camera_slot:
                rec.camera_slot = camera_slot.upper()
            self.model.update_row(found_idx)
            self.table.scrollTo(self.model.index(found_idx, 0))
        else:
            rec = ExecutionRecord(
                event_id=getattr(event, "event_id", "L??"),
                camera_slot=(camera_slot or getattr(event, "camera_slot", "A")).upper(),
                phase=getattr(event, "phase", ""),
                description=event.description,
                shutter=event.shutter_speed,
                iso=event.iso,
                sched_timestamp=time.time() - delay_s,
                jitter_ms=delay_ms,
                status="SKIPPED",
                event_ref=event
            )
            self.model.records.append(rec)
            self.model.beginResetModel()
            self.model.endResetModel()

        self._update_stats()

    def _find_event_index(self, event: EclipseEvent) -> int:
        """Busca el índice de un evento en el log por referencia, id o descripción."""
        for idx, rec in enumerate(self.model.records):
            if rec.event_ref is event:
                return idx
            if getattr(event, "event_id", "") and rec.event_id == getattr(event, "event_id", ""):
                return idx
            if rec.description == event.description and rec.status == "PENDING":
                return idx
        return -1

    def _update_stats(self):
        """Actualiza el resumen superior con conteo y promedio de jitter."""
        total = len(self.model.records)
        done = sum(1 for r in self.model.records if r.status == "DONE")
        skipped = sum(1 for r in self.model.records if r.status == "SKIPPED")
        errors = sum(1 for r in self.model.records if r.status in ("FAIL", "ERROR"))

        jitters = [r.jitter_ms for r in self.model.records if r.jitter_ms is not None and r.status == "DONE"]
        if jitters:
            avg_j = sum(jitters) / len(jitters)
            jitter_str = f"{avg_j:+.1f} ms"
        else:
            jitter_str = "--"

        self.lbl_stats.setText(
            f"📊 {total} eventos | {done} ejecutados con éxito | {skipped} omitidos | {errors} errores | Jitter medio: {jitter_str}"
        )

    def get_jitter_values(self) -> List[float]:
        """Retorna lista de todos los jitters registrados en milisegundos."""
        return [r.jitter_ms for r in self.model.records if r.jitter_ms is not None]

    def clear_log(self):
        """Reinicia el log."""
        self.model.clear()
        self._update_stats()
