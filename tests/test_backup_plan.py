"""
Tests unitarios para el generador de Plan Manual de Emergencia (core/backup_plan.py).
"""

import os
import time
import pytest
from core.backup_plan import (
    generate_backup_plan_html,
    format_timestamp_utc,
    format_timestamp_local,
    format_duration_mm_ss
)


def test_format_helpers():
    # Duración
    assert format_duration_mm_ss(0) == "00m 00s"
    assert format_duration_mm_ss(112.0) == "01m 52s"
    assert format_duration_mm_ss(113.0) == "01m 53s"
    assert format_duration_mm_ss(3600) == "60m 00s"

    # None handling
    assert format_timestamp_utc(None) == "--:--:--"
    assert format_timestamp_local(None) == "--:--:--"

    # UTC format
    ts = 1786559179.0  # 2026-08-12 18:26:19 UTC
    formatted_utc = format_timestamp_utc(ts)
    assert "18:26:19 UTC" in formatted_utc

    # Local format with specific timezone offset
    formatted_local = format_timestamp_local(ts, tz_offset_hours=2.0)
    assert "20:26:19" in formatted_local
    assert "UTC+2" in formatted_local


def test_generate_backup_plan_html_content(tmp_path):
    out_file = str(tmp_path / "test_plan.html")

    contacts = {
        "C1": 1786555279.0,
        "C2": 1786559179.0,
        "MAX": 1786559235.0,
        "C3": 1786559291.0,
        "C4": 1786563191.0
    }

    result_path = generate_backup_plan_html(
        eclipse_name="Eclipse Solar 2026 (Ponferrada)",
        location_name="Castillo de los Templarios, Ponferrada",
        lat=42.545,
        lon=-6.592,
        alt_m=540,
        visibility="totality",
        totality_duration_s=112.0,
        sun_altitude_deg=10.8,
        sun_azimuth_deg=280.3,
        contacts=contacts,
        camera_name="Nikon Z5 II",
        lens_info="Tamron 150-500mm @ 500mm f/8",
        iso_default="200",
        output_path=out_file
    )

    assert result_path == out_file
    assert os.path.isfile(out_file)

    with open(out_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Validar secciones esenciales
    assert "eclipZe" in content
    assert "Ponferrada" in content
    assert "01m 52s" in content
    assert "RETIRAR FILTRO SOLAR" in content
    assert "COLOCAR FILTRO SOLAR" in content
    assert "Receta Manual de Rueda" in content
    assert "Perlas de Baily" in content
    assert "Checklist de Campo Pre-Eclipse" in content
    assert "Nikon Z5 II" in content
    assert "500mm f/8" in content
    assert "@media print" in content
    assert "window.print()" in content


def test_generate_backup_plan_annular_eclipse(tmp_path):
    out_file = str(tmp_path / "test_plan_annular.html")
    contacts = {
        "C1": 1832490000.0,
        "C2": 1832493600.0,
        "MAX": 1832493800.0,
        "C3": 1832494000.0,
        "C4": 1832497600.0
    }

    result_path = generate_backup_plan_html(
        eclipse_name="Eclipse Solar Anular 2028 (España)",
        location_name="Mallorca, España",
        lat=39.569,
        lon=2.650,
        alt_m=50,
        visibility="annularity",
        totality_duration_s=400.0,
        sun_altitude_deg=22.0,
        sun_azimuth_deg=210.0,
        contacts=contacts,
        camera_name="Nikon Z5 II",
        lens_info="500mm f/8",
        output_path=out_file
    )

    assert result_path == out_file
    assert os.path.isfile(out_file)

    with open(out_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Seguridad crítica: NO retirar filtro solar jamás
    assert "RETIRAR FILTRO SOLAR" not in content, "Un eclipse anular jamás debe ordenar retirar el filtro solar"
    assert "MANTENER FILTRO SOLAR PUESTO" in content
    assert "ANULARIDAD" in content
    assert "Anillo de Fuego" in content
    assert "NUNCA retires el filtro solar" in content
    assert "NUNCA mirar directamente sin filtro homologado" in content


def test_generate_backup_plan_without_contacts():
    # Debe funcionar sin fallar cuando no hay contactos calculados
    html = generate_backup_plan_html(
        eclipse_name="Simulación sin datos",
        contacts={}
    )
    assert "<!DOCTYPE html>" in html
    assert "Contactos pendientes de cálculo" in html
    assert "Checklist de Campo Pre-Eclipse" in html


from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication
from ui.calendar_view import EclipseCalendarWidget
from ui.main_window import MainWindow
from core.eclipse_db import EclipseCatalogManager


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_calendar_print_button_and_trigger(qapp, tmp_path):
    cat = EclipseCatalogManager()
    widget = EclipseCalendarWidget(catalog_manager=cat)
    assert hasattr(widget, "btn_print_plan")
    assert widget.btn_print_plan.text().startswith("📄")

    # Mock webbrowser.open
    with patch("webbrowser.open") as mock_open:
        widget._on_print_manual_plan()
        # Si no hay eclipse seleccionado, no debe fallar
        if widget.selected_eclipse and widget.last_result:
            assert mock_open.called


def test_mainwindow_manual_plan_button(qapp):
    with patch("webbrowser.open") as mock_open, \
         patch("PySide6.QtWidgets.QMessageBox.information"):
        win = MainWindow()
        assert hasattr(win, "btn_manual_plan")
        assert "Plan Manual" in win.btn_manual_plan.text()

        # Trigger plan generation
        win._generate_active_backup_plan()
        assert mock_open.called
        plan_path = mock_open.call_args[0][0]
        assert os.path.exists(plan_path)
        with open(plan_path, "r", encoding="utf-8") as f:
            data = f.read()
        assert "Plan de Respaldo Manual" in data
        assert "Checklist de Campo Pre-Eclipse" in data
        win.close()
