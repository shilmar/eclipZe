"""
Gestor de Catálogo de Eclipses (2026–2035) para eclipZe v2.0.
Carga, valida y filtra los grandes eventos astronómicos de la década con
especial foco en los eclipses de España (2026, 2027, 2028).
"""

import os
import json
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger("eclipZe.eclipse_db")


@dataclass
class EclipseInfo:
    """Modelo de datos unificado para eventos de eclipse."""
    id: str
    name: str
    date: str
    type: str  # "solar_total", "solar_annular", "solar_hybrid", "lunar_total", "lunar_partial"
    regions: List[str]
    max_duration_s: float
    path_width_km: float = 200.0
    penumbra_radius_km: float = 3000.0
    path_polygon: List[List[float]] = field(default_factory=list)
    northern_limit: List[List[float]] = field(default_factory=list)
    southern_limit: List[List[float]] = field(default_factory=list)
    centerline: List[Dict[str, Any]] = field(default_factory=list)
    besselian_elements: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    @property
    def is_solar(self) -> bool:
        return "solar" in self.type

    @property
    def is_total(self) -> bool:
        return "total" in self.type

    @property
    def is_annular(self) -> bool:
        return "annular" in self.type

    @property
    def is_lunar(self) -> bool:
        return "lunar" in self.type

    @property
    def is_simulation(self) -> bool:
        return self.type == "simulation"

    @property
    def type_label(self) -> str:
        labels = {
            "solar_total": "Solar Total",
            "solar_annular": "Solar Anular",
            "solar_hybrid": "Solar Híbrido",
            "lunar_total": "Lunar Total",
            "lunar_partial": "Lunar Parcial",
            "simulation": "SIMULACIÓN",
        }
        return labels.get(self.type, self.type.replace("_", " ").title())

    @property
    def badge_color(self) -> str:
        """Color oficial de badge según directrices eclipZe v2.0."""
        if self.is_simulation:
            return "#EF4444"       # Simulación: Rojo advertencia
        if self.is_lunar:
            return "#DC2626"       # Lunar: Rojo carmesí
        if self.is_annular:
            return "#F59E0B"       # Anular: Oro / Ámbar
        if self.is_total:
            return "#A855F7"       # Solar Total: Púrpura cósmico
        return "#38BDF8"           # Híbrido / Otro: Azul celeste

    @property
    def formatted_max_duration(self) -> str:
        total_sec = int(round(self.max_duration_s))
        minutes = total_sec // 60
        seconds = total_sec % 60
        if minutes > 0:
            return f"{minutes}m {seconds:02d}s"
        return f"{seconds}s"

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EclipseInfo":
        return cls(
            id=d.get("id", ""),
            name=d.get("name", ""),
            date=d.get("date", ""),
            type=d.get("type", "solar_total"),
            regions=d.get("regions", []),
            max_duration_s=float(d.get("max_duration_s", 0.0)),
            path_width_km=float(d.get("path_width_km", 200.0)),
            penumbra_radius_km=float(d.get("penumbra_radius_km", 3000.0)),
            path_polygon=d.get("path_polygon", []),
            northern_limit=d.get("northern_limit", []),
            southern_limit=d.get("southern_limit", []),
            centerline=d.get("centerline", []),
            besselian_elements=d.get("besselian_elements", {}),
            description=d.get("description", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "date": self.date,
            "type": self.type,
            "regions": self.regions,
            "max_duration_s": self.max_duration_s,
            "path_width_km": self.path_width_km,
            "penumbra_radius_km": self.penumbra_radius_km,
            "path_polygon": self.path_polygon,
            "northern_limit": self.northern_limit,
            "southern_limit": self.southern_limit,
            "centerline": self.centerline,
            "besselian_elements": self.besselian_elements,
            "description": self.description,
        }


class EclipseCatalogManager:
    """
    Gestor de base de datos de eclipses.
    Permite cargar data/eclipses.json, buscar, filtrar y evaluar visibilidad general.
    """

    def __init__(self, json_path: Optional[str] = None):
        self._eclipses: List[EclipseInfo] = []
        if json_path is None:
            # Buscar data/eclipses.json relativo a la raíz del proyecto
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            candidate = os.path.join(base_dir, "data", "eclipses.json")
            if os.path.exists(candidate):
                json_path = candidate
            else:
                json_path = "data/eclipses.json"

        self.json_path = json_path
        self.load_catalog(self.json_path)

    def load_catalog(self, path: str) -> bool:
        """Carga y valida el archivo JSON del catálogo."""
        if not os.path.exists(path):
            logger.warning(f"Catálogo de eclipses no encontrado en {path}. Usando lista vacía.")
            self._eclipses = []
            return False

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._eclipses = [EclipseInfo.from_dict(item) for item in data]
            # Ordenar por fecha cronológica
            self._eclipses.sort(key=lambda x: x.date)
            logger.info(f"Cargados {len(self._eclipses)} eclipses desde {path}.")
            return True
        except Exception as e:
            logger.error(f"Error parseando {path}: {e}")
            self._eclipses = []
            return False

    def get_all(self) -> List[EclipseInfo]:
        """Devuelve todos los eclipses registrados en el catálogo."""
        return list(self._eclipses)

    def get_by_id(self, eclipse_id: str) -> Optional[EclipseInfo]:
        """Busca un eclipse por su identificador único."""
        for e in self._eclipses:
            if e.id == eclipse_id:
                return e
        return None

    def filter_future(self, reference_date: Optional[str] = None) -> List[EclipseInfo]:
        """
        Filtra eventos futuros a partir de una fecha ISO ('YYYY-MM-DD').
        Por defecto toma la fecha actual.
        """
        if not reference_date:
            reference_date = datetime.now().strftime("%Y-%m-%d")
        return [e for e in self._eclipses if e.date >= reference_date]

    def filter_by_type(self, eclipse_type: str, reference_date: Optional[str] = None) -> List[EclipseInfo]:
        """Filtra por tipo ('solar_total', 'solar_annular', 'lunar_total', etc.)."""
        if eclipse_type == "all":
            events = list(self._eclipses)
        else:
            events = [e for e in self._eclipses if e.type == eclipse_type]
        if reference_date:
            events = [e for e in events if e.date >= reference_date]
        return events

    def filter_spain_eclipses(self, reference_date: Optional[str] = None) -> List[EclipseInfo]:
        """Devuelve los eclipses que cruzan España (2026 Total, 2027 Total, 2028 Anular, etc.)."""
        events = [e for e in self._eclipses if any("España" in r for r in e.regions)]
        if reference_date:
            events = [e for e in events if e.date >= reference_date]
        return events

    def search(self, query: str) -> List[EclipseInfo]:
        """Búsqueda por texto libre en nombre, regiones o descripción."""
        q = query.lower().strip()
        if not q:
            return list(self._eclipses)
        results = []
        for e in self._eclipses:
            match = (
                q in e.id.lower() or
                q in e.name.lower() or
                q in e.date or
                q in e.description.lower() or
                any(q in r.lower() for r in e.regions)
            )
            if match:
                results.append(e)
        return results
