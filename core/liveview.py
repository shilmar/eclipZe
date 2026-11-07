"""
Núcleo de Asistente de Enfoque (Focus Assist) y Procesamiento de Live View para eclipZe v2.0.
Calcula el Focus Score mediante varianza del Laplaciano sobre Región de Interés (ROI),
mantiene el filtro Peak Hold para retención de picos máximos y aplica corte de seguridad (2 min).
"""

import time
import threading
from typing import Optional, Tuple, Union

import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

from PySide6.QtCore import QThread, Signal, QObject
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QFont
from PySide6.QtCore import Qt, QRect

from .camera import CameraDriver


# Corte de seguridad obligatorio 2 minutos (120 segundos) antes del inicio de secuencia
SAFETY_CUTOFF_SECONDS: float = 120.0


def is_safety_cutoff_needed(time_to_start_s: float) -> bool:
    """Verifica si el tiempo restante hasta el inicio de la secuencia requiere apagar Live View."""
    return time_to_start_s <= SAFETY_CUTOFF_SECONDS


def check_saturation(
    image_data: Union[bytes, np.ndarray],
    roi_box: Optional[Tuple[int, int, int, int]] = None,
    threshold: int = 254,
    sat_ratio_limit: float = 0.05
) -> Tuple[bool, float]:
    """
    Comprueba si el canal rojo del sensor se satura (píxeles >= threshold, picos a 255)
    en más del porcentaje límite (sat_ratio_limit, por defecto 5%) dentro del área evaluada.
    Previene falsos positivos de nitidez máxima por clipping sobre el disco solar.

    :return: (is_saturated: bool, saturation_ratio: float)
    """
    red_channel: Optional[np.ndarray] = None

    if isinstance(image_data, bytes):
        if cv2 is not None:
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is not None:
                red_channel = img[:, :, 2]  # BGR: canal 2 es Rojo
        else:
            try:
                import io
                from PIL import Image
                pil_img = Image.open(io.BytesIO(image_data)).convert("RGB")
                arr = np.array(pil_img, dtype=np.uint8)
                red_channel = arr[:, :, 0]  # RGB: canal 0 es Rojo
            except Exception:
                return False, 0.0
    elif isinstance(image_data, np.ndarray):
        if image_data.ndim == 3:
            if cv2 is not None:
                red_channel = np.maximum(image_data[:, :, 0], image_data[:, :, 2])
            else:
                red_channel = image_data[:, :, 0]
        elif image_data.ndim == 2:
            red_channel = image_data

    if red_channel is None or red_channel.size == 0:
        return False, 0.0

    if roi_box is not None:
        rx, ry, rw, rh = roi_box
        h, w = red_channel.shape[:2]
        x1 = max(0, min(w - 1, rx))
        y1 = max(0, min(h - 1, ry))
        x2 = max(x1 + 1, min(w, x1 + rw))
        y2 = max(y1 + 1, min(h, y1 + rh))
        roi = red_channel[y1:y2, x1:x2]
    else:
        roi = red_channel

    if roi.size == 0:
        return False, 0.0

    sat_count = int(np.count_nonzero(roi >= threshold))
    ratio = float(sat_count) / float(roi.size)
    return (ratio >= sat_ratio_limit, ratio)


def calculate_focus_score(
    image_data: Union[bytes, np.ndarray],
    roi_box: Optional[Tuple[int, int, int, int]] = None
) -> float:
    """
    Calcula el Focus Score de una imagen o recorte ROI mediante la varianza del Laplaciano:
    Focus Score = Var(∇² I)
    
    :param image_data: Trama JPEG (bytes) o array numpy (uint8 en escala de grises o BGR/RGB).
    :param roi_box: Opcional (x, y, w, h) en píxeles para evaluar solo la Región de Interés.
    :return: Valor numérico positivo de nitidez (mayor valor = mayor nitidez y contraste de frecuencias altas).
    """
    gray: Optional[np.ndarray] = None

    if isinstance(image_data, bytes):
        if cv2 is not None:
            nparr = np.frombuffer(image_data, np.uint8)
            gray = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        else:
            try:
                import io
                from PIL import Image
                pil_img = Image.open(io.BytesIO(image_data)).convert("L")
                gray = np.array(pil_img, dtype=np.uint8)
            except Exception:
                return 0.0
    elif isinstance(image_data, np.ndarray):
        if image_data.ndim == 3:
            if cv2 is not None:
                gray = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
            else:
                gray = np.mean(image_data, axis=2).astype(np.uint8)
        else:
            gray = image_data

    if gray is None or gray.size == 0:
        return 0.0

    # Recortar Región de Interés (ROI) si se especifica
    if roi_box is not None:
        rx, ry, rw, rh = roi_box
        h, w = gray.shape[:2]
        x1 = max(0, min(w - 1, rx))
        y1 = max(0, min(h - 1, ry))
        x2 = max(x1 + 1, min(w, x1 + rw))
        y2 = max(y1 + 1, min(h, y1 + rh))
        roi = gray[y1:y2, x1:x2]
    else:
        roi = gray

    if roi.size < 9:
        return 0.0

    # Convolución con kernel Laplaciano y cálculo de varianza
    if cv2 is not None:
        lap = cv2.Laplacian(roi, cv2.CV_64F)
        score = float(lap.var())
    else:
        # Fallback analítico mediante convolución 2D con kernel 3x3 estándar
        # [[0, 1, 0], [1, -4, 1], [0, 1, 0]]
        roi_f = roi.astype(np.float64)
        lap = (
            np.roll(roi_f, 1, axis=0) +
            np.roll(roi_f, -1, axis=0) +
            np.roll(roi_f, 1, axis=1) +
            np.roll(roi_f, -1, axis=1) -
            4.0 * roi_f
        )[1:-1, 1:-1]
        score = float(np.var(lap)) if lap.size > 0 else 0.0

    return max(0.0, score)


class PeakHoldFilter:
    """
    Filtro de retención de pico (Peak Hold) para registrar y retener el valor máximo histórico
    de nitidez durante la sesión de calibración de foco astronómico.
    """

    def __init__(self, decay_rate: float = 0.0):
        self.decay_rate = max(0.0, min(1.0, float(decay_rate)))
        self.peak: float = 0.0
        self.last_score: float = 0.0

    def update(self, score: float) -> float:
        """Actualiza el filtro con el nuevo score y retorna el valor pico actual."""
        s = max(0.0, float(score))
        self.last_score = s
        if s > self.peak:
            self.peak = s
        elif self.decay_rate > 0.0:
            self.peak = max(s, self.peak * (1.0 - self.decay_rate))
        return self.peak

    def reset(self):
        """Reinicia el pico retenido a cero."""
        self.peak = 0.0
        self.last_score = 0.0

    def get_peak(self) -> float:
        return self.peak

    def get_normalized(self, score: float) -> float:
        """
        Retorna la eficiencia porcentual (0.0% a 100.0%) respecto al pico máximo histórico.
        Si aún no hay pico histórico, retorna 0.0% (o 100.0% si score > 0).
        """
        if self.peak <= 0.0:
            return 100.0 if score > 0.0 else 0.0
        return min(100.0, max(0.0, (float(score) / self.peak) * 100.0))


class FocusMetricWorker(QThread):
    """
    Hilo secundario Qt para la adquisición en segundo plano de tramas Live View,
    recorte digital ROI (1x, 5x, 10x), cálculo del Focus Score y emisión de QImage.
    """

    frame_ready = Signal(QImage, float, float, float)   # qimage, current_score, peak_score, norm_pct
    saturation_detected = Signal(bool, float)          # (is_saturated, sat_ratio)
    safety_cutoff = Signal(str)                        # Motivo del corte de seguridad
    liveview_stopped = Signal()
    error_occurred = Signal(str)

    def __init__(self, driver: Optional[CameraDriver] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.driver: Optional[CameraDriver] = driver
        self.peak_filter = PeakHoldFilter()
        self.zoom: int = 1               # 1, 5 o 10
        self.center_x: float = 0.5       # Centro relativo X (0.0 a 1.0)
        self.center_y: float = 0.5       # Centro relativo Y (0.0 a 1.0)
        self.last_is_saturated: bool = False
        self.last_sat_ratio: float = 0.0
        self._stop_event = threading.Event()
        self._stop_event.set()           # Comienza detenido
        self._lock = threading.Lock()
        self.target_fps: float = 15.0

    def set_driver(self, driver: Optional[CameraDriver]):
        with self._lock:
            self.driver = driver
            self.peak_filter.reset()

    def set_zoom(self, zoom: int):
        with self._lock:
            self.zoom = 10 if zoom >= 10 else (5 if zoom >= 5 else 1)

    def set_roi_center(self, cx: float, cy: float):
        with self._lock:
            self.center_x = max(0.05, min(0.95, float(cx)))
            self.center_y = max(0.05, min(0.95, float(cy)))

    def reset_peak(self):
        with self._lock:
            self.peak_filter.reset()

    def start_worker(self):
        """Inicia el hilo limpiando la señal de parada de forma atómica."""
        self._stop_event.clear()
        self.start()

    def stop(self):
        """Detiene el hilo inmediatamente despertando cualquier espera activa."""
        self._stop_event.set()
        self.wait(1500)

    def run(self):
        if self._stop_event.is_set():
            return
        current_drv = self.driver
        if current_drv:
            try:
                current_drv.start_liveview()
            except Exception as e:
                self.error_occurred.emit(f"Error al iniciar Live View: {e}")

        frame_interval = 1.0 / max(1.0, self.target_fps)

        while not self._stop_event.is_set():
            t0 = time.time()
            with self._lock:
                drv = self.driver
                zoom = self.zoom
                cx = self.center_x
                cy = self.center_y

            if not drv:
                if self._stop_event.wait(0.1):
                    break
                continue

            try:
                raw_bytes = drv.get_liveview_frame()
                if raw_bytes and len(raw_bytes) > 10:
                    res = self._process_frame(raw_bytes, zoom, cx, cy)
                    if res[0] and not res[0].isNull() and not self._stop_event.is_set():
                        qimg, score, peak, norm, is_sat, sat_ratio = res
                        self.last_is_saturated = is_sat
                        self.last_sat_ratio = sat_ratio
                        self.frame_ready.emit(qimg, score, peak, norm)
                        self.saturation_detected.emit(is_sat, sat_ratio)
            except Exception as e:
                if not self._stop_event.is_set():
                    self.error_occurred.emit(str(e))

            elapsed = time.time() - t0
            sleep_time = max(0.005, frame_interval - elapsed)
            if self._stop_event.wait(sleep_time):
                break

        if self.driver:
            try:
                self.driver.stop_liveview()
            except Exception:
                pass

        self.liveview_stopped.emit()

    def _process_frame(
        self,
        raw_bytes: bytes,
        zoom: int,
        cx: float,
        cy: float
    ) -> Tuple[Optional[QImage], float, float, float, bool, float]:
        """Decodifica la trama JPEG, calcula el ROI, métrica y saturación, y compone el QImage."""
        # Decodificar imagen para métrica
        if cv2 is not None:
            arr = np.frombuffer(raw_bytes, np.uint8)
            img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img_bgr is None:
                return None, 0.0, 0.0, 0.0, False, 0.0
            h, w = img_bgr.shape[:2]
        else:
            import io
            from PIL import Image
            pil_img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
            w, h = pil_img.size
            img_bgr = None

        # Dimensiones del área ROI analizada
        roi_w = max(32, int(w / zoom))
        roi_h = max(24, int(h / zoom))
        roi_cx = int(cx * w)
        roi_cy = int(cy * h)

        rx = max(0, min(w - roi_w, roi_cx - roi_w // 2))
        ry = max(0, min(h - roi_h, roi_cy - roi_h // 2))
        roi_box = (rx, ry, roi_w, roi_h)

        # Cálculo de nitidez y saturación sobre el ROI
        if img_bgr is not None:
            roi_raw = img_bgr[ry:ry + roi_h, rx:rx + roi_w]
            gray_roi = cv2.cvtColor(roi_raw, cv2.COLOR_BGR2GRAY)
            score = calculate_focus_score(gray_roi)
            # Canal rojo en BGR es canal 2
            red_roi = roi_raw[:, :, 2]
            sat_count = int(np.count_nonzero(red_roi >= 254))
            sat_ratio = float(sat_count) / float(red_roi.size) if red_roi.size > 0 else 0.0
            is_saturated = (sat_ratio >= 0.05)
        else:
            score = calculate_focus_score(raw_bytes, roi_box=roi_box)
            is_saturated, sat_ratio = check_saturation(raw_bytes, roi_box=roi_box)

        peak = self.peak_filter.update(score)
        norm = self.peak_filter.get_normalized(score)

        # Conversión a QImage thread-safe
        qimg = QImage()
        qimg.loadFromData(raw_bytes, "JPEG")
        if qimg.isNull():
            return None, score, peak, norm, is_saturated, sat_ratio

        # Composición visual según el nivel de zoom usando QImage
        if zoom == 1:
            display_img = qimg.convertToFormat(QImage.Format_RGB32)
            painter = QPainter(display_img)
            try:
                # Recuadro ROI: Rojo si saturado, verde si óptimo, ámbar si intermedio
                if is_saturated:
                    box_color = QColor("#EF4444")
                    pen = QPen(box_color, 2, Qt.SolidLine)
                elif norm >= 90.0:
                    box_color = QColor("#10B981")
                    pen = QPen(box_color, 2, Qt.DashLine)
                else:
                    box_color = QColor("#F59E0B")
                    pen = QPen(box_color, 2, Qt.DashLine)

                painter.setPen(pen)
                painter.drawRect(rx, ry, roi_w, roi_h)

                if is_saturated:
                    painter.setPen(QPen(QColor("#EF4444"), 1))
                    painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
                    painter.drawText(rx + 4, max(14, ry - 4), f"⚠️ SATURADO R: {int(sat_ratio * 100)}%")

                # Retícula central de alineación astronómica
                pen_cross = QPen(QColor("#38BDF8"), 1, Qt.DotLine)
                painter.setPen(pen_cross)
                painter.drawLine(roi_cx - 15, roi_cy, roi_cx + 15, roi_cy)
                painter.drawLine(roi_cx, roi_cy - 15, roi_cx, roi_cy + 15)
            finally:
                painter.end()
            return display_img, score, peak, norm, is_saturated, sat_ratio
        else:
            # Zoom digital 5x o 10x: recortar ROI y escalar suavemente a resolución estándar
            cropped_qimg = qimg.copy(QRect(rx, ry, roi_w, roi_h))
            zoomed_img = cropped_qimg.scaled(
                w, h,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            ).convertToFormat(QImage.Format_RGB32)

            # Dibujar retícula central fina en el centro del zoom
            painter = QPainter(zoomed_img)
            try:
                zw, zh = zoomed_img.width(), zoomed_img.height()
                pen_cross = QPen(QColor("#EF4444") if is_saturated else (QColor("#10B981") if norm >= 90.0 else QColor("#38BDF8")), 1)
                painter.setPen(pen_cross)
                painter.drawLine(zw // 2 - 20, zh // 2, zw // 2 + 20, zh // 2)
                painter.drawLine(zw // 2, zh // 2 - 20, zw // 2, zh // 2 + 20)

                if is_saturated:
                    painter.setPen(QPen(QColor("#EF4444"), 1))
                    painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
                    painter.drawText(12, 24, f"⚠️ CANAL ROJO SATURADO ({int(sat_ratio * 100)}%)")
            finally:
                painter.end()
            return zoomed_img, score, peak, norm, is_saturated, sat_ratio
