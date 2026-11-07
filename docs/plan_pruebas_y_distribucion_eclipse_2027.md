# Plan de Pruebas y Distribución de Disparos - Eclipse Solar Total 2027

**Fecha de elaboración:** Noviembre 2026  
**Objetivo de misión:** Eclipse Solar Total del **2 de Agosto de 2027** (Cádiz / Tarifa / Luxor)  
**Cámara principal:** Nikon Z5 II (vía SDK Oficial Plug&Play USB)  
**Configuración óptica base:** Teleobjetivo 500mm / f/8 en trípode rígido (sin Star Tracker)  

---

## 1. Parámetros Empíricos Validados en Hardware (Banco de Pruebas Noviembre 2026)

A partir de las pruebas de disparo en vivo sobre la Nikon Z5 II conectada por USB, se han certificado las siguientes métricas reales:

| Parámetro | Medición Real | Impacto en la Secuencia |
| :--- | :---: | :--- |
| **Cadencia Ráfaga Continua (CH RAW)** | **~6.4 fps** (14 tomas en 2.19s) | Ráfaga de Perlas de Baily ultra-compacta y completa. |
| **Ráfaga BKT Hardware (7 tomas a 1.7 EV)** | **1.05 segundos** | Horquillado HDR de 10 pasos EV completo en 1 segundo plano. |
| **Cobertura de Rango Dinámico (Base 1/100s)** | **1/8000s a 1/10s** (10 EV) | Protuberancias (1/8000s) hasta corona media-exterior (1/10s). |
| **Pausa de Drenaje / Desactivación BKT** | **~1.5 segundos** | Cero colapsos del SDK y sin contaminación en salidas. |
| **Pre-armado Single / Drive Mode** | **~0.3 segundos** | Conmutación invisible durante los silencios previos a Diamante. |

---

## 2. Cronograma y Distribución para el Eclipse Solar del 2 de Agosto de 2027

La totalidad en el sur de la Península Ibérica (Cádiz / Tarifa) tendrá una duración de aproximadamente **2 minutos y 45 segundos (165 segundos)**, y en Luxor (Egipto) superará los **6 minutos**. 

A continuación se detalla la distribución optimizada para una totalidad de referencia de **165 segundos (Cádiz/Tarifa 2027)**:

```text
TIEMPO RELATIVO   FASE                 DISPARO / ACCIÓN                                       OBJETIVO CIENTÍFICO / VISUAL
-----------------------------------------------------------------------------------------------------------------------------------------
C2 - 10 min       ENFOQUE TÉRMICO      Aviso de voz: "Comprobar y fijar enfoque en A"         Ajuste fino de foco con dilatación térmica
C2 - 5 min        PARCIAL PREVIA       1 toma @ 1/4000s ISO 100 (Filtro solar puesto)         Seguimiento de fase parcial
C2 - 2 min        PARCIAL FINA         1 toma @ 1/4000s ISO 100 (Filtro solar puesto)         Último vestigio de fotosfera
C2 - 30s          AVISO FILTRO #1      Aviso de voz: "Quedan 30 segundos, preparado filtro"   Preparación física del operador
C2 - 15s          QUITAR FILTRO        Aviso de voz: "¡Quitar filtro solar ahora!"            Retirada física obligatoria del filtro
C2 - 6.0s         LIVE VIEW OFF        Parada preventiva Live View + Pre-armado CH 1/4000s    Despeje USB y buffer en la Nikon Z5 II
C2 - 4.2s         BAILY ENTRADA        14 tomas CH RAW @ 1/4000s (duración 2.19s)             Perlas de Baily en valles lunares oeste
C2 - 1.2s         PRE-ARMADO DR        Conmutación Single @ 1/2000s                           Cámara en reposo absoluto previo a contacto
C2 - 1.0s         DIAMANTE ENTRADA     1 toma Single @ 1/2000s ISO 100                        Anillo de Diamante de entrada
C2 - 0.2s         DESTELLO ENTRADA     1 toma Single @ 1/2000s ISO 100                        Último destello fotosférico (Baily final)

========================================== [ C2: INICIO DE LA TOTALIDAD - 165 SEGUNDOS ] ==========================================
C2 + 4.0s         HDR CORONA #1        Ráfaga BKT 7 tomas (1.7 EV, base 1/100s) [1.05s]       Cromosfera + Protuberancias emergentes
C2 + 18.0s        HDR CORONA #2        Ráfaga BKT 7 tomas (1.7 EV, base 1/100s) [1.05s]       Corona media y penachos polares
C2 + 36.0s        HDR CORONA #3        Ráfaga BKT 7 tomas (1.7 EV, base 1/100s) [1.05s]       Streamers ecuatoriales (primer tercio)
C2 + 56.0s        HDR CORONA #4        Ráfaga BKT 7 tomas (1.7 EV, base 1/100s) [1.05s]       Estructura magnética coronal
C2 + 82.0s        HDR MÁXIMO #5        Ráfaga BKT 7 tomas (1.7 EV, base 1/100s) [1.05s]       Punto medio de la totalidad (máxima simetría)
C2 + 105.0s       HDR CORONA #6        Ráfaga BKT 7 tomas (1.7 EV, base 1/100s) [1.05s]       Corona media y streamers este
C2 + 125.0s       HDR CORONA #7        Ráfaga BKT 7 tomas (1.7 EV, base 1/100s) [1.05s]       Evolución de protuberancias este
C2 + 145.0s       HDR CORONA #8        Ráfaga BKT 7 tomas (1.7 EV, base 1/100s) [1.05s]       Último bloque HDR previo a C3
C2 + 150.0s       DESACTIVACIÓN BKT    Desactivación BKT + Pre-armado Single @ 1/2000s        Cámara en reposo 12 segundos antes de C3

========================================== [ C3: FIN DE LA TOTALIDAD ] ============================================================
C3 - 2.2s         DESTELLO SALIDA      1 toma Single @ 1/2000s ISO 100                        Aparición primer rayo fotosférico este
C3 - 1.2s         DIAMANTE SALIDA      1 toma Single @ 1/2000s ISO 100                        Anillo de Diamante de salida
C3 + 0.5s         BAILY SALIDA         14 tomas CH RAW @ 1/4000s (duración 2.19s)             Perlas de Baily salientes (limbo este)
C3 + 5.0s         PONER FILTRO         Aviso de voz: "¡Colocar filtro solar inmediatamente!"  Seguridad ocular y protección de sensor
C3 + 15.0s        PARCIAL POST-C3      1 toma @ 1/4000s ISO 100 (Filtro puesto)               Inicio de fase parcial de retroceso
C3 + 60.0s        REPORTE TELEMETRÍA   Reporte de telemetría y vaciado de cola                Verificación de integridad de almacenamiento
```

---

## 3. Batería de Pruebas Pendientes de Realizar (Checklist de Validación Pre-2027)

Para garantizar un éxito del 100% en condiciones de expedición, se deben realizar las siguientes pruebas de laboratorio y campo:

### Prueba 1: Compensación EV Dinámica en Vivo (*Live EV Offset*)
* **Objetivo:** Verificar la respuesta del secuenciador si durante la totalidad entran cirros o calima y el operador pulsa `+1 EV` o `+2 EV` en la interfaz.
* **Aspectos a comprobar:**
  1. Que la velocidad base del BKT suba de `1/100s` a `1/50s` o `1/25s` sin interrumpir el temporizador.
  2. Que el comando SDK no desactive accidentalmente el bracketing por hardware.
  3. Que al volver a `0 EV` el sistema recupere la base de `1/100s`.

### Prueba 2: Operación Dual con Cámara Secundaria (Ranura B)
* **Objetivo:** Si se emplea una segunda cámara (ej. Nikon D750 o gran angular para paisaje crepuscular 360°), validar la sincronización mediante `MultiCameraDispatcher`.
* **Aspectos a comprobar:**
  1. Que los disparos en Ranura B no colisionen en el bus USB mientras la Z5 II está disparando su ráfaga BKT de 7 fotos.
  2. Que el desfase escalonado (*stagger delay* de 30 ms) funcione limpiamente sin retardar la cámara principal.

### Prueba 3: Tarjeta SD Definitiva y Resistencia Térmica Prolongada
* **Objetivo:** Certificar el comportamiento con la tarjeta de memoria final (UHS-II V60 o V90).
* **Aspectos a comprobar:**
  1. Ejecutar una secuencia continua de 8 bloques HDR seguidos (56 fotos RAW de 25 MB = 1.4 GB) comprobando que el búfer se vacíe en menos de 3.5 segundos entre bloques.
  2. Monitorear el sensor térmico de la cámara tras 15 minutos de conexión con Live View previo para descartar incremento de ruido de corriente oscura (*dark current*).

### Prueba 4: Verificación del Dial U3 en Frío (Checklist Físico de Salida)
* **Objetivo:** Garantizar que no haya sesgos de configuración física en el cuerpo de la cámara.
* **Aspectos a comprobar:**
  1. Modo dial en **U3**.
  2. Dial físico de compensación de exposición en **`0.0 EV`** (verificar que no esté en $+0.33$ EV).
  3. ISO base en **`100`** nativo (no en Lo 0.3 / 80).
  4. Reducción de vibración (VR): **OFF** (recomendado en trípode pesado para evitar derivas de estabilizador en exposiciones de 1/10s).
  5. Modo de enfoque: **MF** (Manual Focus) fijo y con cinta adhesiva en el anillo de enfoque tras la calibración térmica de C2 - 10 min.

### Prueba 5: Resiliencia ante Micro-Desconexión USB
* **Objetivo:** Simular un tirón accidental o vibración del cable USB en campo.
* **Aspectos a comprobar:**
  1. Comportamiento del driver si el cable USB pierde contacto durante 1 segundo antes de la totalidad.
  2. Capacidad de auto-reconexión PnP de `EquipmentManager` sin necesidad de reiniciar el ejecutable de eclipZe.
