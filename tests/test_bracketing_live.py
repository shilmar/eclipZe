"""
Test interactivo de validación de horquillado (Bracketing) para eclipZe y Nikon Serie Z (U3).
Permite validar:
1. Horquillado por Software (Escalera de velocidades controlada por eclipZe).
2. Horquillado por Hardware (Ráfaga disparadora con BKT interno activo en U3).
3. Prueba del simulacro rápido de eclipse con la cámara física.
"""

import os
import sys
import time

# Asegurar que el directorio raíz está en el path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.camera import NikonSdkDriver, MockCameraDriver
from core.sequencer import EclipseSequencer
from core.presets import get_quick_rehearsal_preset


def test_software_bracketing(cam=None, steps=None):
    """
    Prueba 1: Horquillado controlado por Software.
    eclipZe cambia la velocidad dinámicamente entre toma y toma por USB.
    """
    if cam is None:
        cam = MockCameraDriver()
        cam.connect()
    if steps is None:
        steps = ["1/4000", "1/2000", "1/1000", "1/250", "1/60"]

    print("\n" + "=" * 60)
    print(" [PRUEBA 1] Horquillado por Software (Escalera de velocidades)")
    print("=" * 60)
    print(f"Secuencia a ejecutar: {' -> '.join(steps)}")
    
    t_start_total = time.time()
    for i, speed in enumerate(steps, 1):
        t0 = time.time()
        print(f"\n[{i}/{len(steps)}] Configurando velocidad: {speed}...")
        cam.set_shutter_speed(speed)
        t_set = time.time()
        
        print(f"[{i}/{len(steps)}] Disparando...")
        ok = cam.trigger_capture()
        t_shot = time.time()
        
        dt_cmd = (t_set - t0) * 1000
        dt_shot = (t_shot - t_set) * 1000
        status = "OK" if ok else "FALLO"
        print(f" -> Resultado: {status} | Cambio: {dt_cmd:.0f}ms | Disparo: {dt_shot:.0f}ms")
        
        # Pequeña pausa técnica de seguridad
        time.sleep(cam.overhead_safety)

    total_elapsed = time.time() - t_start_total
    print("-" * 60)
    print(f"Prueba 1 completada en {total_elapsed:.2f} segundos ({total_elapsed/len(steps):.2f} s/toma).")


def test_hardware_burst_bkt(cam=None, count=5):
    """
    Prueba 2: Ráfaga rápida para activar el Horquillado de Hardware de la cámara.
    Requiere que la cámara esté en U3 con el modo BKT activo en el cuerpo.
    """
    if cam is None:
        cam = MockCameraDriver()
        cam.connect()
    print("\n" + "=" * 60)
    print(" [PRUEBA 2] Ráfaga para Horquillado Hardware (BKT en U3)")
    print("=" * 60)
    print(f"Enviando ráfaga directa a tarjeta SD de {count} disparos (sin descarga USB)...")
    print("Verifica que en el visor de la cámara la velocidad cambie automáticamente.\n")

    def on_burst_shot(desc, iso):
        print(f"  ✔ [{desc}] Disparo enviado a la tarjeta SD.")

    old_cb = cam.on_shot_callback
    cam.on_shot_callback = on_burst_shot
    
    t0 = time.time()
    try:
        ok = cam.trigger_burst(count=count)
    finally:
        cam.on_shot_callback = old_cb
        
    t_elapsed = time.time() - t0
    
    print("-" * 60)
    if ok:
        print(f"✔ Ráfaga de {count} disparos enviada con éxito en {t_elapsed:.2f} segundos.")
    else:
        print(f"⚠ Ráfaga finalizada con incidencias en algún fotograma ({t_elapsed:.2f} s).")


def test_rehearsal_sequence(cam=None):
    """
    Prueba 3: Ejecución de un simulacro rápido de eclipse (12 s)
    Verifica que el secuenciador gobierne la cámara con precisión temporal.
    """
    if cam is None:
        cam = MockCameraDriver()
        cam.connect()
    print("\n" + "=" * 60)
    print(" [PRUEBA 3] Simulacro Rápido de Eclipse (12 segundos)")
    print("=" * 60)
    
    now = time.time()
    # Contacto simulado en 6 segundos en el futuro
    contacts = {"C2": now + 6.0, "C3": now + 12.0}
    schedule = get_quick_rehearsal_preset()
    
    seq = EclipseSequencer(contacts=contacts, schedule=schedule, camera=cam)
    
    def on_triggered(event, shutter, iso):
        print(f"  [DISPARO] {event.description:<35} | {shutter:>7} | ISO {iso}")

    def on_skipped(event, delay):
        print(f"  [SALTADO] {event.description:<35} (Desfase: {delay*1000:.0f}ms)")

    seq.on_event_triggered = on_triggered
    seq.on_event_skipped = on_skipped
    
    print("Iniciando timeline del simulacro...")
    seq.start()
    
    while seq.is_running:
        time.sleep(0.1)
        
    print("-" * 60)
    print("✔ Simulacro completado.")


def main():
    print("=" * 65)
    print("    eclipZe — BANCO DE PRUEBAS DE HORQUILLADO Y DISPARO")
    print("=" * 65)
    print("Selecciona el controlador a utilizar:")
    print(" 1. Nikon Z Real (Nikon SDK / TestApp - Requiere cámara conectada)")
    print(" 2. Simulación (Mock - Para verificar lógica sin cámara)")
    
    choice = input("\nElige una opción (1 o 2) [por defecto 1]: ").strip()
    if choice == "2":
        cam = MockCameraDriver("Nikon Z5 II (Simulada)")
        print("\n[+] Usando cámara simulada.")
    else:
        cam = NikonSdkDriver("Nikon Z5 II (SDK Real)")
        print("\n[+] Intentando conectar con Nikon Z física vía SDK...")

    if not cam.connect():
        print("\n[-] No se pudo conectar con la cámara física.")
        print("Comprueba que:")
        print(" - La cámara esté encendida y conectada con cable USB.")
        print(" - El dial de la cámara esté en U3 o M.")
        retry_mock = input("\n¿Deseas ejecutar las pruebas con la cámara simulada? (s/n): ").strip().lower()
        if retry_mock == "s":
            cam = MockCameraDriver("Nikon Z5 II (Simulada)")
            cam.connect()
        else:
            return

    try:
        while True:
            print("\n" + "-" * 40)
            print("MENÚ DE PRUEBAS DE HORQUILLADO:")
            print(" 1. Probar Horquillado por Software (Escalera de 5 tomas)")
            print(" 2. Probar Ráfaga para Horquillado Hardware (BKT de cámara en U3)")
            print(" 3. Probar Simulacro de Eclipse (12 segundos)")
            print(" 4. Ejecutar todas las pruebas")
            print(" 0. Salir")
            print("-" * 40)
            
            sub = input("Selecciona prueba: ").strip()
            if sub == "1":
                test_software_bracketing(cam)
            elif sub == "2":
                n = input("Número de fotos de la ráfaga BKT [defecto 5]: ").strip()
                count = int(n) if n.isdigit() else 5
                test_hardware_burst_bkt(cam, count=count)
            elif sub == "3":
                test_rehearsal_sequence(cam)
            elif sub == "4":
                test_software_bracketing(cam)
                time.sleep(1.0)
                test_hardware_burst_bkt(cam, 5)
                time.sleep(1.0)
                test_rehearsal_sequence(cam)
            elif sub == "0":
                break
            else:
                print("Opción no válida.")
    finally:
        cam.disconnect()
        print("\n[+] Desconectado. Sesión finalizada de forma segura.")


if __name__ == "__main__":
    main()
