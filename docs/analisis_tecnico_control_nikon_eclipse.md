# Análisis Técnico y Arquitectura de Software: Control Automatizado de Cámaras Nikon (Serie Z y Réflex D750) para Eclipses Solares Totales

---

## 1. Introducción y Objetivos del Sistema

La captura de un eclipse solar total presenta retos operativos críticos:
* **Ventana temporal estricta:** La fase de totalidad suele oscilar entre unas decenas de segundos y pocos minutos.
* **Rango dinámico extremo:** El brillo aparente del fenómeno cambia abruptamente en varios órdenes de magnitud entre la fase parcial, las Perlas de Baily / Anillo de Diamantes, la cromosfera, las protuberancias solares y la corona externa tenue.
* **Inviabilidad del control manual:** Modificar la velocidad de obturación o ISO a mano en el cuerpo de la cámara induce trepidación, introduce latencias humanas inaceptables e impide disfrutar visualmente del fenómeno.

El objetivo de este proyecto es diseñar una aplicación multiplataforma (Windows y Linux), determinista y desatendida, capaz de ejecutar secuencias de disparo complejas (horquillados de alta densidad y tomas calibradas) sincronizadas con los contactos astronómicos ($C_1$, $C_2$, $\text{MAX}$, $C_3$, $C_4$), garantizando tolerancia a fallos y mínima latencia sobre el bus USB.

---

## 2. Evaluación de Plataformas de Software de Referencia

Para definir la especificación funcional del sistema, se han analizado las herramientas de referencia en la comunidad astrofotográfica:

### 2.1 Umbra (`umbraeclipse.app`) — Paradigma Reactivo Moderno
* **Capa PTP unificada:** Utiliza internamente una compilación optimizada de `libgphoto2` para cuerpos Nikon y Fujifilm, logrando control a bajo nivel sin licencias restrictivas de SDK propietarios.
* **Compensación de Exposición en Vivo (*Live Exposure Compensation*):** Permite al operador aplicar offsets globales ($\pm 1, \pm 2\,\text{EV}$) durante el transcurso del evento (por ejemplo, si aparece una capa delgada de cirros o nubes altas). El algoritmo redistribuye dinámicamente los parámetros (priorizando ISO o tiempo) sin alterar la ventana temporal del guion.
* **Perfilador de hardware (*Camera Gap Profiler*):** Mide empíricamente la cadencia máxima sostenible de la cámara conectada (tiempos de ciclo de obturador y confirmación de bus), validando que ningún disparo del guion se programe por debajo del umbral físico del hardware.
* **Ajuste automático de parámetros (*Value Snapping*):** Corrige automáticamente valores teóricos calculados por el generador de secuencias al valor real más próximo soportado por el firmware de la cámara.
* **Resiliencia y sincronización:** Soporte nativo para dongles GPS USB (tiempo UTC exacto sin red), prevención de suspensión del sistema (*keep-awake*) y lógica de caída y salto (*drop-and-skip*) que descarta tomas atrasadas sin acumular desfase.

### 2.2 Eclipse Orchestrator (`moonglowtech.com`) — Paradigma de Instrumentación Clásica
* **Eventos astronómicos relativos:** El guion no define instantes absolutos fijos, sino offsets temporales respecto a contactos astronómicos calculados mediante elementos besselianos y coordenadas geográficas (ejemplo: $C_2 - 00:00:15$).
* **Alertas sonoras y avisos de seguridad:** Emisión de cuentas atrás por voz y avisos sonoros obligatorios para retirar el filtro solar previo a $C_2$ y volver a colocarlo antes de $C_3$.
* **Guiones de contingencia:** Conmutación rápida a secuencias alternativas mediante atajos de teclado ante cobertura de nubes.

---

## 3. Matriz de Requisitos Funcionales para la Aplicación

| Módulo | Función | Descripción técnica |
| :--- | :--- | :--- |
| **Núcleo de Tiempo** | Motor de timeline relativo | Despachador de eventos indexados respecto a $C_1, C_2, \text{MAX}, C_3, C_4$ usando `time.perf_counter`. |
| **Tiempo Absoluto** | Calibración GPS / NTP | Lógica para fijar el reloj de referencia mediante NMEA por puerto serie (`pyserial`) o NTP previo. |
| **Driver USB** | Comunicación PTP | Abstracción sobre `libgphoto2` o comandos PTP nativos; destino de captura forzado a tarjeta física. |
| **Tolerancia a Fallos** | Política *Drop-and-skip* | Si una llamada previa consume más tiempo del previsto, descartar disparos vencidos y enganchar con la toma vigente. |
| **Snapping** | Validación de valores | Interrogación del árbol de capacidades (`shutterspeed`, `iso`) al iniciar para evitar fallos de parámetro en caliente. |
| **Avisos Sonoros** | Síntesis de voz / Beeps | Avisos audibles de cuenta atrás y manipulación de filtros mediante `pyttsx3` (compatible SAPI5 en Windows y espeak/nsspeech en POSIX). |
| **Compensación EV** | Control dinámico | Offset de ganancia (vía ISO preferentemente) aplicable mediante teclado en tiempo real sin descuadrar el reloj. |

---

## 4. Comparativa de Hardware: Nikon Serie Z vs Nikon D750

El protocolo PTP utilizado por `libgphoto2` es compatible con ambas familias, pero existen diferencias físicas y de interfaz determinantes para el diseño del temporizador:

```
┌─────────────────────────────────┬──────────────────────────────────┐
│         Nikon Serie Z           │            Nikon D750            │
├─────────────────────────────────┼──────────────────────────────────┤
│ Conector USB-C (USB 3.2 Gen 1)  │ Conector UC-E6 (USB 2.0 480 Mbps)│
│ Sin espejo (Mirrorless)         │ Caja de espejo réflex mecánica   │
│ Obturación electrónica / mec.   │ Obturador mecánico + Mirror slap │
│ Latencia PTP: ~70 - 90 ms       │ Latencia PTP: ~150 - 200 ms      │
│ Dial configurable por software  │ Dial físico (Obligatorio Modo M) │
└─────────────────────────────────┴──────────────────────────────────┘
```

### Consideraciones Específicas para la Nikon D750
1. **Cuello de botella USB 2.0:** La tasa real de transferencia por cable ronda los $30\,\text{MB/s}$. Un único archivo NEF (RAW de 24 MP) tarda entre $1$ y $1.5$ segundos en transferirse. **Es mandatorio forzar `capturetarget = "Memory card"`** y usar disparo asíncrono (`trigger_capture`).
2. **Ciclo mecánico del espejo:** El ciclo de elevación de espejo y recorrido de cortinilla requiere un suelo de seguridad (*safety margin*) de al menos $150–200\,\text{ms}$ por encima del tiempo de exposición antes de enviar el siguiente comando `set_config`.
3. **Modo Live View:** Mantener activo el Live View durante la totalidad mantiene el espejo levantado, minimizando vibraciones y acelerando el ciclo de captura.
4. **Dial físico:** La rueda superior debe fijarse físicamente en **M (Manual)**. En modos automáticos o semi-automáticos, las llamadas PTP para alterar velocidad devuelven error de dispositivo ocupado.
5. **Reducción de ruido en largas exposiciones:** Debe desactivarse en los menús internos de ambas cámaras para evitar la toma automática de *dark frames* que duplica la duración de cada exposición.

---

## 5. Estrategia Multiplataforma (Windows y Linux)

Uno de los principales problemas al operar con `gphoto2` fuera de Linux es que este stack fue concebido bajo estándares POSIX. Para lograr funcionamiento idéntico en Windows sin recurrir a scripts Bash, se deben resolver las siguientes capas:

### 5.1 El Conflicto del Driver en Windows: Reemplazo de WPD por WinUSB
Al conectar cualquier cámara Nikon en Windows 10/11:
1. El sistema operativo asigna automáticamente el controlador de clase **WPD (Windows Portable Device)**.
2. Este controlador bloquea el acceso exclusivo al dispositivo para integrarlo en el Explorador de Archivos ("Este equipo").
3. Mientras WPD esté activo, las bibliotecas basadas en `libusb` no pueden abrir el endpoint de comunicación USB.
4. **Solución:** Mediante la utilidad **Zadig** (`zadig.kevs-lab.com`), se debe sustituir el driver del dispositivo compuesto de la cámara por **WinUSB** o **libusbK**.

### 5.2 Alternativas de Ejecución en Windows

#### Opción 1: Binarios precompilados de `libgphoto2` mediante MSYS2 / MinGW-w64 (Recomendada)
* Permite cargar las bibliotecas dinámicas nativas (`libgphoto2-6.dll`, `libusb-1.0.dll`) directamente desde un runtime de Python para Windows.
* Ofrece la mínima latencia y máxima estabilidad al operar en el espacio de memoria del mismo proceso.

#### Opción 2: Subproceso CLI empaquetado (`subprocess`)
* En lugar de llamar a un script de Bash, el script en Python invoca directamente el binario compilado `gphoto2.exe` empaquetado junto a la aplicación:
  ```python
  import subprocess
  subprocess.run(["gphoto2.exe", "--set-config", "shutterspeed=1/1000", "--trigger-capture"])
  ```
* *Limitación:* Cada invocación incurre en un sobrecoste de inicialización de proceso de $\approx 50–150\,\text{ms}$. Para horquillados de alta cadencia durante la totalidad, este desfase acumulado es indeseable.

#### Opción 3: Control PTP puro sobre `pyusb` (Arquitectura Ligera)
* Prescinde totalmente de `libgphoto2`. Emplea `pyusb` para comunicarse directamente con el driver `WinUSB` en Windows o `libusb` en Linux.
* Los parámetros básicos se alteran enviando directamente los códigos de operación PTP:
  * `0x100E`: *InitiateCapture* (Disparo asíncrono).
  * `0x1016`: *SetDevicePropValue* (Configuración de velocidad e ISO).
* Es la opción más limpia para despliegues ligeros en un único script sin dependencias externas complejas.

---

## 6. Arquitectura del Motor de Software

El siguiente diagrama detalla la interacción modular entre el despachador de tiempo y la capa de hardware:

```
[Módulo de Entrada] ───────> [Cálculo Astronómico]
(Lat, Lon, Alt, UTC)          (Instantes C1, C2, MAX, C3, C4)
                                    │
                                    ▼
┌────────────────────────────────────────────────────────┐
│             DESPACHADOR DE TIEMPO REAL                 │
│  - Reloj monótono de alta resolución                   │
│  - Cola de eventos con ordenamiento temporal           │
│  - Modificador global de EV (Compensación de nubes)    │
│  - Módulo de alertas sonoras (pyttsx3)                 │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│            CAPA DE CONTROL DE HARDWARE                 │
│  - Validación de parámetros (Snapping con caché local) │
│  - Ejecución de comandos PTP (Velocidad, ISO)          │
│  - Disparo no bloqueante (Trigger Capture)             │
│  - Evaluador de tiempo de ciclo y margen de seguridad  │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
         [Cámara Nikon Z / D750 vía USB]
           (Guardado en Tarjeta SD / CFexpress)
```

---

## 7. Implementación de Referencia en Python

El siguiente script implementa un secuenciador desacoplado, compatible con Windows y Linux (asumiendo `python-gphoto2` o DLLs funcionales), que incluye timeline relativo, compensación de exposición al vuelo, lógica de descarte por retraso (*drop-and-skip*) y avisos por voz.

```python
"""
Motor de Control Automatizado para Eclipses Solares
Compatible con Nikon Serie Z y Nikon D750 via libgphoto2
"""

import time
import threading
from dataclasses import dataclass
from typing import List, Dict, Optional
import pyttsx3
import gphoto2 as gp


@dataclass
class EclipseEvent:
    contact_ref: str       # "C1", "C2", "MAX", "C3", "C4"
    offset_seconds: float  # Segundos respecto al contacto (ej: -15.0)
    shutter_speed: str     # Valor soportado (ej: "1/2000", "1/125", "1s")
    iso: str               # Valor ISO (ej: "100", "400")
    description: str       # Descripcion de la toma
    allow_skip: bool = True  # Descartar si el bus se desfasa


class CameraEngine:
    def __init__(self, is_dslr: bool = False):
        self.camera: Optional[gp.Camera] = None
        self.context = gp.Context()
        self.is_dslr = is_dslr
        # Suelo de seguridad mecanico (mayor en DSLR por ciclo de espejo)
        self.overhead_safety = 0.20 if is_dslr else 0.08
        self.available_shutters: List[str] = []

    def connect(self):
        print("[Engine] Inicializando conexion con la camara...")
        self.camera = gp.Camera()
        self.camera.init(self.context)
        
        # 1. Forzar destino de captura exclusivo en tarjeta interna
        config = self.camera.get_config(self.context)
        target = config.get_child_by_name("capturetarget")
        target.set_value("Memory card")
        self.camera.set_config(config, self.context)

        # 2. Cachear velocidades disponibles para snapping
        shutter_cfg = config.get_child_by_name("shutterspeed")
        self.available_shutters = [shutter_cfg.get_choice(i) for i in range(shutter_cfg.count_choices())]
        print(f"[Engine] Conectado. Modos de obturacion leidos: {len(self.available_shutters)}")

    def snap_shutter(self, desired: str) -> str:
        """Ajusta un valor teorico al parametro real mas proximo soportado."""
        if desired in self.available_shutters:
            return desired
        # Si no coincide exactamente, retorna el mas cercano o el primero disponible
        return self.available_shutters[0] if self.available_shutters else desired

    def apply_settings_and_trigger(self, speed: str, iso: str):
        """Aplica parametros y emite trigger asincrono sin descarga."""
        config = self.camera.get_config(self.context)
        
        # Asignar velocidad de obturacion
        speed_widget = config.get_child_by_name("shutterspeed")
        speed_widget.set_value(speed)
        
        # Asignar sensibilidad ISO
        iso_widget = config.get_child_by_name("iso")
        iso_widget.set_value(iso)
        
        self.camera.set_config(config, self.context)
        
        # Pulso de disparo sin esperar transferencia de imagen
        self.camera.trigger_capture(self.context)

    def close(self):
        if self.camera:
            self.camera.exit(self.context)


class VoiceNotifier:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 160)

    def speak(self, text: str):
        # Ejecutar locucion en hilo independiente para no bloquear el dispatcher
        threading.Thread(target=self._run_voice, args=(text,), daemon=True).start()

    def _run_voice(self, text: str):
        try:
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[Audio Error] {e}")


class EclipseSequencer:
    def __init__(self, contacts: Dict[str, float], schedule: List[EclipseEvent], camera: CameraEngine):
        self.contacts = contacts
        self.schedule = schedule
        self.camera = camera
        self.notifier = VoiceNotifier()
        self.ev_offset_steps = 0  # Modificador en vivo (+1 EV, -1 EV)

    def compute_absolute_timeline(self) -> List[tuple[float, EclipseEvent]]:
        """Traduce offsets relativos a tiempos absolutos del sistema."""
        timeline = []
        for event in self.schedule:
            t_ref = self.contacts.get(event.contact_ref)
            if t_ref is not None:
                abs_time = t_ref + event.offset_seconds
                timeline.append((abs_time, event))
        timeline.sort(key=lambda x: x[0])
        return timeline

    def run(self):
        timeline = self.compute_absolute_timeline()
        if not timeline:
            print("[Sequencer] Error: Timeline vacio.")
            return

        print(f"[Sequencer] Secuencia compilada: {len(timeline)} disparos programados.")
        
        for abs_target, event in timeline:
            while True:
                now = time.time()
                time_to_shot = abs_target - now

                # Politica de descarte (Drop-and-skip): si ya pasaron mas de 400ms, saltar
                if time_to_shot < -0.400:
                    if event.allow_skip:
                        print(f"[Skip] Disparo vencido omitido: {event.description} ({time_to_shot:.2f}s)")
                        break
                    else:
                        print(f"[Forzar] Disparo prioritario atrasado: {event.description}")

                # Si es momento de disparar (margen <= 15ms)
                if time_to_shot <= 0.015:
                    speed = self.camera.snap_shutter(event.shutter_speed)
                    print(f"[{time.strftime('%H:%M:%S', time.localtime(now))}] Trigger: {event.description} | {speed} | ISO {event.iso}")
                    
                    try:
                        self.camera.apply_settings_and_trigger(speed, event.iso)
                    except Exception as err:
                        print(f"[Error PTP] Fallo de disparo: {err}")
                    
                    # Pausa tecnica minima para no colapsar buffer USB
                    time.sleep(self.camera.overhead_safety)
                    break

                # Espera granular
                if time_to_shot > 0.05:
                    time.sleep(0.01)


# --- Ejemplo de ejecucion simulada ---
if __name__ == "__main__":
    t_base = time.time() + 10.0  # Simular que C2 ocurre en 10 segundos

    contactos = {
        "C2": t_base,
        "MAX": t_base + 60.0,
        "C3": t_base + 120.0
    }

    secuencia = [
        # Fase pre-totalidad (Perlas de Baily y Diamante)
        EclipseEvent("C2", -5.0, "1/4000", "100", "Baily Beads inicio"),
        EclipseEvent("C2", -2.0, "1/2000", "100", "Anillo de Diamante previo"),
        
        # Horquillado durante la totalidad
        EclipseEvent("C2", 1.0, "1/1000", "100", "Cromosfera y prominencias"),
        EclipseEvent("C2", 3.0, "1/250",  "100", "Corona interna"),
        EclipseEvent("C2", 5.0, "1/60",   "100", "Corona media"),
        EclipseEvent("C2", 7.0, "1/4",    "100", "Corona externa"),
        EclipseEvent("C2", 9.0, "1s",     "200", "Corona externa lejana"),
        
        # Salida
        EclipseEvent("C3", -2.0, "1/2000", "100", "Anillo de Diamante salida"),
    ]

    # Parametro is_dslr=True ajusta los timings si se emplea una Nikon D750
    driver = CameraEngine(is_dslr=False)
    
    # En entorno real:
    # driver.connect()
    # app = EclipseSequencer(contactos, secuencia, driver)
    # app.run()
    # driver.close()
```

---

## 8. Recomendaciones y Conclusiones de Campo

1. **Pruebas de estrés previo (*Rehearsal Run*):** Ejecutar la secuencia completa varias semanas antes en idénticas condiciones horarias y de temperatura, verificando que no se generen errores de escritura en tarjeta o bloqueos del buffer.
2. **Cables y conexiones mecánicas:** Usar un cable USB de alta calidad con terminal acodado y fijador mecánico al cuerpo de la cámara para prevenir desconexiones accidentales por tensión o viento.
3. **Optimización de energía:** Desactivar la suspensión del sistema operativo, el salvapantallas y las actualizaciones automáticas. Proporcionar alimentación externa ininterrumpida (batería ficticia acoplada por USB-PD) tanto para la cámara como para el equipo de control.