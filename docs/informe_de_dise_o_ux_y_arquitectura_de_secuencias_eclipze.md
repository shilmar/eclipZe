# Informe de Optimización UI/UX y Arquitectura de Secuencias (Proyecto eclipZe)

**Objetivo:** Pulir la interfaz gráfica para operación crítica en campo (bajo estrés durante la totalidad y luz solar directa en fases parciales), corregir pequeños defectos visuales y establecer la arquitectura de datos para enlazar sin errores la pestaña **Calendario de Eclipses** con **Secuencia Control**.

---

## 1. Mejoras Globales de Interfaz y Seguridad Operativa

### Tarea 1.1: Limpieza de duplicidades en la Cabecera Superior (HUD)
* **Problema actual:** El botón azul `Gestión de Equipamiento` en la barra superior (`Estado del Sistema Conectividad`) está duplicado justo encima de la pestaña homónima. Asimismo, `Reconectar Todo` y `Liberar Controles` aparecen tanto en la barra superior como dentro de la pestaña `Gestión de Equipamiento`.
* **Acción a implementar:**
  1. Eliminar el botón `Gestión de Equipamiento` de la barra superior izquierda y dejar esa zona como indicador de estado pasivo.
  2. Añadir en la barra superior un indicador visual claro del **Offset de Tiempo GPS aplicado** (ej. `GPS Sync: +0.042s [OK]` en verde cuando hay fix satelital, o `Reloj Local PC (Sin corrección GPS)` en gris/ámbar).

### Tarea 1.2: Protección y Estado de los Botones Críticos (`INICIAR SECUENCIA` y `PARADA EMERGENCIA`)
* **Problema actual:**
  1. Cuando la secuencia ya está en ejecución (`► Secuencia iniciada`), el botón verde `► INICIAR SECUENCIA` permanece en verde brillante y clicable, con riesgo de reiniciar la secuencia por accidente.
  2. Los botones de ejecución y emergencia ocupan espacio permanente en pestañas de planificación (`Mapa GPS` y `Calendario de Eclipses`).
* **Acción a implementar:**
  1. **Estado "En Curso":** Al pulsar `INICIAR SECUENCIA`, deshabilitar el botón (`setEnabled(False)`) y cambiar su texto y estilo a `● SECUENCIA EN CURSO (X/N eventos)` en tono azul/ámbar oscuro. Volver a habilitarlo solo si la secuencia termina o se pulsa `PARADA EMERGENCIA`.
  2. **Confirmación rápida anti-accidentes en `PARADA EMERGENCIA`:** Requerir doble clic rápido (o mantener pulsado 0.5s) cuando una secuencia esté activa para evitar abortar un eclipse por un roce involuntario en el touchpad en la oscuridad.

---

## 2. Mejoras en Pestaña `Secuencia Control` (Operación en Vivo)

### Tarea 2.1: Rediseño de la Barra `► NEXT` (Doble Contador y Limpieza de Avisos)
* **Problema actual:**
  1. En eventos del sistema o avisos de voz (ej. `L03 Aviso: ¡Quitar filtro solar ahora!` o `L04 Parada preventiva de Live View`), tanto la barra `NEXT` como la columna `Exposición` de la tabla muestran `1/4000 f/5.6 ISO 100`. Esto añade ruido visual en eventos que no accionan el obturador.
  2. Durante una ráfaga rápida (ej. Perlas de Baily con 18 tomas separadas por 80 ms), el contador `T -` de la barra `NEXT` parpadea de `00:00.080` en `00:00.080`, haciendo que el usuario pierda la referencia de cuánto falta para el hito astronómico (C2 o C3).
* **Acción a implementar:**
  1. **Ocultar exposición en no-disparos:** Para eventos de tipo `AVISO` o `SISTEMA` (no disparos), mostrar `--` en la columna `Exposición` de la tabla, y en la barra `NEXT` omitir los datos de obturación/ISO para destacar el mensaje en mayúsculas y fuente más grande (ej. `⚠️ AVISO: ¡QUITAR FILTRO SOLAR AHORA!`).
  2. **Doble contador en la barra `NEXT`:** Dividir la barra `NEXT` en dos zonas:
     * **Izquierda (Próxima Acción):** `NEXT: T - 00:06.1 | [Descripción acción]` (tamaño de fuente `18pt-22pt`, negrita).
     * **Derecha (Reloj de Fase / Contacto):** Contador regresivo fijo hacia el siguiente contacto principal: `C2 (TOTALIDAD) EN: 00:19.8` (antes de C2) y `FIN TOTALIDAD (C3) EN: 01:42.5` (durante la totalidad).
  3. **Resaltado cromático en tabla:** Pintar el fondo o el texto de las filas de tipo `¡Quitar filtro solar!` y `¡Poner filtro solar!` en color ámbar/naranja de alto contraste dentro del listado de eventos.

### Tarea 2.2: Optimización del Panel `Visor SD / Encuadre` y Botones Manuales
* **Acción a implementar:**
  1. Agrupar los 3 botones superiores derechos (`Disparo Único`, `Ráfaga BKT`, `Ráfaga Baily (18x)`) bajo una etiqueta o borde sutil llamado `Disparo Manual Directo` para diferenciarlos de los controles de perfil.
  2. En el cuadro `Visor SD / Encuadre`, cuando no haya foto cargada durante la secuencia automática, mostrar un resumen grande en texto del estado actual (Fase actual, progreso de ráfagas y confirmación de `Modo SD Directo Activo - Descarga USB pausada por rendimiento`) en lugar de un recuadro negro vacío con `"Sin foto cargada"`.

---

## 3. Arquitectura de Enlace: `Calendario de Eclipses` $\rightarrow$ `Secuencia Control`

Actualmente, la generación de secuencias funciona con perfiles de simulacro fijos, pero falla o carece de integración directa al cargar un eclipse desde la pestaña `Calendario de Eclipses` (especialmente si las coordenadas actuales corresponden a un eclipse parcial donde `C2` y `C3` son `--:--:--`).

### Tarea 3.1: Separar "Efeméride Activa" de "Plantilla Fotográfica (Receta)"
1. **Estructura de Efeméride (`ActiveEclipseContext`):**
   Al pulsar el botón morado `⚡ Cargar como Eclipse Activo (1-Clic)` en `Calendario de Eclipses`, se debe construir un diccionario de contexto:
   ```python
   eclipse_context = {
       "id": "2027-08-02",
       "name": "Eclipse Solar Total 2027",
       "obs_type": "TOTAL",  # "TOTAL", "ANULAR", "PARCIAL" o "SIMULACRO"
       "obscuration": 81.9,
       "duration_totality_sec": 0.0,
       "contacts_utc": {
           "C1": "07:49:52.000",
           "C2": None,       # None si es parcial en esas coordenadas
           "MAX": "08:47:00.000",
           "C3": None,
           "C4": "09:44:07.000"
       }
   }
   ```
2. **Separación en la UI de `Secuencia Control`:**
   * Mostrar una pastilla o etiqueta informativa junto a `Perfil de Eclipse` que indique qué evento temporal está gobernando el reloj:
     * `🎯 Evento: Simulacro T+60s (Duración 60s)` o `🎯 Evento: 2027-08-02 (C2: 08:46:12 UTC | Totalidad: 4m 38s)`.
   * El desplegable `Perfil de Eclipse` pasa a seleccionar la **estrategia de disparo relativa a contactos** (ej. `BKT Hardware 9 tomas (1.7 EV)`, `Rampa Manual Corona + Baily`, `Solo Fase Parcial Time-Lapse`).

### Tarea 3.2: Compilador Dinámico de Secuencias y Manejo de Eclipses Parciales (Prevención de Fallos)
Cuando el usuario pulsa `⚡ Cargar como Eclipse Activo (1-Clic)` en la pestaña `Calendario de Eclipses`, el compilador de la tabla de eventos debe actuar según el siguiente árbol de decisión para **nunca lanzar una excepción por `C2 = None`**:

1. **Caso A: El eclipse en las coordenadas elegidas es TOTAL o ANULAR (`C2` y `C3` tienen hora válida):**
   * Instanciar los eventos de entrada anclados a `C2` (`C2 - 30s` aviso preparación, `C2 - 15s` aviso quitar filtro, `C2 - 5s` apagar Live View, `C2 - 2s` a `C2 + 2s` Ráfaga Baily entrada).
   * **Bucle elástico de Totalidad (`C2 + 2.5s` hasta `C3 - 2.5s`):** Calcular el tiempo libre exacto entre el fin de Baily de entrada y el inicio de Baily de salida (`t_free = (C3 - 2.5) - (C2 + 2.5)`). Rellenar ese hueco iterando ciclos de Corona (ráfagas BKT o rampas de exposición) hasta agotar `t_free`.
   * Instanciar los eventos de salida anclados a `C3` (`C3 - 2s` a `C3 + 2s` Ráfaga Baily salida, `C3 + 3s` aviso urgente de poner filtro solar).
   * Cambiar automáticamente el foco a la pestaña `Secuencia Control` y mostrar notificación en el log inferior.

2. **Caso B: El eclipse en las coordenadas actuales es PARCIAL (`C2` y `C3` son `None`, ej. Madrid 81.9%):**
   * No intentar calcular offsets sobre `C2` en crudo. Mostrar un `QMessageBox` con 3 opciones claras para el usuario:
     * **Opción 1 — Modo Entrenamiento (Simular Totalidad Ahora):** Toma la duración máxima teórica del eclipse seleccionado en el catálogo (ej. `6m 23s` o `120s` configurables) y sitúa un `C2` sintético a `T + 60 segundos` desde el reloj actual para poder ensayar con las cámaras en casa.
     * **Opción 2 — Cargar Secuencia Real de Eclipse Parcial (Con Filtro):** Genera automáticamente una tabla de eventos entre `C1`, `MAX` y `C4` (1 disparo cada $N$ minutos con filtro solar puesto + ráfaga corta en `MAX`, sin avisos de quitar filtro).
     * **Opción 3 — Mover coordenadas a la Línea Central más cercana:** Ajusta las coordenadas de observación al punto de máxima totalidad del evento seleccionado y compila la secuencia completa.

---

## 4. Mejoras Específicas en el Resto de Pestañas

### Tarea 4.1: Pestaña `Calendario de Eclipses`
1. **Corregir bug de recorte CSS/Qt en etiquetas `Lunar Total`:**
   En la lista izquierda (`Catálogo de Eclipses 2026-2035`), las tarjetas de eclipses lunares (`2028-12-31` y `2029-06-26`) tienen el badge rojo `Lunar Total` cortado horizontalmente a la mitad. Ajustar el `min-height` de las tarjetas del `QListWidget` / `QFrame` o reducir el `padding` vertical de las etiquetas para que el texto se lea íntegro.
2. **Selector rápido de Zonas Guardadas:**
   Junto al botón `Sincronizar GPS / Mapa`, añadir un desplegable que permita cargar rápidamente las coordenadas de cualquiera de las **Zonas Cartográficas Offline** ya guardadas en la pestaña Mapa, evitando teclear latitud/longitud manualmente.

### Tarea 4.2: Pestaña `Mapa GPS Coordenadas`
1. **Dibujar la Franja de Totalidad (Path of Totality) en Leaflet:**
   Superponer en el mapa una polilínea central (amarilla/naranja) y el polígono sombreado de la franja de totalidad del eclipse seleccionado en el calendario. Esto permite verificar visualmente en el campo (con los mapas offline) si el usuario se encuentra dentro de la zona de totalidad y a qué distancia del centro.

### Tarea 4.3: Pestaña `Enfoque (Live View)`
1. **Mini-gráfico histórico de Focus Score (Últimos 10-15 segundos):**
   Complementar la barra horizontal de nitidez con una pequeña gráfica de línea continua (*sparkline*) que dibuje la evolución del `Score Actual` en los últimos 10 segundos. Al enfocar manualmente un telescopio de 600mm con vibración al tacto, ver la curva subir y bajar facilita enormemente encontrar el punto exacto de foco frente a un único número instantáneo.
2. **Alerta de saturación en el ROI:**
   Al calcular el Focus Score sobre el recorte del Sol, comprobar si más del 5% de los píxeles del disco solar tienen el canal Rojo o Verde al 100% (`>= 254`). Si está saturado, mostrar un aviso en ámbar: `"⚠️ Disco solar sobreexpuesto en Live View: reduce velocidad o ISO para una métrica de enfoque precisa"`.

### Tarea 4.4: Pestaña `Gestión de Equipamiento`
1. **Visibilidad del activador de `Ranura B`:**
   Reemplazar el pequeño checkbox oscuro junto a `Ranura B — Rol Óptico Secundario (Deshabilitada)` por un botón conmutador claro (`[ Habilitar Cámara Secundaria ]`) con borde visible para que no pase desapercibido sobre el fondo oscuro.