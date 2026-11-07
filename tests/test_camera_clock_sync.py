"""
Tests unitarios para la sincronización horaria de cámara mediante GPS y PTP en eclipZe.
Verifica:
1. Parser PTP ISO 8601 (parse_ptp_datetime) con subsegundos y husos horarios.
2. Lectura y ajuste del reloj RTC en CameraDriver / MockCameraDriver.
3. Telemetría de reloj y sincronización inteligente en EquipmentManager (Local vs UTC).
4. Integración en los controles de la interfaz MainWindow.
"""

import os
import sys
import datetime
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

from core.camera import parse_ptp_datetime, MockCameraDriver
from core.equipment import EquipmentManager
from core.gps import GPSData
from ui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_parse_ptp_datetime():
    # Caso 1: Cadena PTP estándar sin subsegundos ni zona
    dt = parse_ptp_datetime("20261106T093015")
    assert dt is not None
    assert dt.year == 2026 and dt.month == 11 and dt.day == 6
    assert dt.hour == 9 and dt.minute == 30 and dt.second == 15
    assert dt.microsecond == 0
    assert dt.tzinfo is None

    # Caso 2: Con décimas de segundo (.5 -> 500000 microsegundos)
    dt2 = parse_ptp_datetime("20261106T093015.5")
    assert dt2 is not None
    assert dt2.second == 15
    assert dt2.microsecond == 500000

    # Caso 3: Con zona horaria UTC 'Z'
    dt3 = parse_ptp_datetime("20261106T093015Z")
    assert dt3 is not None
    assert dt3.tzinfo == datetime.timezone.utc

    # Caso 4: Con offset +0200 (CEST España verano)
    dt4 = parse_ptp_datetime("20260812T193000+0200")
    assert dt4 is not None
    assert dt4.hour == 19
    assert dt4.tzinfo is not None
    assert dt4.tzinfo.utcoffset(None) == datetime.timedelta(hours=2)

    # Caso 5: Cadenas inválidas
    assert parse_ptp_datetime("") is None
    assert parse_ptp_datetime(None) is None
    assert parse_ptp_datetime("invalid-string") is None


def test_mock_camera_driver_clock():
    drv = MockCameraDriver()
    t_read = drv.get_clock_time()
    assert t_read is not None

    # Ajustar a una hora fija (10 segundos en el futuro)
    target = datetime.datetime.now() + datetime.timedelta(seconds=10)
    ok = drv.set_clock_time(target)
    assert ok is True

    t_after = drv.get_clock_time()
    diff = (t_after - datetime.datetime.now()).total_seconds()
    assert 9.0 <= diff <= 11.0


def test_equipment_manager_clock_telemetry_and_sync():
    em = EquipmentManager()

    # 1. Lectura inicial en Ranura A
    read_a = em.read_camera_clock("A")
    assert read_a["ok"] is True
    assert "clock_str" in read_a
    assert "delta_sec" in read_a
    assert read_a["status"] in ("synced", "drift", "desynced")

    # 2. Sincronización en modo Local sin GPS fix (fallback a reloj de sistema)
    ok, msg, prev_delta = em.sync_camera_clock("A", gps_data=None, use_utc=False)
    assert ok is True
    assert "Hora Local" in msg

    # Comprobar que el slot quedó sincronizado
    tel_a = em.get_telemetry("A")
    assert tel_a["clock_sync_status"] == "synced"
    assert abs(tel_a["clock_delta_sec"]) < 0.25

    # 3. Sincronización con GPS simulado con Fix
    gps = GPSData()
    gps.connected = True
    gps.has_fix = True
    gps.satellites = 8
    gps.clock_offset_seconds = 0.05
    gps.utc_time = datetime.datetime.now(datetime.timezone.utc)

    ok_gps, msg_gps, _ = em.sync_camera_clock("B", gps_data=gps, use_utc=True)
    assert ok_gps is True
    assert "UTC" in msg_gps

    # 4. Sincronización global (A y B)
    all_res = em.sync_all_cameras(gps_data=gps, use_utc=False)
    assert "A" in all_res and "B" in all_res
    assert all_res["A"][0] is True
    assert all_res["B"][0] is True


def test_main_window_clock_sync_ui(qapp):
    win = MainWindow()
    win.show()

    # Verificar que los widgets existen
    assert hasattr(win, "btn_sync_all_clocks")
    assert hasattr(win, "combo_time_mode")
    assert hasattr(win, "lbl_clock_cam_a")
    assert hasattr(win, "lbl_clock_delta_a")
    assert hasattr(win, "btn_sync_clock_a")
    assert hasattr(win, "lbl_clock_cam_b")
    assert hasattr(win, "lbl_clock_delta_b")
    assert hasattr(win, "btn_sync_clock_b")

    # Ejecutar clic en sincronización de Cámara Principal
    win.btn_sync_clock_a.click()
    assert "Cámara Principal: Reloj calibrado" in win.txt_log.toPlainText()

    # Ejecutar sincronización de ambas cámaras
    win.btn_sync_all_clocks.click()
    assert "Cámara Secundaria: Reloj calibrado" in win.txt_log.toPlainText()

    win.close()
