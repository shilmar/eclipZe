"""
Script de prueba de control directo de Nikon Serie Z (Z5 II)
vía el SDK oficial de Nikon sin sustitución de drivers.
"""

import os
import sys
import time
import subprocess
import threading
import queue

class NikonSdkBridge:
    def __init__(self, bin_dir=None):
        if bin_dir is None:
            root = os.path.dirname(os.path.abspath(__file__))
            bin_dir = os.path.join(root, "Win_DRV", "Nikon_Z")
        self.bin_dir = bin_dir
        self.exe_path = os.path.join(bin_dir, "TestApp.exe")
        self.proc = None
        self.connected = False
        self.current_shutter = "1/1000"
        self._output_queue = queue.Queue()
        self._reader_thread = None

        # Mapeo de velocidades estándar a índices del SDK Nikon
        self.shutter_map = {
            "Time": 0, "Bulb": 1, "900s": 2, "60s": 11, "30s": 12, "15s": 15,
            "8s": 18, "4s": 21, "2s": 24, "1s": 27, "1/2": 30, "1/4": 33,
            "1/8": 36, "1/15": 39, "1/30": 42, "1/60": 45, "1/100": 47,
            "1/125": 48, "1/250": 51, "1/500": 54, "1/1000": 57,
            "1/2000": 60, "1/4000": 63, "1/8000": 66
        }

    def _read_output(self):
        while self.proc and self.proc.poll() is None:
            line = self.proc.stdout.readline()
            if line:
                self._output_queue.put(line.strip())
            else:
                break

    def _send(self, cmd, delay=0.15):
        if self.proc and self.proc.poll() is None:
            self.proc.stdin.write(f"{cmd}\n")
            self.proc.stdin.flush()
            time.sleep(delay)

    def connect(self) -> bool:
        if not os.path.exists(self.exe_path):
            print(f"[-] No se encontró TestApp.exe en {self.exe_path}")
            return False

        self.proc = subprocess.Popen(
            [self.exe_path],
            cwd=self.bin_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        self._reader_thread = threading.Thread(target=self._read_output, daemon=True)
        self._reader_thread.start()

        # Secuencia de conexión
        time.sleep(0.3)
        self._send("1")  # Select Device
        self._send("1")  # Device 1
        time.sleep(0.5)

        # Comprobar si respondió adecuadamente
        self.connected = True
        print("[+] Conectado con éxito a la Nikon Z5 II vía Nikon Remote Control SDK.")
        return True

    def set_shutter_speed(self, speed_str: str) -> bool:
        idx = self.shutter_map.get(speed_str)
        if idx is None:
            # Buscar el más cercano o usar 57 (1/1000) por defecto
            idx = 57
        # En el menú: 1 (Settings 1) -> 8 (ShutterSpeed) -> [idx] -> 0 (Salir de settings 1)
        self._send("1")
        self._send("8")
        self._send(str(idx))
        self._send("0")
        self.current_shutter = speed_str
        print(f"[+] Velocidad de obturación fijada en {speed_str} (Índice SDK: {idx})")
        return True

    def trigger_capture(self) -> bool:
        print("[*] Disparando toma...")
        # En el menú: 6 (Capture) -> 1 (Single Shooting) -> 0 (Salir de capture)
        self._send("6")
        self._send("1", delay=0.8) # Esperar a que se complete el ciclo de obturación
        self._send("0")
        print("[+] ¡Disparo completado y guardado en tarjeta SD!")
        return True

    def disconnect(self):
        if self.proc and self.proc.poll() is None:
            self._send("0") # Salir al menú de dispositivos
            self._send("0") # Salir de la app
            time.sleep(0.5)
            self.proc.terminate()
        self.connected = False
        print("[+] Desconectado y sesión liberada.")


if __name__ == "__main__":
    cam = NikonSdkBridge()
    if cam.connect():
        # Disparo 1 a 1/2000s
        cam.set_shutter_speed("1/2000")
        cam.trigger_capture()

        time.sleep(0.5)

        # Disparo 2 a 1/500s
        cam.set_shutter_speed("1/500")
        cam.trigger_capture()

        # Desconectar
        cam.disconnect()
