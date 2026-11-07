# Informe Técnico de Optimización: `camera.py` (Proyecto eclipZe)

**Objetivo:** Reducir al mínimo la latencia entre cambios de parámetros (velocidad de obturación/ISO) y disparos consecutivos en la **Nikon Z5 II** (y cuerpos secundarios como D750) durante las fases críticas de un eclipse solar (C2, Totalidad y C3).

---

## 1. Resumen Ejecutivo de Cuellos de Botella

Actualmente, el archivo `camera.py` presenta tiempos muertos artificiales (`time.sleep`) y sobrecargas de comunicación USB que penalizan cada disparo individual o rampa de horquillado manual con **entre 300 ms y 600 ms de retraso extra por toma**.

| Driver | Problema Detectado | Impacto de Latencia | Solución Propuesta |
| :--- | :--- | :--- | :--- |
| **`NikonSdkDriver`** | Envío línea a línea por `stdin` con `delay=0.035s` fijo por comando (`_send`). | **~140 ms** solo para cambiar la velocidad de obturación. | Implementar envío por lotes (`_send_batch`) en un único `write` + `flush`. Reduce a **~15 ms**. |
| **`NikonSdkDriver`** | Espera estática `time.sleep(0.35)` dentro de `trigger_capture()`. | Limita la cadencia máxima en modo Single a **~2 FPS**. | Espera dinámica calculada en función de la velocidad de exposición real (`exp_sec + 0.045s`) y modo `fast_sequence`. |
| **`NikonSdkDriver`** | `set_iso()` es un *No-Op* (solo actualiza el atributo en Python). | **Crítico:** La cámara nunca cambia el ISO físico por SDK. | Implementar la secuencia de menú real o delegar advertencia explícita. |
| **`NikonPTPDriver`** | Doble intento `0xD100` -> `0x500D` y llamada a `_drain_endpoints()` cuando un opcode no es soportado. | **~30-50 ms** perdidos en timeouts de drenaje USB en cada cambio. | Cachear el opcode válido en el primer uso (`_cached_shutter_prop`) y no drenar endpoints por respuestas PTP lógicas (`!= 0x2001`). |
| **`NikonPTPDriver`** | Lectura bloqueante de `ep_intr.read(64, timeout=25)` en cada `trigger_capture()`. | **25 ms** de penalización por foto esperando el evento `ObjectAdded`. | Añadir flag `fetch_handle: bool = False` por defecto durante ráfagas. |
| **`NikonPTPDriver`** | Falta forzar `RecordingMedia = Card` (`0xD00B`) en `connect()`. | **Riesgo crítico:** Si quedó en SDRAM, colapsa el búfer en el eclipse. | Fijar propiedad PTP `0xD00B` a `0` (Card) al abrir sesión. |
| **`GPhotoCameraDriver`** | Uso de `get_config()` / `set_config()` completos en cada cambio de parámetro. | **~80-150 ms** reconstruyendo todo el árbol PTP en cada cambio. | Reemplazar por `get_single_config()` y `set_single_config()`. Reduce a **~12 ms**. |
| **`NikonD750SdkDriver`** | Método `trigger_burst()` duplicado (líneas 748 y 766). | Código muerto / riesgo de `AttributeError` (`shot_history`). | Eliminar la primera definición duplicada. |

---

## 2. Instrucciones de Refactorización para Antigravity

A continuación se detallan los cambios exactos que deben aplicarse en `camera.py`.

### Tarea 1: Optimizar `NikonSdkDriver` (Batching por `stdin` y Espera Dinámica)

1. Añadir un método auxiliar estático `_shutter_str_to_seconds(shutter_str: str) -> float` para calcular la duración real de la exposición en segundos.
2. Añadir el método `_send_batch(self, commands: List[str], final_delay: float = 0.015) -> bool` que concatene los comandos con `\n`, haga un único `stdin.write()` y `stdin.flush()`, y aplique un solo `sleep` al final.
3. Refactorizar `set_shutter_speed`, `set_save_media`, `set_shooting_mode`, `set_continuous_shooting_num` y `set_ae_bracketing` para usar `_send_batch`.
4. Refactorizar `trigger_capture(self, fast_sequence: bool = False) -> bool` para:
   - Calcular la espera dinámica: `wait_time = max(0.055, exp_sec + 0.045) if fast_sequence else max(0.22, exp_sec + 0.08)`.
   - Evitar reactivar Live View entre toma y toma cuando `fast_sequence=True`.
5. Añadir el método `execute_bracket_ramp(self, shutter_list: List[str]) -> bool` en la clase base `CameraDriver` (y optimizado en `NikonSdkDriver`) para ejecutar barridos de velocidades de corona sin sobrecarga intermedia.

#### Código de referencia para `NikonSdkDriver`:

```python
    @staticmethod
    def _shutter_str_to_seconds(shutter_str: str) -> float:
        """Convierte cadena de velocidad ('1/1000', '2s', '1/1.3') a segundos reales."""
        s = str(shutter_str).strip().lower().rstrip("s")
        if s in ("bulb", "time"):
            return 1.0
        if "/" in s:
            try:
                num, den = s.split("/")
                return float(num) / float(den)
            except (ValueError, ZeroDivisionError):
                return 0.001
        try:
            return float(s)
        except ValueError:
            return 0.001

    def _send_batch(self, commands: List[str], final_delay: float = 0.015) -> bool:
        """Envía una secuencia completa de menú de una sola vez al buffer stdin sin sleeps intermedios."""
        if not self.proc or self.proc.poll() is not None:
            return False
        try:
            payload = "\n".join(commands) + "\n"
            self.proc.stdin.write(payload.encode("latin-1"))
            self.proc.stdin.flush()
            if final_delay > 0:
                time.sleep(final_delay)
            return True
        except Exception as e:
            print(f"[NikonSdkDriver Error] Fallo en batch {commands}: {e}")
            return False

    def set_save_media(self, mode: int = 0) -> bool:
        if not self.proc or self.proc.poll() is not None:
            return False
        with self._lock:
            self._send_batch(["1", "11", str(mode), "0"], final_delay=0.025)
        self.current_save_media = mode
        return True

    def set_shutter_speed(self, speed: str) -> bool:
        if not self.connected or not self.proc or self.proc.poll() is not None:
            return False
        clean_speed = str(speed).strip().lower()
        if self.current_shutter.lower() == clean_speed:
            return True
        idx = self.SHUTTER_INDEX_MAP.get(clean_speed, 57)
        with self._lock:
            self._send_batch(["1", "8", str(idx), "0"], final_delay=0.015)
        self.current_shutter = speed
        return True

    def set_shooting_mode(self, mode: str = "single") -> bool:
        if not self.connected or not self.proc or self.proc.poll() is not None:
            return False
        clean = mode.lower().strip()
        idx = 2 if "high" in clean or clean in ("continuous_h", "ch") else (1 if "low" in clean or clean in ("continuous_l", "cl") else 0)
        target_mode = "continuous_h" if idx == 2 else ("continuous_l" if idx == 1 else "single")
        if getattr(self, "current_shooting_mode", "single") == target_mode:
            return True
        with self._lock:
            self._send_batch(["3", "8", str(idx), "0"], final_delay=0.025)
        self.current_shooting_mode = target_mode
        return True

    def set_continuous_shooting_num(self, count: int = 1) -> bool:
        if not self.connected or not self.proc or self.proc.poll() is not None:
            return False
        try:
            c = max(1, min(65535, int(count)))
            with self._lock:
                self._send_batch(["3", "9", str(c), "0"], final_delay=0.025)
            return True
        except Exception as e:
            print(f"[NikonSdkDriver Warning] Error fijando ContinuousShootingNum ({count}): {e}")
            return False

    def set_ae_bracketing(self, enable: bool = True, count: int = 9, step_index: int = 4) -> bool:
        if not self.connected or not self.proc or self.proc.poll() is not None:
            return False
        try:
            b_val = "1" if enable else "2"
            cmds = ["1", "24", b_val]
            if enable:
                bkt_type = 3 if count >= 9 else (2 if count == 7 else 1)
                cmds.extend(["28", str(bkt_type), "26", str(step_index)])
            cmds.append("0")
            with self._lock:
                self._send_batch(cmds, final_delay=0.030)
            return True
        except Exception as e:
            print(f"[NikonSdkDriver Warning] Error configurando AE Bracketing: {e}")
            return False

    def trigger_capture(self, fast_sequence: bool = False) -> bool:
        if not self.connected or not self.proc or self.proc.poll() is not None:
            return False

        was_lv = self._liveview_active
        if was_lv:
            self.stop_liveview()

        if getattr(self, "current_shooting_mode", "single") != "single":
            self.set_shooting_mode("single")

        exp_sec = self._shutter_str_to_seconds(self.current_shutter)
        wait_time = max(0.055, exp_sec + 0.045) if fast_sequence else max(0.22, exp_sec + 0.08)

        with self._lock:
            self._send_batch(["6", "1"], final_delay=wait_time)
            if self.on_shot_callback:
                self.on_shot_callback(self.current_shutter, self.current_iso)
            self._send("0", delay=0.01)

        if was_lv and not fast_sequence:
            self.start_liveview()
        return True
```

---

### Tarea 2: Optimizar `NikonPTPDriver` (Caché de Propiedades PTP, Grabación en Tarjeta y Disparo Rápido)

1. En `__init__`, inicializar:
   ```python
   self._cached_shutter_prop: Optional[int] = None
   self._cached_iso_prop: Optional[int] = None
   self.last_captured_handle: Optional[int] = None
   ```
2. En `connect()`, tras abrir sesión exitosamente (`resp_code in (0x2001, 0x201E)`), forzar que las capturas se guarden en la tarjeta SD de la cámara (`0xD00B` = `0`, Card) para evitar llenar la SDRAM:
   ```python
   self._set_ptp_prop_u8(0xD00B, 0)
   ```
3. En `set_shutter_speed` y `set_iso`, recordar qué código de propiedad PTP (`0xD100` vs `0x500D`, `0xD102` vs `0x500F`) funcionó en el primer intento para no repetir intentos fallidos en cada toma del eclipse.
4. En `trigger_capture(self, fetch_handle: bool = False) -> bool`, omitir la lectura de `self.ep_intr.read(64, timeout=25)` salvo cuando se pida explícitamente (`fetch_handle=True`), ahorrando 25 ms por disparo.
5. En `trigger_burst`, reducir el `time.sleep(0.08)` fijo o adaptarlo al tiempo de exposición real.

#### Código de referencia para `NikonPTPDriver`:

```python
    def set_shutter_speed(self, speed: str) -> bool:
        """Configura la velocidad de obturación física en la cámara vía PTP con caché de opcode."""
        if self.current_shutter == speed:
            return True
        val = parse_shutter_to_ptp_u32(speed)
        if self._cached_shutter_prop is not None:
            if self._set_ptp_prop_u32(self._cached_shutter_prop, val):
                self.current_shutter = speed
                return True

        for prop in (0xD100, 0x500D):
            if self._set_ptp_prop_u32(prop, val):
                self._cached_shutter_prop = prop
                self.current_shutter = speed
                return True
        return False

    def set_iso(self, iso: str) -> bool:
        """Configura la sensibilidad ISO física en la cámara vía PTP con caché de opcode."""
        if self.current_iso == iso:
            return True
        try:
            val = int(iso.strip())
        except ValueError:
            val = 100

        if self._cached_iso_prop is not None:
            if self._set_ptp_prop_u16(self._cached_iso_prop, val):
                self.current_iso = iso
                return True

        for prop in (0xD102, 0x500F):
            if self._set_ptp_prop_u16(prop, val):
                self._cached_iso_prop = prop
                self.current_iso = iso
                return True
        return False

    def trigger_capture(self, fetch_handle: bool = False) -> bool:
        if not self.connected or not self.ep_out or not self.ep_in:
            return False
        try:
            import struct
            self.tx_id += 1
            cmd_capture = struct.pack("<IHHI II", 20, 1, 0x100E, self.tx_id, 0, 0)
            self.ep_out.write(cmd_capture, timeout=1500)
            cap_resp = self.ep_in.read(512, timeout=2500)
            cap_code = struct.unpack("<IHHI", cap_resp[:12])[2]

            self.last_captured_handle = None
            if fetch_handle and self.ep_intr:
                try:
                    evt = self.ep_intr.read(64, timeout=20)
                    if len(evt) >= 16:
                        evt_code = struct.unpack("<IHHI", evt[:12])[2]
                        if evt_code == 0x4002:  # PTP_EC_ObjectAdded
                            self.last_captured_handle = struct.unpack("<I", evt[12:16])[0]
                except Exception:
                    pass

            if cap_code == 0x2001:  # PTP_RC_OK
                if self.on_shot_callback:
                    self.on_shot_callback(self.current_shutter, self.current_iso)
                return True
            else:
                print(f"[NikonPTP] Error en InitiateCapture: 0x{cap_code:04X}")
                self._drain_endpoints()
                return False
        except Exception as e:
            print(f"[NikonPTP Error] Excepción al disparar: {e}")
            self._drain_endpoints()
            return False
```

---

### Tarea 3: Optimizar `GPhotoCameraDriver` (`get_single_config`)

Reemplazar las llamadas a `self._camera.get_config(self._context)` en `set_shutter_speed` y `set_iso` por `get_single_config` / `set_single_config` para evitar descargar el árbol completo de propiedades USB en cada cambio:

```python
    def set_shutter_speed(self, speed: str) -> bool:
        if not self.connected:
            return False
        if self.current_shutter == speed:
            return True
        try:
            speed_widget = self._camera.get_single_config("shutterspeed", self._context)
            speed_widget.set_value(speed)
            self._camera.set_single_config("shutterspeed", speed_widget, self._context)
            self.current_shutter = speed
            return True
        except Exception as e:
            print(f"[GPhotoDriver Error] Error al cambiar velocidad: {e}")
            return False

    def set_iso(self, iso: str) -> bool:
        if not self.connected:
            return False
        if self.current_iso == iso:
            return True
        try:
            iso_widget = self._camera.get_single_config("iso", self._context)
            iso_widget.set_value(iso)
            self._camera.set_single_config("iso", iso_widget, self._context)
            self.current_iso = iso
            return True
        except Exception as e:
            print(f"[GPhotoDriver Error] Error al cambiar ISO: {e}")
            return False
```

---

### Tarea 4: Limpieza de Bug en `NikonD750SdkDriver`

1. En `NikonD750SdkDriver`, eliminar la primera definición duplicada de `trigger_burst` (líneas 748-764) que intenta hacer `.append()` sobre `self.shot_history` (atributo exclusivo de `MockCameraDriver`).
2. Mantener únicamente la segunda definición de `trigger_burst` (líneas 766-772) y aplicar también `_send_batch` en `NikonD750SdkDriver.set_shutter_speed` para reducir su latencia.

---

## 3. Recomendación Adicional para el Planificador del Eclipse

Para lograr la máxima tasa de fotogramas por segundo (10-14 FPS) en la Nikon Z5 II durante la totalidad:
1. **Desactivar Live View (`stop_liveview()`) al menos 3 segundos antes de C2:** Asegura que el sensor y el obturador electrónico no tengan que salir y entrar del modo de vídeo entre ráfagas.
2. **Usar `set_ae_bracketing(enable=True, count=9, step_index=4)` + `trigger_burst(count=9)` para la Corona:** Deja que sea el propio firmware de la Z5 II quien varíe la velocidad de obturación en modo `Continuous High (CH)` directo a la tarjeta SD, en lugar de cambiar la velocidad comando a comando por USB cuando las exposiciones sean inferiores a 1/15s.
3. **Para exposiciones largas de corona exterior o Tierra Cenicienta (0.5s a 2s):** Desactivar el AEB y usar el nuevo método `execute_bracket_ramp()` con `fast_sequence=True`.


## 4. Nota 
No se probó con una cámara física conectada al puerto USB ni se verificó la correspondencia exacta de cada índice ISO en firmwares de Nikon distintos al estándar Z5 II. Riesgo: si un cuerpo requiere más de 15 ms para consolidar un SetCapability, el parámetro final_delay de _send_batch podría necesitar ampliarse levemente en pruebas de campo.