# eclipZe — Nikon Eclipse Sequencer 🌒📸

[![Version](https://img.shields.io/badge/version-v0.1.0-blue.svg)](https://github.com/shilmar/eclipZe/releases/tag/v0.1.0)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-informational.svg)](https://www.python.org/)

**eclipZe** es una estación de control y secuenciador automatizado de alta precisión para la captura fotográfica de eclipses solares totales y anulares. Diseñado específicamente para cámaras **Nikon** (series Z como Z5 II / Z6 II y réflex serie D como D750) e integración con receptores satelitales **GPS** (u-blox / NMEA).

---

## ✨ Características Principales

* ⏱️ **Secuenciador Milimétrico de Contactos:** Automatización de ráfagas continuas de alta velocidad para Perlas de Baily (C2 y C3), bracketing de exposición dinámico para la corona solar durante la totalidad y tomas periódicas de fases parciales (C1 a C4).
* 🛰️ **Telemetría y Sincronización GPS:** Lectura en vivo de coordenadas, altitud y sincronización de reloj de precisión con receptores GPS por puerto serie (VK-162 / u-blox) para compensar desfases de la cámara con el tiempo astronómico real.
* 📷 **Controlador de Cámaras Dual:** Soporte para Slot A (cámara principal telescópica) y Slot B (cámara gran angular de paisaje y contexto), con soporte híbrido Nikon SDK nativo (C++/Type0015/Nikon Z) y protocolo PTP USB directo.
* 🗺️ **Mapa Interactivo con Bandas de Totalidad:** Visualización cartográfica sin conexión de la trayectoria del eclipse (incluyendo datos oficiales IGN para los eclipses de España 2026 y 2027), cálculo de línea central y duración exacta según la ubicación.
* 🎙️ **HUD y Alertas de Voz en Vivo:** Cuenta atrás acústica y locución sintetizada para eventos clave de seguridad (retirada de filtros solares antes de C2, avisos de tiempo restante de totalidad y colocación obligatoria de filtros en C3).
* 📋 **Generador de Planes de Contingencia (HTML):** Exportación con un solo clic de manuales de campo autosuficientes e imprimibles con efemérides locales calculadas, checklist de seguridad y tabla de exposiciones de emergencia.

---

## 🛠️ Requisitos del Sistema

* **Sistema Operativo:** Windows 10 u 11 (64-bit recomendado para drivers del SDK de Nikon).
* **Python:** 3.11 o superior.
* **Hardware Soportado:**
  * Cámaras: Nikon Z5 II, Z6 II, Z5, D750 (u otras cámaras Nikon compatibles con PTP).
  * GPS: Receptor USB NMEA (ej. u-blox 7 / VK-162 a 9600 baudios).
  * Cable USB de alta velocidad / USB-C directo a la cámara.

---

## 🚀 Instalación y Puesta en Marcha

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/shilmar/eclipZe.git
   cd eclipZe
   ```

2. **Crear y activar un entorno virtual (recomendado):**
   ```bash
   python -m venv venv
   # En Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # En Windows CMD:
   .\venv\Scripts\activate.bat
   ```

3. **Instalar dependencias necesarias:**
   ```bash
   pip install PySide6 pyusb libusb-package pyserial pillow opencv-python pytest
   ```

4. **Ejecutar la aplicación:**
   ```bash
   python main.py
   ```
   *(También puedes hacer doble clic en el ejecutable por lotes `run_eclipze.bat`)*.

---

## 📂 Estructura del Repositorio

```text
eclipZe/
├── core/                  # Núcleo de lógica astronómica, cámaras y secuenciador
│   ├── astronomy.py       # Efemérides astronómicas y cálculo de contactos C1-C4
│   ├── camera.py          # Abstracción y drivers de cámara (SDK Nikon & PTP)
│   ├── dispatcher.py      # Gestor de doble cámara (Slot A y Slot B)
│   ├── eclipse_db.py      # Base de datos local y catálogo de eclipses
│   ├── gps.py             # Lector NMEA y telemetría satelital USB
│   ├── liveview.py        # Streaming de LiveView y asistencia de enfoque
│   ├── map_manager.py     # Gestor de mapas Leaflet y caché local de teselas
│   ├── presets.py         # Tablas de exposición y presets de bracketing
│   └── sequencer.py       # Motor de ejecución temporal milimétrico
├── ui/                    # Interfaz gráfica de usuario basada en PySide6
│   ├── main_window.py     # Ventana principal e integración del secuenciador
│   ├── calendar_view.py   # Selector de catálogo, mapas y cálculo de ubicación
│   ├── focus_view.py      # Visor de enfoque en vivo y medición de contraste
│   ├── timeline_widget.py # Línea de tiempo visual del eclipse
│   ├── next_banner.py     # HUD de aviso de próximo evento y cuenta atrás
│   └── execution_log.py   # Consola de telemetría y registro de disparos
├── Win_DRV/               # SDK nativo de Nikon y drivers para Windows
├── docs/                  # Documentación técnica y manuales de usuario
│   └── manual_de_usuario.md  # Manual completo paso a paso
├── tests/                 # Batería de pruebas unitarias automatizadas
├── plans/                 # Directorio de salida para planes manuales generados
├── maps_cache/            # Directorio local para teselas descargadas de mapas
├── CHANGELOG.md           # Registro histórico de cambios y versiones
├── LICENSE                # Licencia MIT del proyecto
└── main.py                # Punto de entrada de la aplicación
```

---

## 📖 Documentación

* 📘 [Manual de Usuario](docs/manual_de_usuario.md): Guía de campo exhaustiva para el día del eclipse.
* 📋 [Registro de Cambios (Changelog)](CHANGELOG.md): Historial de versiones y notas de lanzamiento.
* 📐 [Documentación Técnica](docs/diseno_sistema_eclipze_v2.md): Arquitectura interna y especificaciones de ingeniería.

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.
