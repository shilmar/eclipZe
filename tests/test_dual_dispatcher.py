"""
Tests unitarios para el Núcleo Multi-Cámara y Árbitro de Prioridad (Fase 1 eclipZe v2.0).
Verifica resolución de colisiones temporales (|ΔT| < 25 ms), micro-escalonamiento (+30 ms),
conmutación de rol Master, y telemetría de EquipmentManager con cámaras duales simuladas.
"""

import os
import sys
import time

# Asegurar que el directorio raíz del proyecto está en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.camera import MockCameraDriver
from core.dispatcher import PriorityArbiter, MultiCameraDispatcher
from core.equipment import EquipmentManager, CameraSlot, DiscoveredCamera


def test_priority_arbiter_tie_resolution_master_a():
    """Verifica que con Master=A, un empate (|ΔT| < 25ms) dispare A en T_0 y B a +30ms."""
    arbiter = PriorityArbiter(master_slot="A", tie_threshold_ms=25.0, stagger_delay_ms=30.0)
    assert arbiter.is_master("A") is True
    assert arbiter.is_master("B") is False

    t_base = 1000.0
    # Empate con diferencia de 10 ms (< 25 ms)
    t_a = t_base
    t_b = t_base + 0.010

    eff_a, eff_b, collision = arbiter.resolve_collision(t_a, t_b)
    assert collision is True, "Debe detectar colisión de empate temporal"
    assert eff_a == t_a, "Cámara Master A debe disparar exactamente en su T_0 programado"
    # Cámara B debe ser escalonada al menos +30ms sobre el tiempo programado
    assert eff_b >= t_b + 0.029, f"Cámara Slave B debe sufrir micro-escalonamiento (+30ms). Obtenido: {eff_b}"
    assert round(eff_b - eff_a, 4) >= 0.030, "El desfase mínimo entre tomas debe ser de 30 ms"


def test_priority_arbiter_tie_resolution_master_b():
    """Verifica que al conmutar Master=B, B dispara en T_0 y A sufre el micro-escalonamiento (+30ms)."""
    arbiter = PriorityArbiter(master_slot="B", tie_threshold_ms=25.0, stagger_delay_ms=30.0)
    assert arbiter.is_master("B") is True
    assert arbiter.is_master("A") is False

    t_base = 2000.0
    # Disparos programados en el mismo milisegundo exacto
    t_a = t_base
    t_b = t_base

    eff_a, eff_b, collision = arbiter.resolve_collision(t_a, t_b)
    assert collision is True, "Debe detectar colisión en tiempo simultáneo"
    assert eff_b == t_b, "Cámara Master B debe disparar en T_0"
    assert eff_a >= t_a + 0.029, "Cámara Slave A debe ser micro-escalonada (+30ms)"
    assert eff_a - eff_b >= 0.0299, "El desfase debe favorecer a B"


def test_priority_arbiter_no_collision():
    """Verifica que diferencias >= 25ms no sufran modificaciones de horario."""
    arbiter = PriorityArbiter(master_slot="A", tie_threshold_ms=25.0, stagger_delay_ms=30.0)
    t_a = 500.000
    t_b = 500.035  # 35 ms de diferencia (> 25 ms)

    eff_a, eff_b, collision = arbiter.resolve_collision(t_a, t_b)
    assert collision is False, "No debe registrar colisión con |ΔT| >= 25ms"
    assert eff_a == t_a
    assert eff_b == t_b


def test_dual_mock_dispatcher_execution():
    """Verifica la orquestación real con dos instancias de MockCameraDriver."""
    cam_a = MockCameraDriver(camera_name="Mock Nikon Z5 II (Telescopio)", is_dslr=False)
    cam_b = MockCameraDriver(camera_name="Mock Nikon D750 (Gran Angular)", is_dslr=True)

    dispatcher = MultiCameraDispatcher(
        driver_a=cam_a,
        driver_b=cam_b,
        master_slot="A",
        tie_threshold_ms=25.0,
        stagger_delay_ms=30.0
    )

    res = dispatcher.connect_all()
    assert res["A"] is True and res["B"] is True, "Ambas cámaras deben conectarse"

    # Disparo dual simultáneo con Master = A
    report = dispatcher.trigger_dual_simultaneous(
        shutter_a="1/4000", iso_a="100",
        shutter_b="1/1000", iso_b="200"
    )

    assert report["master_success"] is True, "Disparo Master A debe ser exitoso"
    assert report["slave_success"] is True, "Disparo Slave B debe ser exitoso"
    assert report["master_slot"] == "A"
    assert report["slave_slot"] == "B"

    # Verificar historial de disparos y desfase
    assert len(cam_a.shot_history) == 1
    assert len(cam_b.shot_history) == 1
    shot_a_ts = cam_a.shot_history[0]["timestamp"]
    shot_b_ts = cam_b.shot_history[0]["timestamp"]

    # B debe haberse ejecutado después de A con al menos 28 ms de diferencia (tolerancia de timer)
    delta_s = shot_b_ts - shot_a_ts
    assert delta_s >= 0.028, f"Micro-escalonamiento debe ser >= 28ms. Obtenido: {delta_s*1000:.2f} ms"

    # Ahora conmutar a Master = B y volver a disparar
    dispatcher.set_master_slot("B")
    report_2 = dispatcher.trigger_dual_simultaneous(
        shutter_a="1/2000", iso_a="100",
        shutter_b="1/500", iso_b="400"
    )

    assert report_2["master_slot"] == "B"
    assert report_2["slave_slot"] == "A"
    assert len(cam_a.shot_history) == 2
    assert len(cam_b.shot_history) == 2

    shot_a_ts2 = cam_a.shot_history[1]["timestamp"]
    shot_b_ts2 = cam_b.shot_history[1]["timestamp"]
    delta_s2 = shot_a_ts2 - shot_b_ts2
    assert delta_s2 >= 0.028, f"Micro-escalonamiento debe favorecer a B sobre A. Obtenido: {delta_s2*1000:.2f} ms"

    dispatcher.disconnect_all()
    assert cam_a.connected is False
    assert cam_b.connected is False


def test_equipment_manager_slots_and_telemetry():
    """Verifica que EquipmentManager gestione las ranuras A y B, telemetría y prioridad."""
    em = EquipmentManager()

    # Verificar estado por defecto
    assert em.slot_a.slot_id == "A"
    assert em.slot_b.slot_id == "B"
    assert em.slot_a.is_priority_master is True
    assert em.slot_b.is_priority_master is False
    assert em.slot_a.status == "Conectada"
    assert em.slot_b.status == "Conectada"
    assert em.slot_a.battery_level > 0
    assert em.slot_b.battery_level > 0

    # Disparo de prueba individual en Ranura A
    ok_a = em.test_shot("A")
    assert ok_a is True, "Disparo de prueba A debe ser exitoso"

    # Disparo de prueba individual en Ranura B
    ok_b = em.test_shot("B")
    assert ok_b is True, "Disparo de prueba B debe ser exitoso"

    # Conmutar prioridad global
    em.set_priority_master("B")
    assert em.slot_a.is_priority_master is False
    assert em.slot_b.is_priority_master is True
    assert em.dispatcher.arbiter.master_slot == "B"

    # Liberar controles
    em.release_camera_controls()
    assert em.slot_a.status == "Liberada (Manual)"
    assert em.slot_b.status == "Liberada (Manual)"
    assert not em.slot_a.driver.connected
    assert not em.slot_b.driver.connected

    # Reconectar controles
    em.reconnect_camera_controls()
    assert em.slot_a.status == "Conectada"
    assert em.slot_b.status == "Conectada"
    assert em.slot_a.driver.connected
    assert em.slot_b.driver.connected


def test_ui_equipment_tab():
    """Verifica que la pestaña de Equipamiento en PySide6 funcione e interactúe con el dispatcher."""
    import os
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from PySide6.QtWidgets import QApplication
    from ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert hasattr(window, "tab_equipment"), "Debe tener la pestaña de equipamiento"
    assert window.tabs.tabText(0) == "📷 Gestión de Equipamiento"
    assert window.tabs.count() >= 3

    # Probar conmutador global de prioridad Master
    window.combo_master_priority.setCurrentIndex(1)  # Ranura B
    assert window.equipment_manager.slot_b.is_priority_master is True
    assert "MASTER" in window.lbl_badge_b.text()
    assert "SLAVE" in window.lbl_badge_a.text()

    window.combo_master_priority.setCurrentIndex(0)  # Ranura A
    assert window.equipment_manager.slot_a.is_priority_master is True
    assert "MASTER" in window.lbl_badge_a.text()
    assert "SLAVE" in window.lbl_badge_b.text()

    # Probar disparos individuales
    window._on_test_shot_a()
    assert len(window.equipment_manager.slot_a.driver.shot_history) >= 1

    window._on_test_shot_b()
    assert len(window.equipment_manager.slot_b.driver.shot_history) >= 1

    # Probar disparo dual simulado desde la UI
    window._on_test_dual_shot()
    assert "✔ Disparo Dual: Master (A)" in window.lbl_dual_result.text()

    # Probar liberación individual de controles
    window._on_release_a()
    assert not window.equipment_manager.slot_a.driver.connected
    window._on_release_a()
    assert window.equipment_manager.slot_a.driver.connected

    window.ui_timer.stop()
    window.close()
    del window
    app.processEvents()
    app.quit()
    del app


if __name__ == "__main__":
    print("Ejecutando tests de Dispatcher Multi-Cámara y Priority Arbiter...")
    test_priority_arbiter_tie_resolution_master_a()
    print("  [OK] Priority Arbiter: Empate con Master A (+30ms a B)")
    test_priority_arbiter_tie_resolution_master_b()
    print("  [OK] Priority Arbiter: Empate con Master B (+30ms a A)")
    test_priority_arbiter_no_collision()
    print("  [OK] Priority Arbiter: Sin colisión (|Delta_T| >= 25ms)")
    test_dual_mock_dispatcher_execution()
    print("  [OK] MultiCameraDispatcher: Disparo dual y micro-staggering simulado")
    test_equipment_manager_slots_and_telemetry()
    print("  [OK] EquipmentManager: Ranuras A y B, telemetría y liberación")
    test_ui_equipment_tab()
    print("  [OK] UI PySide6: Pestaña Equipamiento, conmutador Master y disparos duales")
    print("\nTodos los tests multi-cámara pasaron exitosamente.")
