"""
Plantillas de secuencias de disparo y horquillado para eclipZe.
Incluye perfiles para Eclipse Solar Total (agosto 2027), Eclipse Lunar y simulacro rápido.
"""

from typing import List
from dataclasses import dataclass, field


@dataclass
class EclipseEvent:
    """Representa un disparo programado dentro de la secuencia."""
    contact_ref: str          # "C1", "C2", "MAX", "C3", "C4" (Solar) o "U1", "U2", "MAX", "U3", "U4" (Lunar)
    offset_seconds: float     # Offset temporal en segundos respecto al contacto (negativo = antes, positivo = después)
    shutter_speed: str        # Velocidad teórica base (ej: "1/4000", "1/250", "2s")
    iso: str                  # Sensibilidad ISO base (ej: "100", "400")
    description: str          # Descripción del objetivo astronómico de la toma
    allow_skip: bool = True   # Si es True, se descarta si el bus PTP o la cámara sufren desfase
    executed: bool = False
    skipped: bool = False
    actual_timestamp: float = 0.0
    camera_slot: str = "A"    # "A" (Cámara A / Master) o "B" (Cámara B / Slave)
    event_id: str = ""        # Identificador del evento (ej: "L01", "L02")
    phase: str = ""           # Fase astronómica: "DR", "BB", "CH", "PR", "PARCIAL"
    aperture: str = "f/5.6"   # Apertura relativa para telemetría
    is_shot: bool = True      # Si es False, es un evento de aviso/control de sistema sin accionar el obturador
    burst_count: int = 1      # Número de tomas en ráfaga continua por hardware si > 1


def is_notice_event(event: EclipseEvent) -> bool:
    """Identifica si el evento es puramente informativo, de aviso por voz o control (sin disparo de cámara)."""
    if not getattr(event, "is_shot", True):
        return True
    desc = event.description.lower()
    return (
        "aviso:" in desc or
        "alerta:" in desc or
        "parada preventiva" in desc or
        "vaciado búfer" in desc or
        "fin de " in desc or
        "reporte telemetría" in desc or
        ("filtro" in desc and ("quitar" in desc or "poner" in desc or "colocar" in desc or "mantener" in desc or "asegurar" in desc or "asegurado" in desc or "no retirar" in desc or "no quitar" in desc))
    )


def infer_phase(event: EclipseEvent) -> str:
    """Deduce la fase astronómica (DR, BB, CH, PR, PARCIAL) a partir de descripción y offset."""
    desc = event.description.lower()
    if "diamante" in desc or "diamond" in desc:
        return "DR"
    if "baily" in desc or "beads" in desc:
        return "BB"
    if "cromosfera" in desc or "chromosphere" in desc:
        return "CH"
    if "corona" in desc or "prominencia" in desc or "totalidad" in desc or "ceniciento" in desc:
        return "PR"
    if "parcial" in desc or "filtro" in desc or "aviso" in desc or "alerta" in desc or "live view" in desc or "inicio" in desc or "test" in desc or "vaciado" in desc or "reporte" in desc:
        return "PARCIAL"
    if event.contact_ref == "C2":
        if event.offset_seconds <= -5.0:
            return "PARCIAL"
        elif event.offset_seconds < -2.0:
            return "BB"
        elif event.offset_seconds <= 0.0:
            return "DR"
        elif event.offset_seconds <= 3.0:
            return "BB"
        elif event.offset_seconds <= 8.0:
            return "CH"
        else:
            return "PR"
    elif event.contact_ref == "C3":
        if event.offset_seconds < -3.0:
            return "CH"
        elif event.offset_seconds <= 0.0:
            return "BB"
        elif event.offset_seconds <= 2.0:
            return "DR"
        elif event.offset_seconds <= 5.0:
            return "BB"
        else:
            return "PARCIAL"
    return "PR"


def assign_event_metadata(events: List[EclipseEvent]) -> List[EclipseEvent]:
    """Asigna identificadores únicos (L01, L02...), fases y ranura por defecto si faltan."""
    for idx, ev in enumerate(events, start=1):
        if not ev.event_id:
            ev.event_id = f"L{idx:02d}"
        if not ev.phase:
            ev.phase = infer_phase(ev)
        if not ev.camera_slot:
            ev.camera_slot = "A"
        if not getattr(ev, "aperture", None):
            ev.aperture = "f/5.6"
        if is_notice_event(ev):
            ev.is_shot = False
            ev.allow_skip = False
    return events


def get_solar_eclipse_2027_preset() -> List[EclipseEvent]:
    """
    Secuencia optimizada de horquillado para totalidad de eclipse solar (Cádiz/Luxor 2027).
    Calibrada a f/8 ISO 100 a 500mm sin star tracker, con avisos de filtro a -30s y -15s,
    recordatorio de enfoque térmico a C2-10min y ráfagas de Perlas de Baily a 1/4000s.
    """
    events = [
        # --- Pre-C2: Comprobación de foco térmico y fase parcial con filtro solar ---
        EclipseEvent("C2", -600.0, "1/4000", "100", "Alerta: 10 minutos para C2. Comprobar y fijar enfoque en cámara principal", allow_skip=False, camera_slot="A"),
        EclipseEvent("C2", -120.0, "1/4000", "100", "Parcial con filtro solar (C2 - 2 min)", allow_skip=True, camera_slot="A"),
        EclipseEvent("C2", -60.0,  "1/4000", "100", "Parcial fina pre-C2 (Con filtro solar)", allow_skip=True, camera_slot="A"),
        
        # --- Avisos de seguridad de filtro solar ---
        EclipseEvent("C2", -30.0, "1/4000", "100", "Aviso: Quedan 30 segundos, preparado para el filtro", allow_skip=False, camera_slot="A"),
        EclipseEvent("C2", -15.0, "1/4000", "100", "Aviso: ¡Quitar filtro solar ahora!", allow_skip=False, camera_slot="A"),
        EclipseEvent("C2", -5.0,  "1/4000", "100", "Parada preventiva de Live View", allow_skip=True, camera_slot="A"),
        
        # --- Ventana de C2: Perlas de Baily (Sweet Spot 1/4000s f/8 ISO 100) y Diamante ---
        EclipseEvent("C2", -4.0, "1/4000", "100", "Baily Beads inicio (Ráfaga)", allow_skip=True, camera_slot="A", phase="BB"),
        EclipseEvent("C2", -3.5, "1/2000", "200", "Paisaje: Entrada de umbra", allow_skip=True, camera_slot="B", phase="BB"),
        EclipseEvent("C2", -3.0, "1/4000", "100", "Baily Beads pico central", allow_skip=True, camera_slot="A", phase="BB"),
        EclipseEvent("C2", -2.0, "1/4000", "100", "Baily Beads fin valles", allow_skip=True, camera_slot="A", phase="BB"),
        EclipseEvent("C2", -1.0, "1/2000", "100", "Anillo de Diamante entrada", allow_skip=True, camera_slot="A", phase="DR"),
        EclipseEvent("C2", -0.2, "1/2000", "100", "Diamante destello fotosférico", allow_skip=True, camera_slot="A", phase="DR"),

        # --- TOTALIDAD: Horquillado 9 pasos EV (sin Star Tracker a 500mm, max 1s) ---
        EclipseEvent("C2", +1.5, "1/8000", "100", "HDR 1: Cromosfera extrema (#1)", allow_skip=True, camera_slot="A", phase="CH"),
        EclipseEvent("C2", +3.0, "1/4000", "100", "HDR 1: Protuberancias H-alpha (#2)", allow_skip=True, camera_slot="A", phase="CH"),
        EclipseEvent("C2", +4.5, "1/1250", "100", "HDR 1: Corona interna base (#3)", allow_skip=True, camera_slot="A", phase="PR"),
        EclipseEvent("C2", +5.5, "1/500",  "200", "Paisaje: Sombra 360° totalidad", allow_skip=True, camera_slot="B", phase="PR"),
        EclipseEvent("C2", +6.5, "1/400",  "100", "HDR 1: Penachos polares (#4)", allow_skip=True, camera_slot="A", phase="PR"),
        EclipseEvent("C2", +9.0, "1/125",  "100", "HDR 1: Corona media anclaje (#5)", allow_skip=True, camera_slot="A", phase="PR"),
        EclipseEvent("C2", +12.0, "1/40",  "100", "HDR 1: Corona media-externa (#6)", allow_skip=True, camera_slot="A", phase="PR"),
        EclipseEvent("C2", +13.5, "1/30",  "400", "Paisaje: Atmósfera crepuscular", allow_skip=True, camera_slot="B", phase="PR"),
        EclipseEvent("C2", +15.5, "1/13",  "100", "HDR 1: Corona externa (#7)", allow_skip=True, camera_slot="A", phase="PR"),
        EclipseEvent("C2", +19.0, "1/4",   "100", "HDR 1: Streamers lejanos (#8)", allow_skip=True, camera_slot="A", phase="PR"),
        EclipseEvent("C2", +23.0, "1s",    "100", "HDR 1: Brillo ceniciento / fondo (#9)", allow_skip=True, camera_slot="A", phase="PR"),

        # --- Ventana de Vaciado de Búfer SD ---
        EclipseEvent("C2", +28.0, "1/125", "100", "Vaciado búfer SD y monitor térmico", allow_skip=True, camera_slot="A", phase="PR"),

        # --- Segundo ciclo de horquillado invertido ---
        EclipseEvent("C2", +35.0, "1s",    "100", "HDR 2: Brillo ceniciento (#9)", allow_skip=True, camera_slot="A", phase="PR"),
        EclipseEvent("C2", +39.0, "1/4",   "100", "HDR 2: Streamers lejanos (#8)", allow_skip=True, camera_slot="A", phase="PR"),
        EclipseEvent("C2", +42.0, "1/13",  "100", "HDR 2: Corona externa (#7)", allow_skip=True, camera_slot="A", phase="PR"),
        EclipseEvent("C2", +45.0, "1/40",  "100", "HDR 2: Corona media-externa (#6)", allow_skip=True, camera_slot="A", phase="PR"),
        EclipseEvent("C2", +48.0, "1/125", "100", "HDR 2: Corona media anclaje (#5)", allow_skip=True, camera_slot="A", phase="PR"),
        EclipseEvent("C2", +50.5, "1/400", "100", "HDR 2: Penachos polares (#4)", allow_skip=True, camera_slot="A", phase="PR"),
        EclipseEvent("C2", +53.0, "1/1250", "100", "HDR 2: Corona interna (#3)", allow_skip=True, camera_slot="A", phase="PR"),
        EclipseEvent("C2", +55.0, "1/4000", "100", "HDR 2: Protuberancias (#2)", allow_skip=True, camera_slot="A", phase="CH"),
        EclipseEvent("C2", +57.0, "1/8000", "100", "HDR 2: Cromosfera extrema (#1)", allow_skip=True, camera_slot="A", phase="CH"),

        # --- Salida C3: Anillo de Diamante, Perlas de Baily y recolocación de filtro ---
        EclipseEvent("C3", -2.5, "1/2000", "100", "Anillo de Diamante salida", allow_skip=True, camera_slot="A", phase="DR"),
        EclipseEvent("C3", -1.5, "1/2000", "200", "Paisaje: Salida de umbra", allow_skip=True, camera_slot="B", phase="DR"),
        EclipseEvent("C3", -0.5, "1/2000", "100", "Diamante destello final", allow_skip=True, camera_slot="A", phase="DR"),
        EclipseEvent("C3", +0.5, "1/4000", "100", "Baily Beads salida inicio (Ráfaga)", allow_skip=True, camera_slot="A", phase="BB"),
        EclipseEvent("C3", +1.5, "1/4000", "100", "Baily Beads salida centro", allow_skip=True, camera_slot="A", phase="BB"),
        EclipseEvent("C3", +2.5, "1/4000", "100", "Baily Beads salida fin valles", allow_skip=True, camera_slot="A", phase="BB"),
        EclipseEvent("C3", +5.0, "1/4000", "100", "Aviso: ¡Colocar filtro solar inmediatamente!", allow_skip=False, camera_slot="A", phase="DR"),
        EclipseEvent("C3", +15.0, "1/4000", "100", "Parcial post-C3 (Con filtro solar)", allow_skip=False, camera_slot="A"),
        EclipseEvent("C3", +60.0, "1/4000", "100", "Parcial post-C3 (+1 min)", allow_skip=True, camera_slot="A"),
    ]
    return assign_event_metadata(events)


def get_eclipse_test_preset() -> List[EclipseEvent]:
    """
    Modo de prueba rápida 'ECLIPSE_TEST' (2 minutos 30 segundos de estrés de hardware).
    Emula C2-60s, 60 segundos de totalidad con 2 ráfagas completas de HDR + ventana de vaciado de búfer,
    y 30 segundos post-C3, con perlas de Baily en alta cadencia a 1/4000s y avisos de filtro.
    """
    events = [
        # --- C2 - 60s a -15s: Preparación y Avisos ---
        EclipseEvent("C2", -60.0, "1/4000", "100", "ECLIPSE_TEST: Inicio y comprobación enlace SDK/PTP", allow_skip=False, camera_slot="A"),
        EclipseEvent("C2", -30.0, "1/4000", "100", "Aviso: Quedan 30 segundos, preparado para el filtro", allow_skip=False, camera_slot="A"),
        EclipseEvent("C2", -15.0, "1/4000", "100", "Aviso: ¡Quitar filtro solar ahora!", allow_skip=False, camera_slot="A"),
        EclipseEvent("C2", -5.0,  "1/4000", "100", "Parada preventiva de Live View", allow_skip=True, camera_slot="A"),
    ]

    # --- Baily Entrada: Ráfaga rápida de 18 tomas a 1/4000s, ISO 100 directas a SD ---
    for i in range(18):
        offset = -3.2 + (i * 0.08)  # de -3.2s a -1.84s (ráfaga continua a 14 fps)
        events.append(EclipseEvent("C2", round(offset, 2), "1/4000", "100", f"Baily Entrada Ráfaga #{i+1}", allow_skip=True, camera_slot="A", phase="BB"))

    # Anillo de Diamante Entrada: 2 tomas en Single Mode a 1/2000s espaciadas limpiamente
    events.append(EclipseEvent("C2", -1.0, "1/2000", "100", "Anillo de Diamante entrada", allow_skip=True, camera_slot="A", phase="DR"))
    events.append(EclipseEvent("C2", -0.2, "1/2000", "100", "Diamante destello fotosférico", allow_skip=True, camera_slot="A", phase="DR"))

    # --- TOTALIDAD: 60s (C2 a C3) ---
    # Ráfaga HDR 1 (9 pasos EV)
    hdr1 = [
        (+2.0, "1/8000", "HDR 1: Cromosfera (#1)"),
        (+4.0, "1/4000", "HDR 1: Protuberancias (#2)"),
        (+6.0, "1/1250", "HDR 1: Corona interna (#3)"),
        (+8.0, "1/400",  "HDR 1: Penachos polares (#4)"),
        (+10.5, "1/125", "HDR 1: Corona media anclaje (#5)"),
        (+13.0, "1/40",  "HDR 1: Corona media-externa (#6)"),
        (+15.5, "1/13",  "HDR 1: Corona externa (#7)"),
        (+18.0, "1/4",   "HDR 1: Streamers lejanos (#8)"),
        (+21.0, "1s",    "HDR 1: Brillo ceniciento / fondo (#9)"),
    ]
    for off, spd, desc in hdr1:
        events.append(EclipseEvent("C2", off, spd, "100", desc, allow_skip=True, camera_slot="A", phase="PR"))

    # Ventana de Vaciado de Búfer SD (10 segundos)
    events.append(EclipseEvent("C2", +26.0, "1/125", "100", "Vaciado búfer SD y descanso térmico", allow_skip=True, camera_slot="A", phase="PR"))

    # Ráfaga HDR 2 Invertido (9 pasos EV)
    hdr2 = [
        (+33.0, "1s",    "HDR 2: Brillo ceniciento (#9)"),
        (+35.5, "1/4",   "HDR 2: Streamers lejanos (#8)"),
        (+37.5, "1/13",  "HDR 2: Corona externa (#7)"),
        (+39.5, "1/40",  "HDR 2: Corona media-externa (#6)"),
        (+41.5, "1/125", "HDR 2: Corona media anclaje (#5)"),
        (+43.5, "1/400", "HDR 2: Penachos polares (#4)"),
        (+45.5, "1/1250", "HDR 2: Corona interna (#3)"),
        (+47.5, "1/4000", "HDR 2: Protuberancias (#2)"),
        (+49.5, "1/8000", "HDR 2: Cromosfera (#1)"),
    ]
    for off, spd, desc in hdr2:
        events.append(EclipseEvent("C2", off, spd, "100", desc, allow_skip=True, camera_slot="A", phase="PR"))

    # Anillo Diamante Salida: 2 tomas en Single Mode a 1/2000s espaciadas para evitar colisión
    events.append(EclipseEvent("C3", -2.2, "1/2000", "100", "Diamante salida destello", allow_skip=True, camera_slot="A", phase="DR"))
    events.append(EclipseEvent("C3", -1.2, "1/2000", "100", "Diamante Salida", allow_skip=True, camera_slot="A", phase="DR"))

    # --- Baily Salida: Ráfaga rápida de 18 tomas a 1/4000s, ISO 100 directas a SD ---
    for i in range(18):
        offset = +0.5 + (i * 0.08)  # de +0.5s a +1.86s
        events.append(EclipseEvent("C3", round(offset, 2), "1/4000", "100", f"Baily Salida Ráfaga #{i+1}", allow_skip=True, camera_slot="A", phase="BB"))

    # Post-C3: Alerta filtro y cierre
    events.extend([
        EclipseEvent("C3", +5.0,  "1/4000", "100", "Aviso: ¡Colocar filtro solar inmediatamente!", allow_skip=False, camera_slot="A", phase="DR"),
        EclipseEvent("C3", +12.0, "1/4000", "100", "Parcial post-C3 (Con filtro solar)", allow_skip=True, camera_slot="A"),
        EclipseEvent("C3", +25.0, "1/4000", "100", "Fin de ECLIPSE_TEST / Reporte telemetría", allow_skip=False, camera_slot="A"),
    ])

    return assign_event_metadata(events)


def get_full_rehearsal_preset() -> List[EclipseEvent]:
    """
    Simulacro Real Completo (C2 - 5 min hasta C3 + 5 min).
    Cubre la rutina completa de campo: fotos parciales con filtro, avisos sonoros
    a -30s y -15s, perlas de Baily, totalidad de duración real con ciclos HDR y salida con filtro.
    """
    events = [
        EclipseEvent("C2", -600.0, "1/4000", "100", "Alerta: 10 minutos para C2. Comprobar y fijar enfoque en cámara principal", allow_skip=False, camera_slot="A"),
        EclipseEvent("C2", -300.0, "1/4000", "100", "Parcial con filtro solar (C2 - 5 min)", allow_skip=True, camera_slot="A"),
        EclipseEvent("C2", -240.0, "1/4000", "100", "Parcial con filtro solar (C2 - 4 min)", allow_skip=True, camera_slot="A"),
        EclipseEvent("C2", -180.0, "1/4000", "100", "Parcial con filtro solar (C2 - 3 min)", allow_skip=True, camera_slot="A"),
        EclipseEvent("C2", -120.0, "1/4000", "100", "Parcial con filtro solar (C2 - 2 min)", allow_skip=True, camera_slot="A"),
        EclipseEvent("C2", -60.0,  "1/4000", "100", "Parcial con filtro solar (C2 - 1 min)", allow_skip=True, camera_slot="A"),
        EclipseEvent("C2", -30.0,  "1/4000", "100", "Aviso: Quedan 30 segundos, preparado para el filtro", allow_skip=False, camera_slot="A"),
        EclipseEvent("C2", -15.0,  "1/4000", "100", "Aviso: ¡Quitar filtro solar ahora!", allow_skip=False, camera_slot="A"),
        EclipseEvent("C2", -5.0,   "1/4000", "100", "Parada preventiva de Live View", allow_skip=True, camera_slot="A"),
    ]

    # Baily Entrada (18 disparos)
    for i in range(18):
        offset = -4.0 + (i * 0.19)
        events.append(EclipseEvent("C2", round(offset, 2), "1/4000", "100", f"Baily Entrada #{i+1}", allow_skip=True, camera_slot="A", phase="BB"))

    events.append(EclipseEvent("C2", -0.2, "1/2000", "100", "Diamante Entrada", allow_skip=True, camera_slot="A", phase="DR"))

    # Totalidad: 2 ciclos HDR completos
    hdr_steps = [
        (+2.0, "1/8000", "HDR 1: Cromosfera (#1)"),
        (+4.5, "1/4000", "HDR 1: Protuberancias (#2)"),
        (+7.0, "1/1250", "HDR 1: Corona interna (#3)"),
        (+9.5, "1/400",  "HDR 1: Penachos polares (#4)"),
        (+12.0, "1/125", "HDR 1: Corona media anclaje (#5)"),
        (+15.0, "1/40",  "HDR 1: Corona media-externa (#6)"),
        (+18.0, "1/13",  "HDR 1: Corona externa (#7)"),
        (+21.5, "1/4",   "HDR 1: Streamers lejanos (#8)"),
        (+25.0, "1s",    "HDR 1: Brillo ceniciento (#9)"),
    ]
    for off, spd, desc in hdr_steps:
        events.append(EclipseEvent("C2", off, spd, "100", desc, allow_skip=True, camera_slot="A", phase="PR"))

    events.append(EclipseEvent("C2", +30.0, "1/125", "100", "Vaciado búfer SD", allow_skip=True, camera_slot="A", phase="PR"))

    hdr_inv = [
        (+38.0, "1s",    "HDR 2: Brillo ceniciento (#9)"),
        (+41.0, "1/4",   "HDR 2: Streamers lejanos (#8)"),
        (+43.5, "1/13",  "HDR 2: Corona externa (#7)"),
        (+46.0, "1/40",  "HDR 2: Corona media-externa (#6)"),
        (+48.5, "1/125", "HDR 2: Corona media anclaje (#5)"),
        (+51.0, "1/400", "HDR 2: Penachos polares (#4)"),
        (+53.5, "1/1250", "HDR 2: Corona interna (#3)"),
        (+56.0, "1/4000", "HDR 2: Protuberancias (#2)"),
        (+58.0, "1/8000", "HDR 2: Cromosfera (#1)"),
    ]
    for off, spd, desc in hdr_inv:
        events.append(EclipseEvent("C2", off, spd, "100", desc, allow_skip=True, camera_slot="A", phase="PR"))

    events.append(EclipseEvent("C3", -2.0, "1/2000", "100", "Diamante Salida", allow_skip=True, camera_slot="A", phase="DR"))

    # Baily Salida (18 disparos)
    for i in range(18):
        offset = +0.5 + (i * 0.19)
        events.append(EclipseEvent("C3", round(offset, 2), "1/4000", "100", f"Baily Salida #{i+1}", allow_skip=True, camera_slot="A", phase="BB"))

    events.extend([
        EclipseEvent("C3", +5.0,   "1/4000", "100", "Aviso: ¡Colocar filtro solar inmediatamente!", allow_skip=False, camera_slot="A", phase="DR"),
        EclipseEvent("C3", +60.0,  "1/4000", "100", "Parcial con filtro solar (C3 + 1 min)", allow_skip=True, camera_slot="A"),
        EclipseEvent("C3", +120.0, "1/4000", "100", "Parcial con filtro solar (C3 + 2 min)", allow_skip=True, camera_slot="A"),
        EclipseEvent("C3", +180.0, "1/4000", "100", "Parcial con filtro solar (C3 + 3 min)", allow_skip=True, camera_slot="A"),
        EclipseEvent("C3", +240.0, "1/4000", "100", "Parcial con filtro solar (C3 + 4 min)", allow_skip=True, camera_slot="A"),
        EclipseEvent("C3", +300.0, "1/4000", "100", "Parcial con filtro solar (C3 + 5 min / Fin)", allow_skip=True, camera_slot="A"),
    ])

    return assign_event_metadata(events)


def get_lunar_eclipse_bracket_preset() -> List[EclipseEvent]:
    """Secuencia de horquillado HDR para eclipse lunar (fase umbral / totalidad roja)."""
    events = [
        EclipseEvent("U2", +0.0, "1/250",  "100", "Luna: Borde brillante", allow_skip=True, camera_slot="A"),
        EclipseEvent("U2", +3.0, "1/60",   "200", "Luna: Umbra superficial", allow_skip=True, camera_slot="A"),
        EclipseEvent("U2", +7.0, "1/8",    "400", "Luna: Umbra media", allow_skip=True, camera_slot="A"),
        EclipseEvent("U2", +12.0, "1s",    "800", "Luna: Totalidad roja (Blood Moon)", allow_skip=True, camera_slot="A"),
        EclipseEvent("U2", +18.0, "4s",   "1600", "Luna: Fondo estelar y umbra profunda", allow_skip=True, camera_slot="A"),
    ]
    return assign_event_metadata(events)


def get_quick_rehearsal_preset() -> List[EclipseEvent]:
    """Secuencia rápida de 12 segundos para pruebas de campo inmediatas y verificación de interfaz."""
    events = [
        EclipseEvent("C2", -4.0, "1/4000", "100", "Simulacro: Baily Beads", camera_slot="A", phase="BB"),
        EclipseEvent("C2", -3.0, "1/1000", "200", "Simulacro: Paisaje angular", camera_slot="B", phase="BB"),
        EclipseEvent("C2", -2.0, "1/1000", "100", "Simulacro: Diamante entrada", camera_slot="A", phase="DR"),
        EclipseEvent("C2", +1.0, "1/250",  "100", "Simulacro: Corona interna", camera_slot="A", phase="CH"),
        EclipseEvent("C2", +2.0, "1/500",  "200", "Simulacro: Paisaje totalidad", camera_slot="B", phase="PR"),
        EclipseEvent("C2", +3.0, "1/60",   "100", "Simulacro: Corona media", camera_slot="A", phase="PR"),
        EclipseEvent("C2", +5.5, "1/4",    "200", "Simulacro: Corona externa", camera_slot="A", phase="PR"),
        EclipseEvent("C2", +8.5, "1s",     "400", "Simulacro: Corona tenue", camera_slot="A", phase="PR"),
        EclipseEvent("C3", -1.0, "1/2000", "100", "Simulacro: Diamante salida", camera_slot="A", phase="DR"),
        EclipseEvent("C3", +0.5, "1/1000", "200", "Simulacro: Salida paisaje", camera_slot="B", phase="DR"),
    ]
    return assign_event_metadata(events)


def get_bkt_hardware_preset() -> List[EclipseEvent]:
    """
    Simulacro con Horquillado AE Bracketing por Hardware (7 tomas a 1.7 EV por ráfaga).
    Aprovecha la capacidad de ráfaga y búfer de la Nikon Z5 II disparando 3 bloques HDR
    completos en ráfaga continua nativa durante la totalidad de 60 segundos.
    """
    events = [
        # --- Pre-C2 ---
        EclipseEvent("C2", -60.0, "1/4000", "100", "BKT_TEST: Comprobación enlace SDK/PTP", allow_skip=False, camera_slot="A"),
        EclipseEvent("C2", -30.0, "1/4000", "100", "Aviso: Quedan 30 segundos, preparado para el filtro", allow_skip=False, camera_slot="A"),
        EclipseEvent("C2", -15.0, "1/4000", "100", "Aviso: ¡Quitar filtro solar ahora!", allow_skip=False, camera_slot="A"),
        EclipseEvent("C2", -5.0,  "1/4000", "100", "Parada preventiva de Live View", allow_skip=True, camera_slot="A"),
    ]

    # Baily Entrada (14 tomas Continuous High RAW a 1/4000s, despejando 1.0s antes de Diamante)
    for i in range(14):
        offset = -4.2 + (i * 0.12)
        events.append(EclipseEvent("C2", round(offset, 2), "1/4000", "100", f"Baily Entrada Ráfaga #{i+1}", allow_skip=True, camera_slot="A", phase="BB"))

    # Anillo de Diamante Entrada (Single Mode a 1/2000s con margen limpio)
    events.extend([
        EclipseEvent("C2", -1.0, "1/2000", "100", "Anillo de Diamante entrada", allow_skip=True, camera_slot="A", phase="DR"),
        EclipseEvent("C2", -0.2, "1/2000", "100", "Diamante destello fotosférico", allow_skip=True, camera_slot="A", phase="DR"),
    ])

    # TOTALIDAD (60s): 3 Ráfagas AE Bracketing por Hardware de 7 tomas a 1.7 EV (base 1/100s)
    events.extend([
        # Ráfaga HDR 1 (C2 + 4.0s)
        EclipseEvent("C2", +4.0,  "1/100", "100", "HDR 1: Horquillado Corona 7 tomas (1.7 EV BKT Hardware)", allow_skip=True, camera_slot="A", phase="HDR_BKT", burst_count=7),
        EclipseEvent("C2", +12.0, "1/125", "100", "Vaciado búfer SD y monitor térmico #1", allow_skip=True, camera_slot="A", phase="PARCIAL"),

        # Ráfaga HDR 2 (C2 + 25.0s)
        EclipseEvent("C2", +25.0, "1/100", "100", "HDR 2: Horquillado Corona 7 tomas (1.7 EV BKT Hardware)", allow_skip=True, camera_slot="A", phase="HDR_BKT", burst_count=7),
        EclipseEvent("C2", +33.0, "1/125", "100", "Vaciado búfer SD y monitor térmico #2", allow_skip=True, camera_slot="A", phase="PARCIAL"),

        # Ráfaga HDR 3 (C2 + 45.0s)
        EclipseEvent("C2", +45.0, "1/100", "100", "HDR 3: Horquillado Corona 7 tomas (1.7 EV BKT Hardware)", allow_skip=True, camera_slot="A", phase="HDR_BKT", burst_count=7),
        EclipseEvent("C2", +53.0, "1/125", "100", "Preparación salida C3 y vaciado búfer", allow_skip=True, camera_slot="A", phase="PARCIAL"),
    ])

    # Anillo Diamante Salida (Single Mode a 1/2000s espaciadas)
    events.extend([
        EclipseEvent("C3", -2.2, "1/2000", "100", "Diamante salida destello", allow_skip=True, camera_slot="A", phase="DR"),
        EclipseEvent("C3", -1.2, "1/2000", "100", "Anillo de Diamante salida", allow_skip=True, camera_slot="A", phase="DR"),
    ])

    # Baily Salida (14 tomas Continuous High RAW a 1/4000s)
    for i in range(14):
        offset = +0.5 + (i * 0.12)
        events.append(EclipseEvent("C3", round(offset, 2), "1/4000", "100", f"Baily Salida Ráfaga #{i+1}", allow_skip=True, camera_slot="A", phase="BB"))

    # Post-C3
    events.extend([
        EclipseEvent("C3", +5.0,  "1/4000", "100", "Aviso: ¡Colocar filtro solar inmediatamente!", allow_skip=False, camera_slot="A", phase="DR"),
        EclipseEvent("C3", +12.0, "1/4000", "100", "Parcial post-C3 (Con filtro solar)", allow_skip=True, camera_slot="A"),
        EclipseEvent("C3", +25.0, "1/4000", "100", "Fin de BKT_TEST / Reporte telemetría", allow_skip=False, camera_slot="A"),
    ])
    return assign_event_metadata(events)


def get_solar_eclipse_annular_preset() -> List[EclipseEvent]:
    """
    Secuencia optimizada para Eclipse Solar Anular (ej: 26 de enero de 2028).
    CRÍTICO PARA SEGURIDAD: En eclipses anulares la fotosfera solar NUNCA queda totalmente cubierta.
    El filtro solar (ND 5.0 / Baader Solar Safety Film) DEBE PERMANECER COLOCADO en todos los objetivos
    y telescopios durante TODAS las fases del eclipse (C1 a C4, incluyendo la anularidad).
    Todas las tomas se calibran para filtro solar a f/8 ISO 100 (1/1000s - 1/4000s).
    """
    events = [
        # --- Pre-C2: Enfoque y parciales con filtro solar ---
        EclipseEvent("C2", -600.0, "1/4000", "100", "Alerta: 10 minutos para C2. Comprobar y fijar enfoque con filtro solar", allow_skip=False, camera_slot="A"),
        EclipseEvent("C2", -120.0, "1/4000", "100", "Parcial con filtro solar (C2 - 2 min)", allow_skip=True, camera_slot="A"),
        EclipseEvent("C2", -60.0,  "1/4000", "100", "Parcial fina pre-C2 (Con filtro solar)", allow_skip=True, camera_slot="A"),

        # --- Avisos de seguridad: Recordatorio explícito de MANTENER el filtro ---
        EclipseEvent("C2", -30.0, "1/4000", "100", "Aviso de seguridad: Mantener filtro solar colocado. En eclipse anular nunca debe retirarse", allow_skip=False, camera_slot="A"),
        EclipseEvent("C2", -15.0, "1/4000", "100", "Aviso: Confirmar filtro solar asegurado en todos los objetivos", allow_skip=False, camera_slot="A"),
        EclipseEvent("C2", -5.0,  "1/4000", "100", "Parada preventiva de Live View", allow_skip=True, camera_slot="A"),

        # --- Ventana C2: Baily Beads y formación del Anillo de Fuego (con filtro solar) ---
        EclipseEvent("C2", -4.0, "1/4000", "100", "Baily Beads entrada anular (Ráfaga)", allow_skip=True, camera_slot="A", phase="BB"),
        EclipseEvent("C2", -3.0, "1/4000", "100", "Baily Beads entrada pico interno", allow_skip=True, camera_slot="A", phase="BB"),
        EclipseEvent("C2", -2.0, "1/4000", "100", "Baily Beads fin valles", allow_skip=True, camera_slot="A", phase="BB"),
        EclipseEvent("C2", -1.0, "1/2000", "100", "C2: Cierre completo del anillo (Entrada Anularidad)", allow_skip=True, camera_slot="A", phase="DR"),
        EclipseEvent("C2", -0.2, "1/2000", "100", "Anillo de Fuego inicio con filtro solar", allow_skip=True, camera_slot="A", phase="DR"),

        # --- FASE ANULAR: Anillo de Fuego continuo con filtro solar (f/8 ISO 100) ---
        EclipseEvent("C2", +2.0,  "1/4000", "100", "Anillo de Fuego: Borde interno fotosférico (#1)", allow_skip=True, camera_slot="A", phase="PR"),
        EclipseEvent("C2", +5.0,  "1/2000", "100", "Anillo de Fuego: Detalle fotosfera y manchas (#2)", allow_skip=True, camera_slot="A", phase="PR"),
        EclipseEvent("C2", +8.5,  "1/1000", "100", "Anillo de Fuego: Exposición completa del anillo (#3)", allow_skip=True, camera_slot="A", phase="PR"),
        EclipseEvent("C2", +12.0, "1/2000", "100", "Anillo de Fuego: Monitoreo simetría (#4)", allow_skip=True, camera_slot="A", phase="PR"),
        EclipseEvent("C2", +16.0, "1/4000", "100", "Anillo de Fuego: Alta velocidad limbo lunar (#5)", allow_skip=True, camera_slot="A", phase="PR"),

        # Ventana de descanso térmico y vaciado de búfer SD
        EclipseEvent("C2", +22.0, "1/2000", "100", "Vaciado búfer SD y monitor térmico", allow_skip=True, camera_slot="A", phase="PR"),

        # Segundo ciclo de anularidad
        EclipseEvent("C2", +28.0, "1/1000", "100", "Anillo de Fuego: Máxima anularidad simétrica (#6)", allow_skip=True, camera_slot="A", phase="PR"),
        EclipseEvent("C2", +34.0, "1/2000", "100", "Anillo de Fuego: Simetría de anillo (#7)", allow_skip=True, camera_slot="A", phase="PR"),
        EclipseEvent("C2", +40.0, "1/4000", "100", "Anillo de Fuego: Detalle perfil montañas (#8)", allow_skip=True, camera_slot="A", phase="PR"),
        EclipseEvent("C2", +46.0, "1/2000", "100", "Anillo de Fuego: Desplazamiento hacia limbo de salida (#9)", allow_skip=True, camera_slot="A", phase="PR"),
        EclipseEvent("C2", +52.0, "1/2000", "100", "Anillo de Fuego: Pre-salida C3 (#10)", allow_skip=True, camera_slot="A", phase="PR"),

        # --- Salida C3: Ruptura del anillo y Perlas de Baily (con filtro solar) ---
        EclipseEvent("C3", -2.0, "1/2000", "100", "Anillo de Fuego: Ruptura del anillo de salida", allow_skip=True, camera_slot="A", phase="DR"),
        EclipseEvent("C3", -1.0, "1/2000", "100", "Anillo de Fuego destello final con filtro", allow_skip=True, camera_slot="A", phase="DR"),
        EclipseEvent("C3", +0.5, "1/4000", "100", "Baily Beads salida inicio (Con filtro solar)", allow_skip=True, camera_slot="A", phase="BB"),
        EclipseEvent("C3", +1.5, "1/4000", "100", "Baily Beads salida centro", allow_skip=True, camera_slot="A", phase="BB"),
        EclipseEvent("C3", +2.5, "1/4000", "100", "Baily Beads salida fin valles", allow_skip=True, camera_slot="A", phase="BB"),
        EclipseEvent("C3", +5.0, "1/4000", "100", "Aviso: Fin de anularidad. Mantener filtro solar colocado", allow_skip=False, camera_slot="A", phase="DR"),
        EclipseEvent("C3", +15.0, "1/4000", "100", "Parcial post-C3 (Con filtro solar)", allow_skip=False, camera_slot="A"),
        EclipseEvent("C3", +60.0, "1/4000", "100", "Parcial post-C3 (+1 min con filtro)", allow_skip=True, camera_slot="A"),
    ]
    return assign_event_metadata(events)
