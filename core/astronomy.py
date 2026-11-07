"""
Motor Astronómico y Evaluador de Contactos Locales para eclipZe v2.0.
Calcula visibilidad local, porcentaje de oscurecimiento, instantes C1-C4,
duración de totalidad, posición solar (altitud/azimut) y corrección topográfica por altitud.
"""

import math
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional, Dict, Tuple, Any, List
from .eclipse_db import EclipseInfo


@dataclass
class LocalEclipseResult:
    """Resultado del cálculo astronómico para una ubicación geográfica concreta."""
    eclipse_id: str
    lat: float
    lon: float
    alt_m: float
    visibility: str          # "totality", "annularity", "partial", "none"
    is_visible: bool
    obscuration_pct: float   # 0.0 a 100.0 %
    magnitude: float         # Ej: 1.03 para totalidad, 0.94 para anular, 0.85 para parcial
    c1_utc: Optional[float]  # Timestamp epoch UTC (segundos)
    c2_utc: Optional[float]  # None si no hay totalidad/anularidad
    max_utc: Optional[float]
    c3_utc: Optional[float]  # None si no hay totalidad/anularidad
    c4_utc: Optional[float]
    totality_duration_s: float
    sun_altitude_deg: float  # Altura sobre el horizonte en el instante MAX
    sun_azimuth_deg: float   # Azimut en el instante MAX (0° N, 90° E, 180° S, 270° W)
    alt_correction_s: float  # Adelanto de C2 por altitud topográfica (segundos)
    c1_iso: str = ""
    c2_iso: str = ""
    max_iso: str = ""
    c3_iso: str = ""
    c4_iso: str = ""
    description: str = ""

    def to_contacts_dict(self) -> Dict[str, float]:
        """Convierte los contactos a diccionario compatible con EclipseSequencer y Timeline."""
        contacts: Dict[str, float] = {}
        if self.c1_utc is not None:
            contacts["C1"] = self.c1_utc
        if self.c2_utc is not None:
            contacts["C2"] = self.c2_utc
            contacts["U2"] = self.c2_utc  # Alias lunar
        if self.max_utc is not None:
            contacts["MAX"] = self.max_utc
        if self.c3_utc is not None:
            contacts["C3"] = self.c3_utc
            contacts["U3"] = self.c3_utc  # Alias lunar
        if self.c4_utc is not None:
            contacts["C4"] = self.c4_utc
        return contacts

    @property
    def formatted_totality(self) -> str:
        if self.totality_duration_s <= 0:
            return "0s"
        total = int(round(self.totality_duration_s))
        m = total // 60
        s = total % 60
        if m > 0:
            return f"{m}m {s:02d}s"
        return f"{s}s"

    @property
    def visibility_label(self) -> str:
        if self.visibility == "totality":
            return "Totalidad Visible"
        elif self.visibility == "annularity":
            return "Anularidad Visible"
        elif self.visibility == "partial":
            return f"Parcial ({self.obscuration_pct:.1f}%)"
        return "No Visible"

    @property
    def badge_color(self) -> str:
        if self.visibility == "totality":
            return "#A855F7"  # Púrpura totalidad
        elif self.visibility == "annularity":
            return "#F59E0B"  # Oro anular
        elif self.visibility == "partial":
            return "#38BDF8"  # Azul parcial
        return "#6B7280"      # Gris no visible


def calculate_solar_position(dt_utc: datetime, lat: float, lon: float) -> Tuple[float, float]:
    """
    Calcula la altitud y azimut del Sol en grados para una fecha/hora UTC y coordenadas.
    Algoritmo estándar de Jean Meeus (Astronomical Algorithms).
    """
    y, m, d = dt_utc.year, dt_utc.month, dt_utc.day
    h = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0 + dt_utc.microsecond / 3600000000.0
    if m <= 2:
        y -= 1
        m += 12
    a = math.floor(y / 100)
    b = 2 - a + math.floor(a / 4)
    jd = math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + h / 24.0 + b - 1524.5
    t = (jd - 2451545.0) / 36525.0

    l0 = math.radians((280.46646 + 36000.76983 * t + 0.0003032 * t**2) % 360.0)
    m_anom = math.radians((357.52911 + 35999.05029 * t - 0.0001537 * t**2) % 360.0)
    c = math.radians(
        (1.914602 - 0.004817 * t) * math.sin(m_anom)
        + (0.019993 - 0.000101 * t) * math.sin(2 * m_anom)
        + 0.000289 * math.sin(3 * m_anom)
    )
    sun_lon = l0 + c
    eps = math.radians(23.439291 - 0.0130042 * t)

    sin_dec = math.sin(eps) * math.sin(sun_lon)
    dec = math.asin(max(-1.0, min(1.0, sin_dec)))
    ra = math.atan2(math.cos(eps) * math.sin(sun_lon), math.cos(sun_lon))

    # GMST
    theta0 = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * t**2 - t**3 / 38710000.0
    gmst = math.radians(theta0 % 360.0)
    lmst = gmst + math.radians(lon)
    ha = lmst - ra

    phi = math.radians(lat)
    sin_alt = math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.cos(ha)
    alt = math.asin(max(-1.0, min(1.0, sin_alt)))

    az = math.degrees(math.atan2(-math.sin(ha), math.cos(phi) * math.tan(dec) - math.sin(phi) * math.cos(ha))) % 360.0
    return math.degrees(alt), az


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia ortodrómica sobre la superficie terrestre (WGS84 aproximado R=6371km)."""
    r_earth = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    return 2.0 * r_earth * math.asin(math.sqrt(max(0.0, min(1.0, a))))


def project_point_to_segment(
    lat: float, lon: float,
    lat1: float, lon1: float,
    lat2: float, lon2: float
) -> Tuple[float, float, float, float]:
    """
    Proyecta ortogonalmente un punto (lat, lon) sobre un segmento lineal de la trayectoria.
    Devuelve: (distancia_km, factor_interpolacion_t, lat_proy, lon_proy)
    """
    lat_mid = math.radians((lat1 + lat2) / 2.0)
    cos_lat = max(0.05, math.cos(lat_mid))

    dx = (lon2 - lon1) * cos_lat
    dy = lat2 - lat1
    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq <= 1e-12:
        d = haversine_distance_km(lat, lon, lat1, lon1)
        return d, 0.0, lat1, lon1

    px = (lon - lon1) * cos_lat
    py = lat - lat1
    t = max(0.0, min(1.0, (px * dx + py * dy) / seg_len_sq))

    proj_lat = lat1 + t * (lat2 - lat1)
    proj_lon = lon1 + t * (lon2 - lon1)
    dist_km = haversine_distance_km(lat, lon, proj_lat, proj_lon)
    return dist_km, t, proj_lat, proj_lon


def point_in_polygon(lat: float, lon: float, polygon: List[List[float]]) -> bool:
    """Algoritmo Ray-Casting (Jordan Curve) para comprobar si (lat, lon) está dentro del polígono geodésico."""
    if not polygon or len(polygon) < 3:
        return False
    n = len(polygon)
    if polygon[0][0] == polygon[-1][0] and polygon[0][1] == polygon[-1][1]:
        n -= 1
        if n < 3:
            return False
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i][1], polygon[i][0]  # lon, lat
        xj, yj = polygon[j][1], polygon[j][0]
        if ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def min_distance_to_polyline(lat: float, lon: float, polyline: List[List[float]]) -> float:
    """Calcula la distancia geodésica mínima (km) desde (lat, lon) hasta una polilínea."""
    if not polyline or len(polyline) < 2:
        return float("inf")
    min_d = float("inf")
    for i in range(len(polyline) - 1):
        p1 = polyline[i]
        p2 = polyline[i + 1]
        dist, _, _, _ = project_point_to_segment(lat, lon, p1[0], p1[1], p2[0], p2[1])
        if dist < min_d:
            min_d = dist
    return min_d


def _iso_from_epoch(epoch_sec: Optional[float]) -> str:
    """Convierte epoch seconds en formato legible 'HH:MM:SS UTC'."""
    if epoch_sec is None:
        return "--:--:--"
    dt = datetime.fromtimestamp(epoch_sec, tz=timezone.utc)
    return dt.strftime("%H:%M:%S UTC")


def calculate_local_eclipse(
    eclipse: EclipseInfo,
    lat: float,
    lon: float,
    alt_m: float = 0.0
) -> LocalEclipseResult:
    """
    Evalúa las condiciones locales de un eclipse para un observador en (lat, lon, alt_m).
    
    Calcula:
    - Visibilidad local (totalidad/anularidad, parcial o no visible)
    - Porcentaje de oscurecimiento local (%) y magnitud
    - Instantes de contacto calculados en UTC: C1, C2, MAX, C3, C4
    - Duración de la totalidad (C3 - C2)
    - Elevación solar y azimut en el instante MAX
    - Corrección topográfica por altitud (0.5s - 1.5s de adelanto de C2 a 2000m)
    """
    # 0. Manejo específico para simulaciones de prueba
    if getattr(eclipse, "is_simulation", False) or eclipse.type == "simulation":
        now = datetime.now(timezone.utc).timestamp()
        c2 = now + 300.0  # T+5 min por defecto
        totality = eclipse.max_duration_s if eclipse.max_duration_s > 0 else 120.0
        c1 = c2 - 120.0
        c3 = c2 + totality
        c4 = c3 + 60.0
        max_t = c2 + (totality / 2.0)
        return LocalEclipseResult(
            eclipse_id=eclipse.id, lat=lat, lon=lon, alt_m=alt_m,
            visibility="totality", is_visible=True, obscuration_pct=100.0,
            magnitude=1.04,
            c1_utc=c1, c2_utc=c2, max_utc=max_t,
            c3_utc=c3, c4_utc=c4,
            totality_duration_s=totality,
            sun_altitude_deg=45.0, sun_azimuth_deg=180.0, alt_correction_s=0.0,
            c1_iso=_iso_from_epoch(c1),
            c2_iso=_iso_from_epoch(c2),
            max_iso=_iso_from_epoch(max_t),
            c3_iso=_iso_from_epoch(c3),
            c4_iso=_iso_from_epoch(c4),
            description="Modo Simulación: Banco de pruebas para ensayo general y validación de hardware."
        )

    # 1. Manejo específico para eclipses lunares
    if eclipse.is_lunar:
        return _calculate_local_lunar(eclipse, lat, lon, alt_m)

    # 2. Eclipse Solar: búsqueda de la mínima distancia a la franja central
    centerline = eclipse.centerline
    if not centerline:
        # Fallback sin datos de trayectoria
        return LocalEclipseResult(
            eclipse_id=eclipse.id, lat=lat, lon=lon, alt_m=alt_m,
            visibility="none", is_visible=False, obscuration_pct=0.0,
            magnitude=0.0, c1_utc=None, c2_utc=None, max_utc=None,
            c3_utc=None, c4_utc=None, totality_duration_s=0.0,
            sun_altitude_deg=0.0, sun_azimuth_deg=0.0, alt_correction_s=0.0,
            description="Sin datos de trayectoria para este eclipse."
        )

    best_dist = float("inf")
    best_t = 0.0
    best_seg_idx = 0
    best_time_sec = 0.0
    best_center_dur = eclipse.max_duration_s

    # Si hay un único punto en la trayectoria
    if len(centerline) == 1:
        p0 = centerline[0]
        d = haversine_distance_km(lat, lon, p0["lat"], p0["lon"])
        best_dist = d
        dt = datetime.fromisoformat(p0["utc_iso"].replace("Z", "+00:00"))
        best_time_sec = dt.timestamp()
        best_center_dur = p0.get("duration_s", eclipse.max_duration_s)
    else:
        # Proyectar sobre todos los segmentos adyacentes
        for i in range(len(centerline) - 1):
            p1 = centerline[i]
            p2 = centerline[i + 1]
            dist_km, t, plat, plon = project_point_to_segment(
                lat, lon, p1["lat"], p1["lon"], p2["lat"], p2["lon"]
            )
            if dist_km < best_dist:
                best_dist = dist_km
                best_t = t
                best_seg_idx = i

                # Parsear tiempos de los nodos extremos
                iso1 = p1.get("utc_iso")
                iso2 = p2.get("utc_iso")
                if iso1 and iso2:
                    t1 = datetime.fromisoformat(iso1.replace("Z", "+00:00")).timestamp()
                    t2 = datetime.fromisoformat(iso2.replace("Z", "+00:00")).timestamp()
                    best_time_sec = t1 + t * (t2 - t1)
                elif iso1 or iso2:
                    iso = iso1 or iso2
                    best_time_sec = datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
                elif best_time_sec == 0.0:
                    best_time_sec = datetime.fromisoformat(eclipse.date + "T12:00:00+00:00").timestamp()

                dur1 = p1.get("duration_s", eclipse.max_duration_s)
                dur2 = p2.get("duration_s", eclipse.max_duration_s)
                best_center_dur = dur1 + t * (dur2 - dur1)

    # 3. Dimensiones de la sombra
    path_half_width = max(10.0, eclipse.path_width_km / 2.0)
    penumbra_radius = max(path_half_width + 100.0, eclipse.penumbra_radius_km)

    # 4. Posición del Sol en el instante central
    dt_max = datetime.fromtimestamp(best_time_sec, tz=timezone.utc)
    sun_alt, sun_az = calculate_solar_position(dt_max, lat, lon)

    # 5. Corrección topográfica por altitud
    # A 2000m de altitud, el cono de sombra de la Luna toca la tierra ~1.0s antes (0.5s - 1.5s)
    alt_corr_s = (alt_m / 2000.0) * 1.0

    # 6. Clasificación de visibilidad local
    has_polygon = bool(eclipse.path_polygon or (eclipse.northern_limit and eclipse.southern_limit))
    is_in_path = False
    dist_outside = max(0.0, best_dist - path_half_width)

    if has_polygon:
        poly = eclipse.path_polygon if eclipse.path_polygon else (
            eclipse.northern_limit + list(reversed(eclipse.southern_limit))
        )
        is_in_path = point_in_polygon(lat, lon, poly)
        if not is_in_path:
            d_n = min_distance_to_polyline(lat, lon, eclipse.northern_limit) if eclipse.northern_limit else float("inf")
            d_s = min_distance_to_polyline(lat, lon, eclipse.southern_limit) if eclipse.southern_limit else float("inf")
            dist_outside = min(d_n, d_s)
    else:
        is_in_path = (best_dist <= path_half_width)

    if is_in_path and sun_alt > -1.0:
        # DENTRO DE LA FRANJA DE TOTALIDAD O ANULARIDAD
        is_totality = eclipse.is_total
        visibility = "totality" if is_totality else "annularity"
        is_visible = True

        # Reducción de duración por cuerda geométrica (distancia al centro)
        local_half_width = max(best_dist * 1.02, path_half_width)
        ratio = min(0.999, best_dist / local_half_width)
        chord_ratio = math.sqrt(max(0.05, 1.0 - ratio ** 2))
        base_dur = best_center_dur * chord_ratio
        
        # Corrección topográfica: C2 se adelanta
        totality_duration = max(0.5, base_dur + alt_corr_s)

        c2_utc = best_time_sec - (base_dur / 2.0) - alt_corr_s
        c3_utc = best_time_sec + (base_dur / 2.0)
        max_utc = best_time_sec

        # Fase parcial dura típicamente ~65-70 minutos antes y después
        partial_wing = 3900.0
        c1_utc = c2_utc - partial_wing
        c4_utc = c3_utc + partial_wing

        obscuration_pct = 100.0 if is_totality else 94.0
        dist_factor = max(0.0, 1.0 - ratio)
        magnitude = (1.0 + 0.04 * dist_factor) if is_totality else 0.94

        desc = (
            f"¡En la franja de {visibility}! Duración: {totality_duration:.1f}s. "
            f"Sol a {sun_alt:.1f}° azimut {sun_az:.0f}°."
        )

    elif (dist_outside <= (penumbra_radius - path_half_width) or best_dist <= penumbra_radius) and sun_alt > -5.0:
        # EN ZONA PARCIAL
        visibility = "partial"
        is_visible = True
        totality_duration = 0.0
        c2_utc = None
        c3_utc = None
        max_utc = best_time_sec

        # Proporción de distancia dentro de la penumbra
        pen_range = max(100.0, penumbra_radius - path_half_width)
        fraction = max(0.0, min(1.0, dist_outside / pen_range))

        # Oscurecimiento decae cuadráticamente desde el borde de totalidad
        obscuration_pct = max(0.1, (1.0 - fraction ** 0.85) * 100.0)
        magnitude = max(0.01, 1.0 - fraction)

        # Duración de fase parcial según cercanía
        wing = 3600.0 * math.sqrt(max(0.1, 1.0 - 0.7 * fraction))
        c1_utc = max_utc - wing
        c4_utc = max_utc + wing

        desc = (
            f"Eclipse parcial ({obscuration_pct:.1f}% oscurecimiento). "
            f"Fuera de franja central por {dist_outside:.0f} km."
        )

    else:
        # NO VISIBLE
        visibility = "none"
        is_visible = False
        obscuration_pct = 0.0
        magnitude = 0.0
        c1_utc = None
        c2_utc = None
        max_utc = None
        c3_utc = None
        c4_utc = None
        totality_duration = 0.0
        desc = "No visible desde esta ubicación geográfica o Sol bajo el horizonte."

    return LocalEclipseResult(
        eclipse_id=eclipse.id,
        lat=lat,
        lon=lon,
        alt_m=alt_m,
        visibility=visibility,
        is_visible=is_visible,
        obscuration_pct=round(obscuration_pct, 2),
        magnitude=round(magnitude, 4),
        c1_utc=c1_utc,
        c2_utc=c2_utc,
        max_utc=max_utc,
        c3_utc=c3_utc,
        c4_utc=c4_utc,
        totality_duration_s=round(totality_duration, 2),
        sun_altitude_deg=round(sun_alt, 2),
        sun_azimuth_deg=round(sun_az, 1),
        alt_correction_s=round(-alt_corr_s, 2),  # Negativo = adelanto
        c1_iso=_iso_from_epoch(c1_utc),
        c2_iso=_iso_from_epoch(c2_utc),
        max_iso=_iso_from_epoch(max_utc),
        c3_iso=_iso_from_epoch(c3_utc),
        c4_iso=_iso_from_epoch(c4_utc),
        description=desc
    )


def _calculate_local_lunar(
    eclipse: EclipseInfo,
    lat: float,
    lon: float,
    alt_m: float
) -> LocalEclipseResult:
    """Evalúa la visibilidad de un eclipse lunar en la ubicación indicada."""
    centerline = eclipse.centerline
    t0_sec = 0.0
    if centerline:
        dt = datetime.fromisoformat(centerline[0]["utc_iso"].replace("Z", "+00:00"))
        t0_sec = dt.timestamp()
    else:
        t0_sec = datetime.fromisoformat(eclipse.date + "T00:00:00+00:00").timestamp()

    # En un eclipse lunar, el Sol está opuesto a la Luna. La Luna está arriba si el Sol está bajo el horizonte.
    dt_max = datetime.fromtimestamp(t0_sec, tz=timezone.utc)
    sun_alt, sun_az = calculate_solar_position(dt_max, lat, lon)
    moon_alt = -sun_alt
    moon_az = (sun_az + 180.0) % 360.0

    dur_tot = eclipse.max_duration_s
    half_tot = dur_tot / 2.0

    if moon_alt > 0:
        # Luna visible sobre el horizonte durante el eclipse
        visibility = "totality" if eclipse.is_total else "partial"
        is_visible = True
        c2_utc = t0_sec - half_tot
        c3_utc = t0_sec + half_tot
        c1_utc = c2_utc - 3600.0
        c4_utc = c3_utc + 3600.0
        totality_dur = dur_tot
        obscuration_pct = 100.0
        magnitude = 1.2
        desc = f"Luna sobre el horizonte ({moon_alt:.1f}°). Eclipse lunar visible."
    else:
        visibility = "none"
        is_visible = False
        c1_utc = c2_utc = c3_utc = c4_utc = None
        totality_dur = 0.0
        obscuration_pct = 0.0
        magnitude = 0.0
        desc = "Luna bajo el horizonte durante el máximo del eclipse lunar."

    return LocalEclipseResult(
        eclipse_id=eclipse.id,
        lat=lat,
        lon=lon,
        alt_m=alt_m,
        visibility=visibility,
        is_visible=is_visible,
        obscuration_pct=obscuration_pct,
        magnitude=magnitude,
        c1_utc=c1_utc,
        c2_utc=c2_utc,
        max_utc=t0_sec,
        c3_utc=c3_utc,
        c4_utc=c4_utc,
        totality_duration_s=totality_dur,
        sun_altitude_deg=round(moon_alt, 2),  # Altura de la Luna para el observador
        sun_azimuth_deg=round(moon_az, 1),
        alt_correction_s=0.0,
        c1_iso=_iso_from_epoch(c1_utc),
        c2_iso=_iso_from_epoch(c2_utc),
        max_iso=_iso_from_epoch(t0_sec),
        c3_iso=_iso_from_epoch(c3_utc),
        c4_iso=_iso_from_epoch(c4_utc),
        description=desc
    )
