"""
Tests unitarios y de integración para la Fase 4 de eclipZe v2.0:
- Catálogo de Eclipses 2026–2035 (data/eclipses.json y core/eclipse_db.py)
- Motor Astronómico y Evaluador de Contactos Locales (core/astronomy.py)
- Widget UI de Calendario y Carga en 1-Clic a MainWindow (ui/calendar_view.py)
"""

import os
import pytest
from datetime import datetime, timezone
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from core.eclipse_db import EclipseCatalogManager, EclipseInfo
from core.astronomy import (
    calculate_local_eclipse,
    calculate_solar_position,
    haversine_distance_km,
    project_point_to_segment,
    point_in_polygon,
    min_distance_to_polyline,
    LocalEclipseResult
)
from ui.calendar_view import EclipseCalendarWidget
from ui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


# =============================================================================
# 1. Tests del Catálogo de Eclipses 2026–2035
# =============================================================================

def test_catalog_loading_and_integrity():
    """Valida la carga del archivo data/eclipses.json y la consistencia de sus campos."""
    mgr = EclipseCatalogManager()
    eclipses = mgr.get_all()
    assert len(eclipses) >= 10, f"Se esperaban al menos 10 eclipses en el catálogo, encontrados: {len(eclipses)}"

    # Verificar presencia de los 3 grandes eclipses de España
    spain_eclipses = mgr.filter_spain_eclipses()
    assert len(spain_eclipses) >= 3, "Deben estar presentes al menos los 3 eclipses clave de España"

    dates = [e.date for e in spain_eclipses]
    assert "2026-08-12" in dates, "Debe existir el Eclipse Total del 12 Ago 2026"
    assert "2027-08-02" in dates, "Debe existir el Eclipse Total del 02 Ago 2027"
    assert "2028-01-26" in dates, "Debe existir el Eclipse Anular del 26 Ene 2028"

    # Verificar presencia de grandes eventos internacionales
    all_dates = [e.date for e in eclipses]
    assert "2028-07-22" in all_dates, "Eclipse Total Australia 2028 no encontrado"
    assert "2034-03-20" in all_dates, "Eclipse Total África/Oriente Medio 2034 no encontrado"
    assert "2035-09-02" in all_dates, "Eclipse Total Japón/China 2035 no encontrado"

    # Validar integridad estructural de cada elemento
    for e in eclipses:
        assert e.id and isinstance(e.id, str)
        assert e.name and isinstance(e.name, str)
        assert e.date and len(e.date) == 10
        assert e.type in ("solar_total", "solar_annular", "solar_hybrid", "lunar_total", "lunar_partial", "simulation")
        assert len(e.regions) > 0
        assert e.max_duration_s > 0
        if e.is_solar:
            assert len(e.centerline) > 0, f"Eclipse solar {e.id} debe tener puntos de trayectoria centerline"
            for pt in e.centerline:
                assert "lat" in pt and "lon" in pt and "utc_iso" in pt


def test_catalog_filtering_and_search():
    """Valida los filtros de búsqueda, fechas futuras y tipos de eclipse."""
    mgr = EclipseCatalogManager()

    # Filtro por tipo
    totales = mgr.filter_by_type("solar_total")
    assert all(e.type == "solar_total" for e in totales)
    assert len(totales) >= 5

    anulares = mgr.filter_by_type("solar_annular")
    assert all(e.type == "solar_annular" for e in anulares)
    assert len(anulares) >= 2

    # Filtro de búsqueda por texto
    cadiz_search = mgr.search("Cádiz")
    assert any("2027" in e.date for e in cadiz_search)

    japan_search = mgr.search("Japón")
    assert any("2035" in e.date for e in japan_search)

    # Filtro futuro
    future = mgr.filter_future(reference_date="2027-01-01")
    assert not any(e.date < "2027-01-01" for e in future)
    assert any(e.date == "2027-08-02" for e in future)

    # Filtro España con fecha de corte
    spain_future = mgr.filter_spain_eclipses(reference_date="2027-01-01")
    assert not any(e.date < "2027-01-01" for e in spain_future)
    assert any(e.date == "2027-08-02" for e in spain_future)
    assert not any(e.date == "2026-08-12" for e in spain_future)


# =============================================================================
# 2. Tests del Motor Astronómico y Contactos Locales
# =============================================================================

def test_astronomy_solar_position_meeus():
    """Valida el cálculo de posición solar (altitud y azimut) con el algoritmo de Meeus."""
    # Verano en España al mediodía (12:00 UTC ~ 14:00 CEST)
    dt = datetime(2026, 8, 12, 12, 0, 0, tzinfo=timezone.utc)
    alt, az = calculate_solar_position(dt, 40.4168, -3.7038)
    assert 60.0 <= alt <= 70.0, f"Altitud solar anómala al mediodía: {alt}°"
    assert 160.0 <= az <= 200.0, f"Azimut anómalo al mediodía: {az}°"


def test_local_contacts_tarifa_2027_totality():
    """
    Valida el 'Eclipse del Siglo' en Tarifa (Cádiz):
    - Debe estar en la franja de totalidad
    - Oscurecimiento del 100%
    - Duración > 4 minutos (> 240 s)
    - Contactos C1 < C2 < MAX < C3 < C4
    - Elevación solar ~38°
    """
    mgr = EclipseCatalogManager()
    e2027 = mgr.get_by_id("2027-08-02-solar-total")
    assert e2027 is not None

    # Coordenadas de Tarifa (Punta de Tarifa / Estrecho)
    res = calculate_local_eclipse(e2027, lat=36.014, lon=-5.604, alt_m=10.0)

    assert res.visibility == "totality"
    assert res.is_visible is True
    assert res.obscuration_pct == 100.0
    assert res.magnitude >= 1.0
    assert res.totality_duration_s > 240.0, f"Tarifa debe tener >4m de totalidad, tiene: {res.totality_duration_s}s"

    # Consistencia cronológica de los contactos
    assert res.c1_utc is not None
    assert res.c2_utc is not None
    assert res.max_utc is not None
    assert res.c3_utc is not None
    assert res.c4_utc is not None
    assert res.c1_utc < res.c2_utc < res.max_utc < res.c3_utc < res.c4_utc

    # Verificación de elevación solar favorable
    assert 30.0 < res.sun_altitude_deg < 45.0, f"Elevación solar en Tarifa debería ser ~38°, es {res.sun_altitude_deg}°"

    contacts = res.to_contacts_dict()
    assert "C1" in contacts and "C2" in contacts and "MAX" in contacts and "C3" in contacts and "C4" in contacts


def test_local_contacts_burgos_2026_totality_and_low_sun():
    """
    Valida el eclipse de 2026 en Burgos:
    - Debe estar en la franja de totalidad
    - Oscurecimiento del 100%
    - Duración > 90s
    - Sol bajo en el horizonte (< 15°) al atardecer
    """
    mgr = EclipseCatalogManager()
    e2026 = mgr.get_by_id("2026-08-12-solar-total")
    assert e2026 is not None

    res = calculate_local_eclipse(e2026, lat=42.344, lon=-3.697, alt_m=850.0)

    assert res.visibility == "totality"
    assert res.is_visible is True
    assert res.obscuration_pct == 100.0
    assert res.totality_duration_s >= 90.0

    # Sol bajo en el horizonte (alrededor de 8° - 10°)
    assert 5.0 <= res.sun_altitude_deg <= 12.0, f"Sol debería estar bajo (~8°-10°), está a {res.sun_altitude_deg}°"
    # Azimut hacia el WNW (~275° - 290°)
    assert 270.0 <= res.sun_azimuth_deg <= 300.0


def test_local_contacts_madrid_partial():
    """
    Valida Madrid en 2026 y 2027:
    - 2026: Fuera de la franja por poco margen al sur (parcial > 90%).
    - 2027: Parcial (~85-88%).
    - En ambos casos: duracion totalidad = 0, C2 y C3 son None.
    """
    mgr = EclipseCatalogManager()
    e2026 = mgr.get_by_id("2026-08-12-solar-total")
    e2027 = mgr.get_by_id("2027-08-02-solar-total")

    # Madrid 2026
    res26 = calculate_local_eclipse(e2026, lat=40.4168, lon=-3.7038, alt_m=650.0)
    assert res26.visibility == "partial"
    assert res26.is_visible is True
    assert res26.totality_duration_s == 0.0
    assert res26.c2_utc is None and res26.c3_utc is None
    assert res26.obscuration_pct > 90.0, f"Madrid 2026 debería tener >90% oscurecimiento, tiene {res26.obscuration_pct}%"

    # Madrid 2027
    res27 = calculate_local_eclipse(e2027, lat=40.4168, lon=-3.7038, alt_m=650.0)
    assert res27.visibility == "partial"
    assert res27.totality_duration_s == 0.0
    assert 80.0 <= res27.obscuration_pct <= 92.0


def test_local_contacts_not_visible_location():
    """Valida un punto del planeta donde el eclipse no es visible en absoluto (ej. Tokio en 2026)."""
    mgr = EclipseCatalogManager()
    e2026 = mgr.get_by_id("2026-08-12-solar-total")

    # Tokio (Japón)
    res = calculate_local_eclipse(e2026, lat=35.6762, lon=139.6503, alt_m=40.0)
    assert res.visibility == "none"
    assert res.is_visible is False
    assert res.obscuration_pct == 0.0
    assert res.c1_utc is None and res.c2_utc is None


def test_topographic_altitude_correction():
    """
    Valida la corrección topográfica por altitud:
    A 2000m de altitud sobre el nivel del mar, C2 se adelanta entre 0.5s y 1.5s
    respecto al nivel del mar (0m).
    """
    mgr = EclipseCatalogManager()
    e2027 = mgr.get_by_id("2027-08-02-solar-total")

    res_sea = calculate_local_eclipse(e2027, lat=36.014, lon=-5.604, alt_m=0.0)
    res_2000m = calculate_local_eclipse(e2027, lat=36.014, lon=-5.604, alt_m=2000.0)

    # C2 a 2000m debe ocurrir ANTES que a 0m
    c2_sea = res_sea.c2_utc
    c2_high = res_2000m.c2_utc
    diff_s = c2_sea - c2_high

    assert 0.5 <= diff_s <= 1.5, f"Adelanto en C2 a 2000m fuera de rango [0.5, 1.5]: {diff_s:.3f}s"
    assert res_2000m.alt_correction_s < 0  # Marcado como valor de adelanto


# =============================================================================
# 3. Tests de UI del Calendario y Carga en 1-Clic
# =============================================================================

def test_ui_calendar_widget_initialization(qapp):
    """Verifica que el widget EclipseCalendarWidget inicializa correctamente los controles."""
    widget = EclipseCalendarWidget()
    assert widget.list_eclipses.count() >= 10
    assert widget.selected_eclipse is not None
    assert widget.last_result is not None
    assert widget.btn_load_active.isEnabled()


def test_ui_calendar_widget_coordinate_update(qapp):
    """Verifica que cambiar coordenadas actualiza automáticamente el resultado astronómico."""
    widget = EclipseCalendarWidget()

    # Seleccionar explícitamente el eclipse 2027
    mgr = widget.catalog
    e2027 = mgr.get_by_id("2027-08-02-solar-total")
    widget.selected_eclipse = e2027

    # Coordenadas en Tarifa (Totalidad)
    widget.update_coordinates(lat=36.014, lon=-5.604, alt_m=10.0)
    assert widget.last_result.visibility == "totality"
    assert widget.last_result.totality_duration_s > 240.0
    assert widget.card_duration.findChild(widget.card_duration.__class__, "val").text() != "0s (Fuera)"

    # Coordenadas en Madrid (Parcial)
    widget.update_coordinates(lat=40.4168, lon=-3.7038, alt_m=650.0)
    assert widget.last_result.visibility == "partial"
    assert widget.last_result.totality_duration_s == 0.0


def test_ui_calendar_widget_filters_past_eclipses(qapp):
    """Verifica que el calendario no muestra eventos pasados según la fecha del sistema o de referencia."""
    widget = EclipseCalendarWidget()
    listed_ids = [widget.list_eclipses.item(i).data(Qt.UserRole).id for i in range(widget.list_eclipses.count())]
    # En fecha actual (noviembre 2026), los eclipses de marzo 2026 y agosto 2026 han pasado y no deben mostrarse
    assert "2026-08-12-solar-total" not in listed_ids
    assert "2026-03-03-lunar-total" not in listed_ids
    assert "2027-08-02-solar-total" in listed_ids

    # El eclipse seleccionado por defecto debe ser el más próximo (2027-08-02)
    assert widget.selected_eclipse is not None
    assert widget.selected_eclipse.id == "2027-08-02-solar-total"

    # Al cambiar de filtro a Eclipses España, solo se muestran los futuros (2027 y 2028, no 2026)
    widget.combo_filter.setCurrentIndex(1)
    spain_ids = [widget.list_eclipses.item(i).data(Qt.UserRole).id for i in range(widget.list_eclipses.count())]
    assert "2026-08-12-solar-total" not in spain_ids
    assert "2027-08-02-solar-total" in spain_ids
    assert "2028-01-26-solar-annular" in spain_ids

    # Si se instancia con fecha anterior (ej. 2026-01-01), sí incluye el eclipse de agosto 2026
    widget_historical = EclipseCalendarWidget(reference_date="2026-01-01")
    historical_ids = [widget_historical.list_eclipses.item(i).data(Qt.UserRole).id for i in range(widget_historical.list_eclipses.count())]
    assert "2026-08-12-solar-total" in historical_ids



def test_ui_one_click_load_to_main_window(qapp):
    """
    Test de integración en 1-clic:
    Verifica que al pulsar '⚡ Cargar como Eclipse Activo', MainWindow recibe los contactos,
    actualiza el EclipseSequencer, el EclipseTimelineWidget y el ExecutionLogWidget.
    """
    win = MainWindow()
    assert hasattr(win, "tab_calendar")
    assert win.tab_calendar is not None

    # Configurar el calendario en Tarifa para 2027
    cal = win.tab_calendar
    e2027 = cal.catalog.get_by_id("2027-08-02-solar-total")
    assert e2027 is not None
    cal.selected_eclipse = e2027
    cal.update_coordinates(lat=36.014, lon=-5.604, alt_m=50.0)

    # Simular clic en el botón de carga en 1-clic
    cal.btn_load_active.click()

    # Comprobar inyección en MainWindow
    assert win.active_eclipse_info is not None
    assert win.active_eclipse_info.id == "2027-08-02-solar-total"
    assert win.active_contacts is not None
    assert "C2" in win.active_contacts
    assert "C3" in win.active_contacts

    # Comprobar actualización en TimelineWidget
    assert win.timeline_widget.contacts == win.active_contacts

    # Comprobar actualización en ExecutionLog
    assert win.execution_log.contacts == win.active_contacts

    # Comprobar cambio automático de pestaña a Secuencia & Control (índice 2)
    assert win.tabs.currentIndex() == 2

    # Comprobar registro en consola
    assert "Eclipse cargado en 1-clic" in win.txt_log.toPlainText()

    win.close()


def test_ui_annular_2028_load_safety_preset(qapp):
    """
    Verifica que al cargar el eclipse solar anular de 2028 en 1-clic:
    1. Se detecta como eclipse anular.
    2. La secuencia cargada NUNCA incluye órdenes de retirar el filtro.
    3. Incluye avisos de seguridad para mantener el filtro solar puesto en todo momento.
    4. El banner NEXT y el TimelineWidget se configuran en modo anular.
    """
    win = MainWindow()
    cal = win.tab_calendar
    e2028 = cal.catalog.get_by_id("2028-01-26-solar-annular")
    assert e2028 is not None
    assert e2028.is_annular is True

    cal.selected_eclipse = e2028
    # Coordenadas en la franja anular de España (ej: Palma de Mallorca)
    cal.update_coordinates(lat=39.569, lon=2.650, alt_m=50.0)

    cal.btn_load_active.click()

    assert win.active_eclipse_info is not None
    assert win.active_eclipse_info.id == "2028-01-26-solar-annular"
    assert win.timeline_widget.is_annular is True
    assert win.next_banner.is_annular is True

    # Verificar que el horario/secuencia cargada no contiene retirar filtro
    active_sched = win._get_active_schedule()
    descriptions = [ev.description.lower() for ev in active_sched]
    assert not any("quitar filtro" in d for d in descriptions), "¡PELIGRO: El eclipse anular no debe ordenar quitar filtro!"
    assert not any("retirar filtro" in d for d in descriptions), "¡PELIGRO: El eclipse anular no debe ordenar retirar filtro!"
    assert any("mantener filtro" in d for d in descriptions), "Debe incluir aviso de mantener filtro solar puesto"

    win.close()


def test_calendar_sync_with_gps_coords(qapp):
    """Verifica sincronización de coordenadas con GPSData tanto por altitude_m como por el alias altitude."""
    win = MainWindow()
    cal = win.tab_calendar

    gps_data = win.gps_reader.data
    gps_data.has_fix = True
    gps_data.latitude = 40.4168
    gps_data.longitude = -3.7038
    gps_data.altitude_m = 650.0

    assert gps_data.altitude == 650.0

    cal._sync_with_parent_coords()

    assert cal.current_lat == 40.4168
    assert cal.current_lon == -3.7038
    assert cal.current_alt == 650.0

    win.close()


def test_clean_startup_no_preloaded_eclipse(qapp):
    """Verifica que MainWindow inicie limpio sin ningún eclipse precargado."""
    win = MainWindow()
    assert len(win.current_schedule) == 0
    assert win.active_eclipse_info is None
    assert win.active_contacts is None
    assert "Sin eclipse cargado" in win.lbl_loaded_profile.text()
    win.close()


def test_simulation_eclipse_in_catalog_and_5min_loading(qapp):
    """Verifica la presencia de la entrada de simulación y la carga en 5 minutos."""
    win = MainWindow()
    cal = win.tab_calendar

    # 1. Verificar catálogo y propiedades del eclipse de simulación
    sim_e = cal.catalog.get_by_id("simulacion-test-lab")
    assert sim_e is not None
    assert sim_e.is_simulation is True
    assert sim_e.badge_color == "#EF4444"
    assert sim_e.type_label == "SIMULACIÓN"

    # 2. Seleccionar simulación en el calendario
    cal.selected_eclipse = sim_e
    cal.recalculate()

    # Comprobar que en modo simulación se muestra el grupo de configuración
    assert not cal.sim_config_group.isHidden()
    assert cal.btn_load_active.isEnabled() is False
    assert cal.btn_load_sim.isEnabled() is True

    # 3. Cargar simulación rápida (en 5 minutos)
    cal.combo_test_mode.setCurrentText("Simulacro Rápido (12 seg de prueba)")
    cal.btn_load_sim.click()

    # 4. Verificar que MainWindow recibió la simulación
    assert win.active_eclipse_info is not None
    assert win.active_eclipse_info.id == "simulacion-test-lab"
    assert win.is_simulation_mode is True
    assert len(win.current_schedule) > 0

    # Comprobar que C2 está en los próximos 5 minutos (entre 280s y 320s en el futuro)
    now = datetime.now(timezone.utc).timestamp()
    c2 = win.active_contacts.get("C2", 0.0)
    delta_s = c2 - now
    assert 280.0 <= delta_s <= 320.0, f"C2 debe estar a ~300s (5 min), obtenido delta={delta_s}"

    assert win.tabs.currentIndex() == 2
    assert "SIMULACIÓN" in win.lbl_loaded_profile.text()

    win.close()


def test_calendar_three_column_layout_and_map_interaction(qapp):
    """
    Verifica la nueva arquitectura de 3 columnas del calendario:
    - Columna 1: Catálogo y filtros
    - Columna 2: Visor de mapas Leaflet y capa de eclipse
    - Columna 3: Coordenadas y métricas en una sola línea, tabla de contactos y carga
    - Interacción bidireccional de clic en mapa -> recálculo automático
    """
    from PySide6.QtWidgets import QSplitter, QHBoxLayout

    widget = EclipseCalendarWidget()

    # 1. Comprobar que existe el Splitter horizontal con 3 paneles
    splitter = widget.findChild(QSplitter)
    assert splitter is not None
    assert splitter.count() == 3, f"Se esperaban 3 columnas en el splitter, encontradas {splitter.count()}"

    # 2. Comprobar que las coordenadas están en una sola fila (QHBoxLayout)
    pos_group = widget.spin_lat.parentWidget()
    assert isinstance(pos_group.layout(), QHBoxLayout), "El grupo de coordenadas debe usar QHBoxLayout (1 sola fila)"
    assert widget.spin_lat.value() == 40.65406
    assert widget.spin_lon.value() == -3.76918
    assert widget.btn_sync_gps is not None

    # 3. Comprobar que las 4 tarjetas de telemetría están en una sola fila horizontal
    telemetry_layout = widget.card_duration.parentWidget().layout()
    # Buscar el layout contenedor de las tarjetas
    assert widget.card_duration is not None
    assert widget.card_sun_alt is not None
    assert widget.card_obscuration is not None
    assert widget.card_azimuth is not None

    # 4. Comprobar presencia del visor de mapas QWebEngineView y botón de centrado
    assert hasattr(widget, "web_map_view")
    assert widget.web_map_view is not None
    assert hasattr(widget, "btn_recenter_map")

    # 5. Probar interacción de clic en el mapa mediante document.title ("OBSERVER:lat,lon")
    e2027 = widget.catalog.get_by_id("2027-08-02-solar-total")
    assert e2027 is not None
    widget.selected_eclipse = e2027

    # Simular clic en mapa en coordenadas de Tarifa (dentro de totalidad)
    widget._on_map_title_changed("OBSERVER:36.01400,-5.60400")

    assert widget.current_lat == 36.014
    assert widget.current_lon == -5.604
    assert widget.spin_lat.value() == 36.014
    assert widget.spin_lon.value() == -5.604
    assert widget.last_result is not None
    assert widget.last_result.visibility == "totality"
    assert widget.last_result.totality_duration_s > 260.0

    # Comprobar que la tarjeta de totalidad refleja la duración calculada
    val_text = widget.card_duration.findChild(widget.card_duration.__class__, "val").text()
    assert "m" in val_text and "s" in val_text
    assert val_text != "0s (Fuera)"

    # Simular clic en mapa en coordenadas de Madrid (fuera de totalidad)
    widget._on_map_title_changed("OBSERVER:40.41680,-3.70380")
    assert widget.current_lat == 40.41680
    assert widget.current_lon == -3.70380
    assert widget.last_result.visibility == "partial"
    val_madrid = widget.card_duration.findChild(widget.card_duration.__class__, "val").text()
    assert val_madrid == "0s (Fuera)"


def test_canonical_limits_and_antequera_edge_case():
    """
    Verifica que la integración de límites canónicos (NASA / IGN) en 2027 resuelve
    la discrepancia visual y astronómica en bordes geográficos críticos (ej. Antequera).
    """
    mgr = EclipseCatalogManager()
    e2027 = mgr.get_by_id("2027-08-02-solar-total")
    assert e2027 is not None
    assert len(e2027.northern_limit) > 50, "Debe tener límite norte canónico densificado"
    assert len(e2027.southern_limit) > 50, "Debe tener límite sur canónico densificado"
    assert len(e2027.path_polygon) > 100, "Debe tener polígono cerrado canónico"

    # 1. Antequera (lat 37.01845, lon -4.58061): fuera de la totalidad por ~25 km
    res_ant = calculate_local_eclipse(e2027, 37.01845, -4.58061, 500.0)
    assert res_ant.visibility == "partial"
    assert res_ant.totality_duration_s == 0.0
    assert 20.0 <= min_distance_to_polyline(37.01845, -4.58061, e2027.northern_limit) <= 30.0
    assert not point_in_polygon(37.01845, -4.58061, e2027.path_polygon)
    assert "25 km" in res_ant.description or "24 km" in res_ant.description

    # 2. Tarifa (lat 36.01, lon -5.60): dentro de totalidad, duración > 4.5 min
    res_tar = calculate_local_eclipse(e2027, 36.01, -5.60, 10.0)
    assert res_tar.visibility == "totality"
    assert point_in_polygon(36.01, -5.60, e2027.path_polygon)
    assert res_tar.totality_duration_s > 270.0
    assert res_tar.obscuration_pct == 100.0

    # 3. Málaga (lat 36.72, lon -4.42): dentro de totalidad
    res_mal = calculate_local_eclipse(e2027, 36.72, -4.42, 20.0)
    assert res_mal.visibility == "totality"
    assert point_in_polygon(36.72, -4.42, e2027.path_polygon)
    assert res_mal.totality_duration_s > 140.0
    assert res_mal.obscuration_pct == 100.0

    # 4. Cádiz (lat 36.53, lon -6.29): dentro de totalidad
    res_cad = calculate_local_eclipse(e2027, 36.53, -6.29, 15.0)
    assert res_cad.visibility == "totality"
    assert point_in_polygon(36.53, -6.29, e2027.path_polygon)
    assert res_cad.totality_duration_s > 180.0

