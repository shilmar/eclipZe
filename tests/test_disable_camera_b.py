"""
Test de verificación para la opción de habilitar / deshabilitar Cámara B (Ranura B) en eclipZe v2.0.
Verifica:
1. EquipmentManager y MultiCameraDispatcher: aislamiento del driver B al deshabilitar.
2. EclipseSequencer: compilación y omisión limpia de eventos de Cámara B.
3. EclipseTimelineWidget: cambio de estado visual y eventos en pista B.
4. Integración MainWindow: comportamiento de toggle y tabla de eventos.
"""

import sys
import os
import time

sys.path.insert(0, r"D:\software\eclipZe")
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from core.equipment import EquipmentManager
from core.dispatcher import MultiCameraDispatcher
from core.camera import MockCameraDriver
from core.presets import get_quick_rehearsal_preset
from core.sequencer import EclipseSequencer
from ui.timeline_widget import EclipseTimelineWidget


def test_equipment_manager_slot_b_toggle():
    print("=== TEST 1: EquipmentManager slot B toggle ===")
    em = EquipmentManager()
    assert em.slot_b.enabled is True
    assert em.dispatcher.get_driver("B") is not None

    # Deshabilitar Slot B
    em.set_slot_enabled("B", False)
    assert em.slot_b.enabled is False
    assert em.dispatcher.get_driver("B") is None
    assert em.slot_b.status == "Deshabilitada"
    tel_b = em.get_telemetry("B")
    assert tel_b["enabled"] is False
    assert tel_b["status"] == "Deshabilitada"
    assert em.test_shot("B") is False

    # Reconectar controles no debe tocar B
    em.reconnect_camera_controls()
    assert em.slot_b.status == "Deshabilitada"
    assert em.dispatcher.get_driver("B") is None

    # Reactivar Slot B
    em.set_slot_enabled("B", True)
    assert em.slot_b.enabled is True
    assert em.dispatcher.get_driver("B") is not None
    assert em.slot_b.status == "Conectada"
    print("  -> EquipmentManager toggle OK")


def test_sequencer_with_slot_b_disabled():
    print("=== TEST 2: EclipseSequencer con Slot B deshabilitado ===")
    drv_a = MockCameraDriver("CamA")
    drv_a.connect()
    drv_b = MockCameraDriver("CamB")
    drv_b.connect()

    dispatcher = MultiCameraDispatcher(driver_a=drv_a, driver_b=drv_b)
    schedule = get_quick_rehearsal_preset()

    # Total de eventos en el preset
    b_count = sum(1 for ev in schedule if getattr(ev, "camera_slot", "A") == "B")
    a_count = sum(1 for ev in schedule if getattr(ev, "camera_slot", "A") == "A")
    assert b_count > 0
    assert a_count > 0

    now = time.time()
    contacts = {
        "C1": now - 30.0,
        "C2": now + 0.1,
        "MAX": now + 0.3,
        "C3": now + 0.5,
        "C4": now + 1.0,
    }

    # Deshabilitar B en dispatcher
    dispatcher.set_driver("B", None)

    seq = EclipseSequencer(contacts=contacts, schedule=schedule, camera=dispatcher)
    compiled = seq.compute_compiled_timeline()

    # Todos los eventos compilados deben ser únicamente de Slot A
    for _, ev in compiled:
        assert getattr(ev, "camera_slot", "A") != "B", "Un evento de Cámara B se compiló a pesar de estar deshabilitada"

    assert len(compiled) == a_count, f"Esperados {a_count} eventos de Cámara A, obtenidos {len(compiled)}"
    print(f"  -> Sequencer excluyó limpiamente los {b_count} eventos de B. Compilados: {len(compiled)} eventos de A.")


def test_timeline_widget():
    print("=== TEST 3: EclipseTimelineWidget con pista B deshabilitada ===")
    app = QApplication.instance() or QApplication(sys.argv)
    w = EclipseTimelineWidget()
    schedule = get_quick_rehearsal_preset()
    now = time.time()
    contacts = {"C1": now - 30.0, "C2": now + 10.0, "C3": now + 20.0, "C4": now + 50.0}

    w.set_contacts(contacts)
    w.set_events(schedule, contacts)
    assert len(w.events_b) > 0, "Debería haber eventos en pista B"

    # Deshabilitar pista B
    w.set_track_b_enabled(False)
    assert len(w.events_b) == 0, "Pista B debería estar vacía de eventos al desactivarse"
    assert w.show_track_b is False

    # Reactivar pista B
    w.set_track_b_enabled(True)
    assert len(w.events_b) > 0, "Pista B debería recuperar sus eventos al reactivarse"
    print("  -> TimelineWidget track B toggle OK")


def test_main_window_integration():
    print("=== TEST 4: Integración en MainWindow ===")
    app = QApplication.instance() or QApplication(sys.argv)
    from ui.main_window import MainWindow

    win = MainWindow()
    total_events = len(win.current_schedule)
    b_events = sum(1 for ev in win.current_schedule if getattr(ev, "camera_slot", "A") == "B")
    a_events = total_events - b_events

    assert win.group_slot_b.isChecked() is True
    assert win.table_events.rowCount() == total_events

    # Desmarcar el checkbox de Ranura B
    win.group_slot_b.setChecked(False)

    # Verificar que Slot B está deshabilitado
    assert win.equipment_manager.slot_b.enabled is False
    assert win.btn_test_dual.isEnabled() is False
    assert win.combo_master_priority.isEnabled() is False
    assert "Deshabilitada" in win.lbl_status_b.text()
    assert "Deshabilitada" in win.lbl_top_slot_b.text()
    assert win.table_events.rowCount() == a_events, f"Esperadas {a_events} filas en la tabla, obtenidas {win.table_events.rowCount()}"

    # Reactivar Ranura B
    win.group_slot_b.setChecked(True)
    assert win.equipment_manager.slot_b.enabled is True
    assert win.btn_test_dual.isEnabled() is True
    assert win.combo_master_priority.isEnabled() is True
    assert win.table_events.rowCount() == total_events
    print("  -> MainWindow integration toggle OK")


if __name__ == "__main__":
    test_equipment_manager_slot_b_toggle()
    test_sequencer_with_slot_b_disabled()
    test_timeline_widget()
    test_main_window_integration()
    print("\n[OK] TODOS LOS TESTS DE DESHABILITACION DE CAMARA B PASARON EXITOSAMENTE.")
