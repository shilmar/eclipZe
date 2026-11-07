# Registro de Cambios (Changelog)

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/) y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

---

## [0.1.0] - 2026-11-07

### Añadido
* **Motor Astronómico y Catálogo (`core/astronomy.py`, `core/eclipse_db.py`):**
  * Cálculo de efemérides astronómicas de alta precisión para posiciones solares y lunares.
  * Determinación de instantes exactos de contacto (C1, C2, C3, C4, Máximo) y duración de totalidad según latitud, longitud y altitud.
  * Catálogo de eclipses solares con especial soporte para los eclipses de España (12 de agosto de 2026 y 2 de agosto de 2027), incluyendo datos oficiales de la franja del IGN.
* **Control de Cámaras Nikon y Protocolo PTP (`core/camera.py`):**
  * Soporte nativo para Nikon Z5 II / serie Z vía SDK C++ (`Win_DRV/Nikon_Z/TestApp.exe`).
  * Soporte nativo para réflex Nikon D750 vía SDK legacy (`Win_DRV/Nikon_D750/Type0015Ctrl.exe`).
  * Driver alternativo multiplataforma USB PTP directo (`PyUSB` / `libusb-1.0`).
  * Control de velocidad de obturación, apertura, sensibilidad ISO, modo de disparo y balance de blancos.
  * Descarga rápida de miniaturas para visor de encuadre en tarjeta SD / memoria RAM.
* **Despachador Dual de Cámaras (`core/dispatcher.py`):**
  * Gestión concurrente de dos ranuras fotográficas: Ranura A (telescopio/focal larga) y Ranura B (paisaje/gran angular).
  * Capacidad de deshabilitar la Ranura B para operación individual sin alterar la línea de tiempo.
* **Telemetría y Sincronización GPS (`core/gps.py`):**
  * Lector asíncrono para receptores GPS serie NMEA (ej. u-blox VK-162) a 9600 baudios.
  * Detección en tiempo real de Fix satelital, número de satélites, coordenadas de campo y cálculo de desfase con el reloj del sistema.
* **Motor de Secuencias y Línea de Tiempo (`core/sequencer.py`, `core/presets.py`):**
  * Automatización precisa de fases:
    * Fase Parcial: Tomas de intervalo regular.
    * Perlas de Baily (C2 y C3): Disparo continuo en ráfaga a alta velocidad.
    * Totalidad (Corona): Secuencias de bracketing de amplio rango dinámico (HDR coronal).
    * Cromosfera y prominencias solares.
* **Interfaz de Usuario PySide6 (`ui/`):**
  * Ventana principal interactiva con visor de estado de cámaras, controles manuales de disparo y telemetría.
  * Visor cartográfico Leaflet integrado sin conexión con soporte para descarga de teselas locales (`maps_cache/`).
  * Asistente de enfoque y LiveView (`ui/focus_view.py`) con detección de contraste numérico por algoritmo Laplacian/Sobel.
  * HUD visual de cuenta atrás y banner de próximo evento (`ui/next_banner.py`).
  * Consola de ejecución en vivo con historial de disparos y estado de buffer (`ui/execution_log.py`).
* **Simulador y Alertas Sonoras (`core/audio.py`):**
  * Ensayo previo de totalidad en tiempo real (Dry-Run) con avance rápido opcional.
  * Locución y beeps sonoros acústicos para avisos de seguridad críticos: retirar filtros solares, avisos de tiempo restante de totalidad y recolocación urgente de filtros en C3.
* **Plan de Emergencia y Respaldo en HTML (`core/backup_plan.py`):**
  * Generador de informes autosuficientes con hojas de ruta horarias locales, tablas de exposición manuales y checklist impreso de campo.
* **Batería de Pruebas Automatizadas (`tests/`):**
  * 14 módulos de pruebas unitarias (`pytest`) que cubren cálculo de efemérides, secuenciador, seguridad de la UI, despacho dual, asistente de enfoque y sincronización de reloj.
