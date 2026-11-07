"""
Banner Horizontal Dinámico NEXT para eclipZe v2.0 (Rediseño HUD Fase 2).
Muestra dos bloques claramente diferenciados:
  - Izquierda: Próxima micro-acción inminente con cuenta atrás milimétrica (T - MM:SS.mmm)
    y tipografía HUD ampliada legible bajo luz solar.
  - Derecha: Hito astronómico principal de referencia (C2 EN: MM:SS o FIN TOTALIDAD EN: MM:SS).
Código de colores por proximidad temporal:
  - T > 10s: Azul neutro (#38BDF8)
  - T <= 10s: Naranja de atención (#F59E0B)
  - T <= 3s: Rojo de disparo inminente (#EF4444)
"""

import time
from typing import Optional
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.presets import EclipseEvent, is_notice_event


def format_countdown_ms(time_to_shot: float) -> str:
    """Formatea la cuenta atrás en formato T - MM:SS.mmm."""
    if time_to_shot > 0:
        total_ms = int(round(time_to_shot * 1000))
        minutes = total_ms // 60000
        seconds = (total_ms % 60000) // 1000
        ms = total_ms % 1000
        return f"T - {minutes:02d}:{seconds:02d}.{ms:03d}"
    else:
        return "T - 00:00.000"


def get_proximity_color(time_to_shot: float) -> str:
    """Devuelve el código hexadecimal según el umbral de proximidad temporal."""
    if time_to_shot > 10.0:
        return "#38BDF8"  # Azul neutro
    elif time_to_shot > 3.0:
        return "#F59E0B"  # Naranja atención
    else:
        return "#EF4444"  # Rojo inminente


class NextBannerWidget(QFrame):
    """
    Banner horizontal de cabina tipo HUD dividido en dos bloques:
    1. Bloque Izquierdo: Próxima micro-acción inminente (cuenta atrás milimétrica y parámetros).
    2. Bloque Derecho: Hito astronómico principal de referencia (fijo y destacado).
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.current_color: str = "#38BDF8"
        self.contacts: Optional[dict] = None
        self.is_annular: bool = False
        self._init_ui()
        self.set_idle()

    def _init_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumHeight(64)

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(6, 4, 6, 4)
        root_layout.setSpacing(8)

        # =========================================================================
        # BLOQUE IZQUIERDO: Próxima Micro-Acción Inminente (HUD Grande)
        # =========================================================================
        self.block_left = QFrame()
        self.block_left.setObjectName("block_left")
        left_layout = QHBoxLayout(self.block_left)
        left_layout.setContentsMargins(10, 6, 10, 6)
        left_layout.setSpacing(10)

        # 1. Pill badge NEXT
        self.lbl_badge = QLabel("▶ NEXT")
        self.lbl_badge.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.lbl_badge.setAlignment(Qt.AlignCenter)
        self.lbl_badge.setFixedWidth(80)
        self.lbl_badge.setStyleSheet("""
            background-color: #0369A1;
            color: #FFFFFF;
            border-radius: 4px;
            padding: 4px 6px;
        """)
        left_layout.addWidget(self.lbl_badge)

        # 2. Contador de micro-acción (HUD tipografía grande de alto contraste)
        self.lbl_countdown = QLabel("T - --:--.---")
        self.lbl_countdown.setFont(QFont("Consolas", 22, QFont.Bold))
        self.lbl_countdown.setStyleSheet("color: #38BDF8; font-family: Consolas; font-size: 24px; font-weight: bold;")
        self.lbl_countdown.setFixedWidth(245)
        left_layout.addWidget(self.lbl_countdown)

        # Separador visual vertical
        self.lbl_sep = QLabel("|")
        self.lbl_sep.setStyleSheet("color: #374151; font-size: 20px; font-weight: bold;")
        left_layout.addWidget(self.lbl_sep)

        # 3. Información detallada del disparo / micro-acción
        self.lbl_target = QLabel("Esperando inicio de secuencia...")
        self.lbl_target.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.lbl_target.setStyleSheet("color: #F3F4F6;")
        left_layout.addWidget(self.lbl_target, stretch=1)

        root_layout.addWidget(self.block_left, stretch=1)

        # =========================================================================
        # BLOQUE DERECHO: Hito Astronómico Principal de Referencia (Fijo y Destacado)
        # =========================================================================
        self.block_right = QFrame()
        self.block_right.setObjectName("block_right")
        self.block_right.setFixedWidth(275)
        right_layout = QVBoxLayout(self.block_right)
        right_layout.setContentsMargins(10, 4, 10, 4)
        right_layout.setSpacing(0)

        self.lbl_milestone_title = QLabel("🌑 HITO PRINCIPAL")
        self.lbl_milestone_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.lbl_milestone_title.setStyleSheet("color: #94A3B8; font-size: 10px; font-weight: bold;")
        right_layout.addWidget(self.lbl_milestone_title)

        self.lbl_milestone = QLabel("C2 EN: --:--s")
        self.lbl_milestone.setFont(QFont("Consolas", 18, QFont.Bold))
        self.lbl_milestone.setStyleSheet("color: #FACC15; font-family: Consolas; font-size: 20px; font-weight: bold;")
        right_layout.addWidget(self.lbl_milestone)

        root_layout.addWidget(self.block_right)

        self._apply_border_style("#38BDF8")

    def _apply_border_style(self, color_hex: str):
        """Aplica el tema oscuro con acento en el color de alerta para el bloque izquierdo."""
        self.current_color = color_hex
        self.setStyleSheet("""
            NextBannerWidget {
                background-color: #0A0E17;
                border: 1px solid #1E293B;
                border-radius: 8px;
            }
        """)
        self.block_left.setStyleSheet(f"""
            QFrame#block_left {{
                background-color: #0B111E;
                border: 1px solid {color_hex};
                border-left: 5px solid {color_hex};
                border-radius: 6px;
            }}
        """)
        self.lbl_countdown.setStyleSheet(f"color: {color_hex}; font-family: Consolas; font-size: 24px; font-weight: bold;")

    def set_contacts(self, contacts: Optional[dict], is_annular: bool = False):
        """Configura el diccionario de contactos astronómicos absolutos."""
        self.contacts = dict(contacts) if contacts else None
        self.is_annular = is_annular

    def set_milestone(self, text: str, title: Optional[str] = None):
        """Asigna directamente el texto y título del hito astronómico."""
        self.lbl_milestone.setText(text)
        if title:
            self.lbl_milestone_title.setText(title)

    def get_milestone_text(self) -> str:
        """Retorna el texto actual del hito principal (ej. 'C2 EN: 00:19s')."""
        return self.lbl_milestone.text()

    def update_countdown(
        self,
        time_to_shot: float,
        event: Optional[EclipseEvent] = None,
        now: Optional[float] = None,
        contacts: Optional[dict] = None
    ):
        """Actualiza la cuenta atrás granular del disparo y el hito astronómico de referencia."""
        color = get_proximity_color(time_to_shot)
        self._apply_border_style(color)

        # 1. Bloque Izquierdo: Cuenta atrás de micro-acción
        if time_to_shot > 0:
            self.lbl_countdown.setText(format_countdown_ms(time_to_shot))
        else:
            self.lbl_countdown.setText("T - 00:00.000 (DISPARANDO)")

        # Datos descriptivos del evento
        if event:
            ev_id = getattr(event, "event_id", "L??")
            desc = event.description
            slot = getattr(event, "camera_slot", "A").upper()
            slot_badge = f"[CÁMARA {slot}]"
            is_notice = not getattr(event, "is_shot", True) or is_notice_event(event)

            if is_notice:
                full_text = f"{ev_id}  📢 {desc}  {slot_badge}"
            else:
                speed = event.shutter_speed
                aperture = getattr(event, "aperture", "f/5.6")
                iso = event.iso
                full_text = f"{ev_id}  {speed}  {aperture}  ISO {iso} — {desc}  {slot_badge}"
            self.lbl_target.setText(full_text)
        else:
            self.lbl_target.setText("Disparo inminente...")

        # 2. Bloque Derecho: Actualizar hito astronómico de referencia
        self._update_milestone(time_to_shot, event, now, contacts)

    def _update_milestone(
        self,
        time_to_shot: float,
        event: Optional[EclipseEvent] = None,
        now: Optional[float] = None,
        contacts: Optional[dict] = None
    ):
        """Calcula el hito astronómico principal de referencia (C2, FIN TOTALIDAD / C3, C4 o MAX)."""
        active_contacts = contacts or self.contacts
        t_now = now if now is not None else time.time()

        if active_contacts:
            t_c2 = active_contacts.get("C2") or active_contacts.get("U2")
            t_c3 = active_contacts.get("C3") or active_contacts.get("U3")
            t_c4 = active_contacts.get("C4")
            t_max = active_contacts.get("MAX")

            if t_c2 and t_now < t_c2:
                rem = max(0.0, t_c2 - t_now)
                m = int(rem // 60)
                s = int(rem % 60)
                title = "💍 INICIO ANULARIDAD (C2)" if self.is_annular else "🌑 INICIO TOTALIDAD (C2)"
                self.lbl_milestone_title.setText(title)
                self.lbl_milestone.setText(f"C2 EN: {m:02d}:{s:02d}s")
                self.lbl_milestone.setStyleSheet("color: #FACC15; font-family: Consolas; font-size: 20px; font-weight: bold;")
                self.block_right.setStyleSheet("QFrame#block_right { background-color: #121D30; border: 1.5px solid #38BDF8; border-radius: 6px; }")
                return

            if t_c3 and t_now < t_c3:
                rem = max(0.0, t_c3 - t_now)
                m = int(rem // 60)
                s = int(rem % 60)
                title = "💍 ANULARIDAD EN CURSO" if self.is_annular else "✨ TOTALIDAD EN CURSO"
                txt = f"FIN ANULARIDAD EN: {m:02d}:{s:02d}s" if self.is_annular else f"FIN TOTALIDAD EN: {m:02d}:{s:02d}s"
                self.lbl_milestone_title.setText(title)
                self.lbl_milestone.setText(txt)
                self.lbl_milestone.setStyleSheet("color: #34D399; font-family: Consolas; font-size: 20px; font-weight: bold;")
                self.block_right.setStyleSheet("QFrame#block_right { background-color: #064E3B; border: 1.5px solid #10B981; border-radius: 6px; }")
                return

            if t_c4 and t_now < t_c4:
                rem = max(0.0, t_c4 - t_now)
                m = int(rem // 60)
                s = int(rem % 60)
                self.lbl_milestone_title.setText("☀️ FIN DE ECLIPSE (C4)")
                self.lbl_milestone.setText(f"FIN ECLIPSE EN: {m:02d}:{s:02d}s")
                self.lbl_milestone.setStyleSheet("color: #38BDF8; font-family: Consolas; font-size: 20px; font-weight: bold;")
                self.block_right.setStyleSheet("QFrame#block_right { background-color: #121D30; border: 1.5px solid #38BDF8; border-radius: 6px; }")
                return

            if t_max and t_now < t_max:
                rem = max(0.0, t_max - t_now)
                m = int(rem // 60)
                s = int(rem % 60)
                self.lbl_milestone_title.setText("⚡ MÁXIMO DEL ECLIPSE")
                self.lbl_milestone.setText(f"MAX EN: {m:02d}:{s:02d}s")
                self.lbl_milestone.setStyleSheet("color: #F59E0B; font-family: Consolas; font-size: 20px; font-weight: bold;")
                self.block_right.setStyleSheet("QFrame#block_right { background-color: #121D30; border: 1.5px solid #F59E0B; border-radius: 6px; }")
                return

        # Fallback analítico a partir del contacto y offset del evento inmediato
        if event and time_to_shot is not None:
            contact_ref = getattr(event, "contact_ref", "")
            offset = getattr(event, "offset_seconds", 0.0)
            time_to_contact = max(0.0, time_to_shot - offset)
            m = int(time_to_contact // 60)
            s = int(time_to_contact % 60)

            if contact_ref in ("C2", "U2"):
                if time_to_contact > 0.5:
                    title = "💍 INICIO ANULARIDAD (C2)" if self.is_annular else "🌑 INICIO TOTALIDAD (C2)"
                    self.lbl_milestone_title.setText(title)
                    self.lbl_milestone.setText(f"C2 EN: {m:02d}:{s:02d}s")
                    self.lbl_milestone.setStyleSheet("color: #FACC15; font-family: Consolas; font-size: 20px; font-weight: bold;")
                    self.block_right.setStyleSheet("QFrame#block_right { background-color: #121D30; border: 1.5px solid #38BDF8; border-radius: 6px; }")
                else:
                    title = "💍 ANULARIDAD EN CURSO" if self.is_annular else "✨ TOTALIDAD EN CURSO"
                    txt = "ANULARIDAD ACTIVA" if self.is_annular else "TOTALIDAD ACTIVA"
                    self.lbl_milestone_title.setText(title)
                    self.lbl_milestone.setText(txt)
                    self.lbl_milestone.setStyleSheet("color: #34D399; font-family: Consolas; font-size: 20px; font-weight: bold;")
                    self.block_right.setStyleSheet("QFrame#block_right { background-color: #064E3B; border: 1.5px solid #10B981; border-radius: 6px; }")
            elif contact_ref in ("C3", "U3"):
                title = "💍 ANULARIDAD EN CURSO" if self.is_annular else "✨ TOTALIDAD EN CURSO"
                txt = f"FIN ANULARIDAD EN: {m:02d}:{s:02d}s" if self.is_annular else f"FIN TOTALIDAD EN: {m:02d}:{s:02d}s"
                self.lbl_milestone_title.setText(title)
                self.lbl_milestone.setText(txt)
                self.lbl_milestone.setStyleSheet("color: #34D399; font-family: Consolas; font-size: 20px; font-weight: bold;")
                self.block_right.setStyleSheet("QFrame#block_right { background-color: #064E3B; border: 1.5px solid #10B981; border-radius: 6px; }")
            elif contact_ref:
                self.lbl_milestone_title.setText(f"HITO: {contact_ref}")
                self.lbl_milestone.setText(f"{contact_ref} EN: {m:02d}:{s:02d}s")
                self.lbl_milestone.setStyleSheet("color: #38BDF8; font-family: Consolas; font-size: 20px; font-weight: bold;")
                self.block_right.setStyleSheet("QFrame#block_right { background-color: #121D30; border: 1.5px solid #38BDF8; border-radius: 6px; }")

    def set_idle(self, message: str = "Secuencia detenida o en espera"):
        """Estado pasivo antes de iniciar o tras detener la secuencia."""
        self._apply_border_style("#38BDF8")
        self.lbl_countdown.setText("T - --:--.---")
        self.lbl_target.setText(message)
        self.lbl_milestone_title.setText("🌑 HITO PRINCIPAL")
        self.lbl_milestone.setText("C2 EN: --:--s")
        self.lbl_milestone.setStyleSheet("color: #94A3B8; font-family: Consolas; font-size: 20px; font-weight: bold;")
        self.block_right.setStyleSheet("QFrame#block_right { background-color: #121D30; border: 1.5px solid #38BDF8; border-radius: 6px; }")

    def set_finished(self, message: str = "Secuencia completada con éxito."):
        """Estado al finalizar la totalidad de los disparos."""
        self._apply_border_style("#10B981")
        self.lbl_countdown.setText("COMPLETADO")
        self.lbl_target.setText(message)
        self.lbl_milestone_title.setText("🌑 SECUENCIA")
        self.lbl_milestone.setText("FINALIZADA")
        self.lbl_milestone.setStyleSheet("color: #10B981; font-family: Consolas; font-size: 20px; font-weight: bold;")
        self.block_right.setStyleSheet("QFrame#block_right { background-color: #064E3B; border: 1.5px solid #10B981; border-radius: 6px; }")

    def get_countdown_text(self) -> str:
        """Retorna el texto actual de la cuenta atrás (para tests y validación)."""
        return self.lbl_countdown.text()

    def get_target_text(self) -> str:
        """Retorna el texto descriptivo del objetivo."""
        return self.lbl_target.text()
