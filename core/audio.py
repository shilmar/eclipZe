"""
Sistema de avisos por voz y sonoros para eclipZe.
Avisos de seguridad críticos (retirar filtro, poner filtro, cuentas atrás).
Utiliza los sintetizadores nativos del sistema operativo sin librerías externas pesadas.
"""

import sys
import subprocess
import threading


class AudioNotifier:
    """Emite alertas audibles y de síntesis de voz en segundo plano sin bloquear el hilo principal."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._is_windows = sys.platform.startswith("win")

    def speak(self, text: str):
        """Sintetiza voz de forma asíncrona."""
        if not self.enabled:
            return
        threading.Thread(target=self._speak_worker, args=(text,), daemon=True).start()

    def _speak_worker(self, text: str):
        try:
            if self._is_windows:
                # SAPI5 nativo vía PowerShell en Windows (sin dependencias externas)
                cmd = f'(New-Object -ComObject SAPI.SpVoice).Speak("{text}")'
                subprocess.run(
                    ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", cmd],
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    timeout=5
                )
            else:
                # Linux nativo vía spd-say o espeak
                try:
                    subprocess.run(["spd-say", text], timeout=5)
                except FileNotFoundError:
                    subprocess.run(["espeak", text], timeout=5)
        except Exception as e:
            # shortcut: si el sintetizador de voz falla, se omite silenciosamente
            print(f"[Audio Warning] No se pudo reproducir aviso de voz: {e}")

    def beep(self):
        """Emite un pitido de advertencia corto."""
        if not self.enabled:
            return
        threading.Thread(target=self._beep_worker, daemon=True).start()

    def _beep_worker(self):
        try:
            if self._is_windows:
                import winsound
                winsound.Beep(1200, 200)
            else:
                print("\a", end="", flush=True)
        except Exception:
            pass
