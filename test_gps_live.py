"""
Script de prueba y diagnóstico en vivo para receptor GPS USB (VK-162 / u-blox).
Muestra telemetría en tiempo real: Fix satelital, coordenadas, altitud y desfase horario con el PC.
"""

import time
from core.gps import GPSReader


def main():
    print("=" * 65)
    print("eclipZe — Diagnóstico en vivo de GPS USB (u-blox VK-162)")
    print("=" * 65)

    reader = GPSReader(port="COM3", baudrate=9600)
    reader.start()

    print("\nIniciando lectura en COM3 (9600 baud)...")
    try:
        for i in range(1, 6):
            time.sleep(1.0)
            d = reader.data
            estado = "FIX SATELITAL OK" if d.has_fix else ("BUSCANDO SATÉLITES" if d.connected else "DESCONECTADO")
            print(
                f"[{i}s] Estado: {estado:<20} | Satélites: {d.satellites:>2} | "
                f"Offset PC: {d.clock_offset_seconds:+.3f}s"
            )
            if d.has_fix:
                print(
                    f"     -> Coordenadas: {d.latitude:.5f}°, {d.longitude:.5f}° | "
                    f"Altitud: {d.altitude_m:.1f} m | UTC: {d.utc_time}"
                )
    except KeyboardInterrupt:
        pass
    finally:
        reader.stop()
        print("\nPrueba completada.")


if __name__ == "__main__":
    main()
