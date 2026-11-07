# Manual de Usuario de eclipZe 🌒📖

**Estación de Control y Secuenciador Automatizado para Eclipses Solares**  
*Compatible con Nikon Serie Z (Z5 II, Z6 II, Z5) y Serie D (D750)*

---

## 📑 Índice de Contenidos
1. [Introducción y Conceptos Básicos](#1-introducción-y-conceptos-básicos)
2. [Seguridad Solar Obligatoria](#2-seguridad-solar-obligatoria)
3. [Preparación del Equipo y Hardware](#3-preparación-del-equipo-y-hardware)
4. [Puesta en Marcha e Interfaz](#4-puesta-en-marcha-e-interfaz)
5. [Ubicación y Efemérides (GPS y Mapas)](#5-ubicación-y-efemérides-gps-y-mapas)
6. [Configuración de Cámaras y Enfoque](#6-configuración-de-cámaras-y-enfoque)
7. [Planificación de Secuencias de Disparo](#7-planificación-de-secuencias-de-disparo)
8. [Modo Simulación (Ensayo General)](#8-modo-simulación-ensayo-general)
9. [Protocolo el Día del Eclipse (Ejecución en Vivo)](#9-protocolo-el-día-del-eclipse-ejecución-en-vivo)
10. [Plan de Emergencia en Campo](#10-plan-de-emergencia-en-campo)
11. [Solución de Problemas Frecuentes](#11-solución-de-problemas-frecuentes)

---

## 1. Introducción y Conceptos Básicos

**eclipZe** es una aplicación diseñada para eliminar el estrés del fotógrafo durante la totalidad de un eclipse solar. Durante los pocos minutos (o segundos) que dura la totalidad, cambiar manualmente las velocidades de obturación de una o dos cámaras es una fuente común de errores. 

eclipZe automatiza el disparo coordinado, calcula los tiempos exactos según tu posición GPS y te guía mediante **alertas visuales y por voz** para que disfrutes del eclipse a simple vista mientras las cámaras capturan todos los fenómenos.

### Fases de un Eclipse Total de Sol
* **C1 (Primer Contacto):** La Luna comienza a morder el disco solar. Inicio de la fase parcial.
* **C2 (Segundo Contacto):** El disco solar queda totalmente cubierto. Justo antes ocurren las **Perlas de Baily** y el **Anillo de Diamantes**.
* **Máximo:** Punto central de la totalidad. Máxima oscuridad; momento ideal para capturar la corona exterior tenue.
* **C3 (Tercer Contacto):** El Sol vuelve a asomar. Reaparición del anillo de diamantes y fin de la totalidad.
* **C4 (Cuarto Contacto):** La Luna abandona el disco solar por completo. Fin del eclipse.

---

## 2. Seguridad Solar Obligatoria

> [!CAUTION]
> **DAÑO OCULAR IRREVERSIBLE Y ROTURA DE CÁMARA:**  
> Mirar directamente al Sol sin filtro certificado o enfocar un telescopio/teleobjetivo al Sol sin filtro frontal destruirá el sensor de la cámara y causará ceguera permanente al instante.

1. **Filtros Solares Certificados (ISO 12312-2 / Densidad Óptica 5.0):**  
   Deben permanecer colocados **frente a la óptica** de todas las cámaras durante **toda la fase parcial** (desde C1 hasta instantes antes de C2, y de nuevo inmediatamente tras C3 hasta C4).
2. **Ventana de Totalidad (Solo entre C2 y C3):**  
   Únicamente cuando el Sol está 100% eclipsado es seguro retirar los filtros solares. eclipZe emitirá una locución de aviso clara para **retirar los filtros** segundos antes de C2 y para **recolocarlos de inmediato** segundos antes de C3.

---

## 3. Preparación del Equipo y Hardware

### Checklist previo a salir de viaje
* **Portátil / PC de control:** Con Windows 10/11 de 64 bits y batería cargada al 100% (llevar batería externa o cargador de coche de 12V/USB-PD).
* **Cámaras Nikon compatibles:**
  * Ranura A (Principal): Nikon Z5 II / Z6 II / Z5 acoplada a telescopio o teleobjetivo (300mm a 800mm).
  * Ranura B (Contexto - opcional): Nikon D750 u otro cuerpo gran angular (14mm a 35mm) para capturar el horizonte y paisaje.
* **Tarjetas de memoria:** SD UHS-II o UHS-I formateadas de alta velocidad (V60 / V90 recomendadas para soportar ráfagas continuas de Baily sin saturar el buffer).
* **Baterías de cámara:** Cargadas al 100% (usar acoplador de corriente continua o alimentación por USB-C si es posible).
* **Cables USB:** Cables de datos blindados de calidad (evitar alargadores no amplificados).
* **Receptor GPS USB:** Módulo basado en u-blox (como el VK-162) con conexión serie COM.
* **Trípode robusto:** Bien contrapesado contra el viento.

---

## 4. Puesta en Marcha e Interfaz

1. Conecta el receptor GPS y la(s) cámara(s) a los puertos USB de tu ordenador.
2. Enciende las cámaras y colócalas en **Modo Manual (M)** y **Enfoque Manual (MF)**.
3. Inicia eclipZe ejecutando `python main.py` o haciendo doble clic en `run_eclipze.bat`.
4. La ventana principal se divide en 4 zonas funcionales:
   * **Superior (Banner HUD):** Cuenta atrás hacia el próximo evento crítico y estado general.
   * **Izquierda (Control de Dispositivos):** Conexión de GPS, cámaras Ranura A y B, y visor de previsualizaciones.
   * **Centro (Línea de Tiempo y Visor):** Representación gráfica de las fases y visor de enfoque.
   * **Inferior (Consola de Registro):** Log en vivo de eventos, disparos ejecutados y telemetría.

---

## 5. Ubicación y Efemérides (GPS y Mapas)

### Sincronización GPS Automática
1. En el panel lateral izquierdo, selecciona el puerto COM de tu GPS (habitualmente `COM3` o `COM4`) a `9600` baudios.
2. Pulsa **Conectar GPS**.
3. El indicador mostrará la búsqueda de satélites. Cuando logre **Fix 3D (verde)**, las coordenadas geográficas (latitud, longitud y altitud) se actualizarán en tiempo real.
4. eclipZe calculará automáticamente el desfase horario entre el reloj del PC y el tiempo satelital UTC atómico.

### Selector de Catálogo y Mapas sin Conexión
1. Abre la pestaña **Calendario / Mapas**.
2. Selecciona el eclipse objetivo (ej. *España 12 de Agosto de 2026* o *España 2 de Agosto de 2027*).
3. Haz clic sobre el mapa interactivo en tu punto de observación exacto si deseas fijar la posición de forma manual.
4. **Descarga de mapas para campo:** Utiliza el botón de pre-descarga de teselas de la zona. eclipZe almacenará los mapas en [`maps_cache/`](file:///d:/software/eclipZe/maps_cache) para que el visor cartográfico funcione en medio del campo sin cobertura telefónica.

---

## 6. Configuración de Cámaras y Enfoque

### Conexión de Cámaras
* **Ranura A (Nikon Z):** Selecciona el modelo en el desplegable y haz clic en **Conectar Ranura A**. La app inicializará el driver nativo de alta velocidad.
* **Ranura B (Secundaria):** Si dispones de un segundo cuerpo (ej. Nikon D750 para gran angular), actívalo y conéctalo en la Ranura B. Si operas con un único cuerpo, desmarca la casilla de la Ranura B para no bloquear la secuencia.

### Calibración de Enfoque Infinito
1. Coloca el filtro solar en el objetivo.
2. Apunta al Sol y busca manchas solares o el borde del limbo solar.
3. Abre el **Visor de Enfoque (Focus Assist)** en eclipZe.
4. Observa el valor numérico de contraste y el recuadro ampliado:
   * Gira el anillo de enfoque lentamente hasta que el número de contraste alcance su **pico máximo**.
   * Bloquea el anillo de enfoque con cinta adhesiva para evitar movimientos accidentales por viento o temperatura.

---

## 7. Planificación de Secuencias de Disparo

eclipZe viene preconfigurado con algoritmos optimizados para cada fase del eclipse:

| Fase | Disparo | Objetivo Fotográfico |
| :--- | :--- | :--- |
| **Parcial (C1 a C2)** | 1 toma cada 3-5 minutos | Documentar la progresión del tránsito lunar |
| **Perlas de Baily (C2)** | Ráfaga continua rápida (~1/4000s) | Capturar valles lunares y anillo de diamantes |
| **Cromosfera** | Exposiciones rápidas (1/1000s a 1/500s) | Captar llamaradas y prominencias de tono rojizo |
| **Corona Interna** | Bracketing medio (1/250s a 1/30s) | Detalles de filamentos y bucles magnéticos |
| **Corona Externa** | Bracketing largo (1/4s a 2s) | Máxima extensión coronal y luz cenicienta lunar |
| **Perlas de Baily (C3)** | Ráfaga continua rápida | Reaparición del Sol |

Puedes ajustar los tiempos de inicio y fin de ráfaga y los pasos de bracketing en el panel de configuración de secuencias.

---

## 8. Modo Simulación (Ensayo General)

> [!TIP]
> **Realiza al menos dos simulacros completos antes del día del evento.**

1. Pulsa el botón **Simulacro (Dry-Run)**.
2. La aplicación simulará el reloj avanzando a través de C2, la totalidad y C3:
   * Escucharás los avisos de voz: *"Quitar filtro solar en 10 segundos"*, *"Totalidad iniciada"*, *"30 segundos restantes"*, *"Colocar filtro solar inmediatamente"*.
   * Las cámaras simularán los disparos o ejecutarán tomas reales con la tapa puesta para comprobar la cadencia del buffer.
   * Verifica que tienes tiempo holgado para retirar y reponer los filtros con calma.

---

## 9. Protocolo el Día del Eclipse (Ejecución en Vivo)

### Línea Temporal de Actuación en Campo

* **T - 60 min:** Montaje mecánico, equilibrado del trípode y conexión de cables.
* **T - 30 min:** Conexión de GPS (verificar Fix satelital), encendido de cámaras, comprobación de baterías y enfoque fino con el Sol.
* **T - 15 min:** Sincronización de reloj de las cámaras mediante GPS y arranque del secuenciador en modo **Armado / En Espera**.
* **C1:** Comienza el registro automático de fases parciales.
* **C2 - 40 seg:** Suena el aviso de aviso de preparación. Retira las tapas de los filtros pero mantén los filtros frente al objetivo.
* **C2 - 15 seg:** Suena la voz: *"Retirar filtros solares"*. Retira con suavidad los filtros solares de todas las cámaras.
* **C2 a C3 (TOTALIDAD):** eclipZe ejecuta las ráfagas de Baily y los ciclos de bracketing HDR coronal. ¡Aparta la vista del ordenador y mira al cielo!
* **C3 - 10 seg:** Suena la voz: *"Colocar filtros solares urgentemente"*. Coloca de nuevo los filtros solares frente a las lentes antes de que emerja el primer destello.
* **C4:** Finaliza la sesión. Las fotos quedarán almacenadas en las tarjetas SD de alta velocidad.

---

## 10. Plan de Emergencia en Campo

Si tu ordenador sufre una avería, corte de batería o incidente en pleno campo, eclipZe incluye un sistema de contingencia:

1. Antes de salir de casa, pulsa **Exportar Plan Manual (HTML)** en la vista de calendario.
2. eclipZe creará un informe completo en la carpeta [`plans/`](file:///d:/software/eclipZe/plans) adaptado a tus coordenadas exactas.
3. **Imprime en papel este documento**. Contiene:
   * La tabla horaria exacta al segundo de C1, C2, Máximo, C3 y C4.
   * La tabla de exposiciones y configuraciones manuales recomendadas (ISO, diafragma y obturación).
   * Checklist de supervivencia para operar la cámara con intervalómetro físico si falla la informática.

---

## 11. Solución de Problemas Frecuentes

### La cámara no conecta por USB
* Comprueba que la cámara no esté en modo almacenamiento masivo estándar.
* Asegúrate de que no haya otros programas de fotografía abiertos en Windows (Nikon Camera Control Pro, Lightroom, etc.) disputando el puerto USB.
* Cambia de puerto USB (preferiblemente un puerto USB 3.0 / USB-C directo en la placa base del portátil, sin hubs intermedios pasivos).

### El visor de fotos / miniaturas no carga
* Revisa que la cámara esté configurada para guardar en ranura SD primaria o dual SDRAM.
* La carpeta temporal de previsualizaciones se purga automáticamente; si la cámara está escribiendo un archivo RAW muy grande, la miniatura tardará un segundo en aparecer.

### El GPS no obtiene Fix (satélites en 0 o buscando)
* Los receptores GPS requieren visión directa hacia la bóveda celeste. Si estás dentro de un vehículo o bajo un techo metálico, colócalo en el techo del coche o sobre el trípode.
* El primer encendido en frío (*Cold Start*) puede tardar entre 2 y 4 minutos en descargar las efemérides satelitales. Ten paciencia.

### El buffer de la cámara se bloquea durante la ráfaga de Baily
* Utiliza exclusivamente tarjetas de memoria SD clasificadas como **UHS-II V60 o V90**.
* En el menú de la cámara, desactiva la reducción de ruido en exposiciones largas y el D-Lighting activo, ya que consumen tiempo de procesamiento en el procesador EXPEED de la cámara.
