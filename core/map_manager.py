"""
Gestor de mapas OpenStreetMap y servidor de teselas offline para eclipZe.
Permite descargar zonas cartográficas para su uso en campo sin conexión a internet,
almacenar la fecha de descarga/actualización y servir teselas a la interfaz Qt/Leaflet.
"""

import os
import json
import math
import time
import datetime
import threading
import urllib.request
import urllib.error
import http.server
import socketserver
from typing import Optional, Callable, Dict, Any, List, Tuple


OSM_TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
USER_AGENT = "eclipZe-Astronomy-App/1.0 (https://github.com/eclipze; contact: field@eclipze.local)"


def lat_lon_to_tile(lat_deg: float, lon_deg: float, zoom: int) -> Tuple[int, int]:
    """Convierte coordenadas geográficas a coordenadas de tesela Slippy Map."""
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile


def get_tiles_in_radius(
    lat: float,
    lon: float,
    radius_km: float,
    zoom_levels: List[int]
) -> List[Tuple[int, int, int]]:
    """Calcula la lista de teselas (z, x, y) necesarias para cubrir un radio en km."""
    tiles = []
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * max(0.01, math.cos(math.radians(lat))))

    for z in zoom_levels:
        n = 2.0 ** z
        x_min = int((lon - lon_delta + 180.0) / 360.0 * n)
        x_max = int((lon + lon_delta + 180.0) / 360.0 * n)
        lat_min_rad = math.radians(lat + lat_delta)
        lat_max_rad = math.radians(lat - lat_delta)
        y_min = int((1.0 - math.asinh(math.tan(lat_min_rad)) / math.pi) / 2.0 * n)
        y_max = int((1.0 - math.asinh(math.tan(lat_max_rad)) / math.pi) / 2.0 * n)
        y1, y2 = min(y_min, y_max), max(y_min, y_max)
        x1, x2 = min(x_min, x_max), max(x_min, x_max)

        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                tiles.append((z, x, y))
    return tiles


class MapTileManager:
    """Administra la caché local de teselas OSM en disco y sus metadatos."""

    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir is None:
            root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cache_dir = os.path.join(root, "maps_cache")
        self.cache_dir = cache_dir
        self.metadata_file = os.path.join(self.cache_dir, "metadata.json")
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_tile_path(self, z: int, x: int, y: int) -> str:
        return os.path.join(self.cache_dir, str(z), str(x), f"{y}.png")

    def has_tile(self, z: int, x: int, y: int) -> bool:
        return os.path.exists(self.get_tile_path(z, x, y))

    def get_tile_data(self, z: int, x: int, y: int) -> Optional[bytes]:
        """Obtiene la tesela: primero de disco; si no existe, la descarga y guarda si hay red."""
        path = self.get_tile_path(z, x, y)
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    return f.read()
            except Exception:
                pass

        # Intento de descarga al vuelo si no está en disco
        data = self._fetch_from_osm(z, x, y)
        if data:
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as f:
                    f.write(data)
            except Exception:
                pass
        return data

    def _fetch_from_osm(self, z: int, x: int, y: int, timeout: float = 3.0) -> Optional[bytes]:
        url = OSM_TILE_URL.format(z=z, x=x, y=y)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    return resp.read()
        except Exception:
            return None
        return None

    def get_metadata(self) -> Optional[Dict[str, Any]]:
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def save_metadata(self, data: Dict[str, Any]):
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def count_cached_tiles(self) -> Tuple[int, float]:
        """Cuenta el total de teselas en disco y calcula el tamaño en MB."""
        count = 0
        total_bytes = 0
        for root, _, files in os.walk(self.cache_dir):
            for file in files:
                if file.endswith(".png"):
                    count += 1
                    total_bytes += os.path.getsize(os.path.join(root, file))
        return count, round(total_bytes / (1024 * 1024), 2)

    def download_region(
        self,
        lat: float,
        lon: float,
        radius_km: float,
        zoom_levels: List[int],
        progress_cb: Optional[Callable[[int, int], None]] = None,
        stop_event: Optional[threading.Event] = None,
        zone_name: Optional[str] = None
    ) -> int:
        """Descarga en bloque una zona para uso offline y actualiza metadata.json."""
        tiles = get_tiles_in_radius(lat, lon, radius_km, zoom_levels)
        total = len(tiles)
        downloaded = 0

        for i, (z, x, y) in enumerate(tiles):
            if stop_event and stop_event.is_set():
                break

            path = self.get_tile_path(z, x, y)
            if not os.path.exists(path):
                data = self._fetch_from_osm(z, x, y, timeout=5.0)
                if data:
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "wb") as f:
                        f.write(data)
                    downloaded += 1
                # Pausa ligera de cortesía hacia OpenStreetMap
                time.sleep(0.04)
            else:
                downloaded += 1

            if progress_cb:
                progress_cb(i + 1, total)

        # Registrar la zona en los metadatos
        now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        zone_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        region_tile_keys = [f"{z}/{x}/{y}.png" for (z, x, y) in tiles]

        if not zone_name or not zone_name.strip():
            final_zone_name = f"Zona {round(lat, 4)}°, {round(lon, 4)}° ({radius_km:.0f} km)"
        else:
            final_zone_name = zone_name.strip()

        metadata = self.get_metadata() or {}
        zones = metadata.get("zones", [])

        # Comprobar si ya existe una zona con centro y radio coincidentes para actualizarla
        found = False
        for z in zones:
            if (
                abs(z.get("center_lat", 0.0) - lat) < 0.01
                and abs(z.get("center_lon", 0.0) - lon) < 0.01
                and abs(z.get("radius_km", 0.0) - radius_km) < 0.5
            ):
                z["name"] = final_zone_name
                z["date"] = now_iso
                z["tiles"] = region_tile_keys
                z["tile_count"] = len(region_tile_keys)
                found = True
                break

        if not found:
            zones.append({
                "id": zone_id,
                "name": final_zone_name,
                "date": now_iso,
                "center_lat": round(lat, 5),
                "center_lon": round(lon, 5),
                "radius_km": radius_km,
                "zoom_levels": zoom_levels,
                "tiles": region_tile_keys,
                "tile_count": len(region_tile_keys)
            })

        # Actualizar metadatos globales
        total_tiles, size_mb = self.count_cached_tiles()
        metadata.update({
            "last_download_iso": now_iso,
            "center_lat": round(lat, 5),
            "center_lon": round(lon, 5),
            "radius_km": radius_km,
            "zoom_levels": zoom_levels,
            "region_tiles": total,
            "total_cached_tiles": total_tiles,
            "total_cache_size_mb": size_mb,
            "zones": zones
        })
        self.save_metadata(metadata)
        return downloaded

    def get_zones(self) -> List[Dict[str, Any]]:
        """Retorna la lista de zonas registradas en metadata.json."""
        metadata = self.get_metadata() or {}
        return metadata.get("zones", [])

    def rename_zone(self, zone_id: str, new_name: str) -> bool:
        """Modifica el nombre descriptivo de una zona guardada."""
        new_name = new_name.strip()
        if not new_name:
            return False
        metadata = self.get_metadata() or {}
        zones = metadata.get("zones", [])
        for z in zones:
            if z.get("id") == zone_id:
                z["name"] = new_name
                self.save_metadata(metadata)
                return True
        return False

    def delete_zone(self, zone_id: str) -> Tuple[int, float]:
        """Elimina una zona específica liberando sus teselas exclusivas de disco."""
        metadata = self.get_metadata() or {}
        zones = metadata.get("zones", [])

        target_zone = None
        remaining_zones = []
        for z in zones:
            if z.get("id") == zone_id:
                target_zone = z
            else:
                remaining_zones.append(z)

        if not target_zone:
            return 0, 0.0

        # Teselas de las otras zonas que deben preservarse
        other_tiles = set()
        for z in remaining_zones:
            other_tiles.update(z.get("tiles", []))

        deleted_count = 0
        deleted_bytes = 0

        for tile_rel in target_zone.get("tiles", []):
            if tile_rel not in other_tiles:
                full_path = os.path.join(self.cache_dir, tile_rel.replace("/", os.sep))
                if os.path.exists(full_path):
                    try:
                        deleted_bytes += os.path.getsize(full_path)
                        os.remove(full_path)
                        deleted_count += 1
                        parent = os.path.dirname(full_path)
                        try:
                            os.removedirs(parent)
                        except OSError:
                            pass
                    except Exception:
                        pass

        # Actualizar metadatos
        total_tiles, size_mb = self.count_cached_tiles()
        metadata["zones"] = remaining_zones
        metadata["total_cached_tiles"] = total_tiles
        metadata["total_cache_size_mb"] = size_mb
        self.save_metadata(metadata)

        freed_mb = round(deleted_bytes / (1024 * 1024), 2)
        return deleted_count, freed_mb

    def purge_older_than(self, days: int = 30) -> Tuple[int, float]:
        """Purga teselas del disco cuya fecha de modificación supere los N días."""
        cutoff_sec = time.time() - (days * 86400)
        deleted_count = 0
        deleted_bytes = 0

        for root, _, files in os.walk(self.cache_dir, topdown=False):
            for file in files:
                if file.endswith(".png"):
                    path = os.path.join(root, file)
                    try:
                        if os.path.getmtime(path) < cutoff_sec:
                            deleted_bytes += os.path.getsize(path)
                            os.remove(path)
                            deleted_count += 1
                    except Exception:
                        pass
            if root != self.cache_dir:
                try:
                    os.rmdir(root)
                except OSError:
                    pass

        # Actualizar metadatos y depurar zonas que ya no tengan teselas en disco
        metadata = self.get_metadata() or {}
        zones = metadata.get("zones", [])
        valid_zones = []
        for z in zones:
            remaining_tiles = [
                t for t in z.get("tiles", [])
                if os.path.exists(os.path.join(self.cache_dir, t.replace("/", os.sep)))
            ]
            if len(remaining_tiles) > 0:
                z["tiles"] = remaining_tiles
                z["tile_count"] = len(remaining_tiles)
                valid_zones.append(z)

        total_tiles, size_mb = self.count_cached_tiles()
        metadata["zones"] = valid_zones
        metadata["total_cached_tiles"] = total_tiles
        metadata["total_cache_size_mb"] = size_mb
        self.save_metadata(metadata)

        freed_mb = round(deleted_bytes / (1024 * 1024), 2)
        return deleted_count, freed_mb


class _MapHTTPHandler(http.server.BaseHTTPRequestHandler):
    """Manejador HTTP para la visualización de mapas Leaflet y entrega de teselas."""

    def handle(self):
        try:
            super().handle()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def log_message(self, format, *args):
        # Silenciar logs ruidosos en consola
        pass

    def do_GET(self):
        manager: MapTileManager = self.server.tile_manager
        leaflet_dir: str = self.server.leaflet_dir

        if self.path in ["/", "/map", "/index.html"]:
            self._serve_map_html()
        elif self.path in ["/calendar_map", "/calendar"]:
            self._serve_calendar_map_html()
        elif self.path.startswith("/leaflet/"):
            filename = os.path.basename(self.path)
            file_path = os.path.join(leaflet_dir, filename)
            if os.path.exists(file_path):
                ext = os.path.splitext(filename)[1].lower()
                mime_map = {
                    ".js": "application/javascript",
                    ".css": "text/css",
                    ".png": "image/png",
                    ".svg": "image/svg+xml"
                }
                ctype = mime_map.get(ext, "application/octet-stream")
                try:
                    with open(file_path, "rb") as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Content-Length", str(len(content)))
                    self.send_header("Cache-Control", "public, max-age=86400")
                    self.end_headers()
                    self.wfile.write(content)
                    return
                except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                    return
                except Exception:
                    pass
            self.send_error(404, "File not found")

        elif self.path.startswith("/tiles/"):
            parts = self.path.strip("/").split("/")
            if len(parts) == 4:
                try:
                    z = int(parts[1])
                    x = int(parts[2])
                    y = int(parts[3].replace(".png", ""))
                    data = manager.get_tile_data(z, x, y)
                    if data:
                        self.send_response(200)
                        self.send_header("Content-Type", "image/png")
                        self.send_header("Content-Length", str(len(data)))
                        self.send_header("Cache-Control", "public, max-age=86400")
                        self.end_headers()
                        self.wfile.write(data)
                        return
                except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                    return
                except Exception:
                    pass
            self.send_error(404, "Tile not found")
        else:
            self.send_error(404, "Not found")

    def _serve_map_html(self):
        html = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>eclipZe Map</title>
  <link rel="stylesheet" href="/leaflet/leaflet.css"/>
  <script src="/leaflet/leaflet.js"></script>
  <style>
    html, body, #map {
      margin: 0; padding: 0; width: 100%; height: 100%;
      background: #111827;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .leaflet-control-attribution {
      background: rgba(17, 24, 39, 0.85) !important;
      color: #9CA3AF !important;
      font-size: 10px;
    }
    .leaflet-control-attribution a {
      color: #60A5FA !important;
    }
    .custom-gps-popup .leaflet-popup-content-wrapper {
      background: #1F2937;
      color: #F3F4F6;
      border: 1px solid #374151;
      border-radius: 6px;
      font-size: 12px;
    }
    .custom-gps-popup .leaflet-popup-tip {
      background: #1F2937;
    }
    .map-legend {
      position: absolute;
      top: 12px;
      right: 12px;
      z-index: 1000;
      background: rgba(17, 24, 39, 0.90);
      color: #E5E9F0;
      padding: 7px 12px;
      border-radius: 6px;
      font-size: 11px;
      border: 1px solid #374151;
      pointer-events: none;
      box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
  </style>
</head>
<body>
  <div id="map"></div>
  <div class="map-legend">
    <div><span style="display:inline-block; width:10px; height:10px; background:#10B981; border:1px solid #fff; border-radius:50%; margin-right:6px; vertical-align:middle;"></span>Tu GPS</div>
    <div style="margin-top:4px;"><span style="display:inline-block; width:10px; height:10px; background:rgba(56,189,248,0.4); border:1px dashed #0284C7; border-radius:50%; margin-right:6px; vertical-align:middle;"></span>Zona a descargar (clic en mapa)</div>
  </div>
  <script>
    var map = L.map('map', {
      center: [40.654, -3.769],
      zoom: 14,
      zoomControl: true
    });

    L.tileLayer('/tiles/{z}/{x}/{y}.png', {
      maxZoom: 18,
      minZoom: 5,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> | eclipZe Offline'
    }).addTo(map);

    var gpsMarker = null;

    // Estado de la zona de descarga offline
    var downloadTarget = {
      lat: 40.654,
      lon: -3.769,
      radiusKm: 10.0
    };
    var downloadMarker = null;
    var downloadCircle = null;

    function initDownloadZone(lat, lon, radiusKm) {
      downloadTarget.lat = lat;
      downloadTarget.lon = lon;
      downloadTarget.radiusKm = radiusKm || 10.0;

      downloadCircle = L.circle([lat, lon], {
        radius: downloadTarget.radiusKm * 1000,
        color: '#0284C7',
        weight: 2,
        dashArray: '6, 6',
        fillColor: '#38BDF8',
        fillOpacity: 0.18
      }).addTo(map);
      downloadCircle.bindTooltip("Zona a descargar: " + downloadTarget.radiusKm + " km", { direction: 'top' });

      downloadMarker = L.circleMarker([lat, lon], {
        radius: 8,
        color: '#FFFFFF',
        weight: 2,
        fillColor: '#0284C7',
        fillOpacity: 1.0
      }).addTo(map);
      downloadMarker.bindPopup("<b>Centro de Descarga Offline</b><br>Haz clic en cualquier punto del mapa para mover la zona.");

      map.on('click', function(e) {
        setDownloadTarget(e.latlng.lat, e.latlng.lng, downloadTarget.radiusKm);
      });

      notifyQtTarget();
    }

    function setDownloadTarget(lat, lon, radiusKm) {
      downloadTarget.lat = lat;
      downloadTarget.lon = lon;
      if (radiusKm !== undefined && radiusKm !== null) {
        downloadTarget.radiusKm = parseFloat(radiusKm);
      }
      if (downloadCircle) {
        downloadCircle.setLatLng([lat, lon]);
        downloadCircle.setRadius(downloadTarget.radiusKm * 1000);
        downloadCircle.setTooltipContent("Zona a descargar: " + downloadTarget.radiusKm + " km");
      }
      if (downloadMarker) {
        downloadMarker.setLatLng([lat, lon]);
      }
      notifyQtTarget();
    }

    function setDownloadRadius(radiusKm) {
      downloadTarget.radiusKm = parseFloat(radiusKm);
      if (downloadCircle) {
        downloadCircle.setRadius(downloadTarget.radiusKm * 1000);
        downloadCircle.setTooltipContent("Zona a descargar: " + downloadTarget.radiusKm + " km");
      }
      notifyQtTarget();
    }

    function centerDownloadOnView() {
      var c = map.getCenter();
      setDownloadTarget(c.lat, c.lng, downloadTarget.radiusKm);
    }

    function notifyQtTarget() {
      document.title = "TARGET:" + downloadTarget.lat.toFixed(5) + "," + downloadTarget.lon.toFixed(5) + "," + downloadTarget.radiusKm;
    }

    function updateGPSPosition(lat, lon, hasFix, satellites) {
      if (!lat || !lon) return;
      var color = hasFix ? '#10B981' : '#F59E0B';
      var text = "<b>Posición GPS eclipZe</b><br>" +
                 "Lat: " + lat.toFixed(5) + "°<br>" +
                 "Lon: " + lon.toFixed(5) + "°<br>" +
                 "Satélites: " + (satellites || 0) + (hasFix ? " (Fix OK)" : " (Buscando)");

      if (!gpsMarker) {
        gpsMarker = L.circleMarker([lat, lon], {
          radius: 9,
          fillColor: color,
          color: '#FFFFFF',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.95
        }).addTo(map);
        gpsMarker.bindPopup(text, { className: 'custom-gps-popup' });
      } else {
        gpsMarker.setLatLng([lat, lon]);
        gpsMarker.setStyle({ fillColor: color });
        gpsMarker.setPopupContent(text);
      }
    }

    function centerMap(lat, lon, zoom) {
      if (lat && lon) {
        if (zoom) {
          map.setView([lat, lon], zoom);
        } else {
          map.panTo([lat, lon]);
        }
      }
    }

    // Inicializar zona de descarga en coordenadas iniciales
    initDownloadZone(40.654, -3.769, 10.0);
  </script>
</body>
</html>"""
        content = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _serve_calendar_map_html(self):
        html = get_calendar_map_html()
        content = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def get_calendar_map_html() -> str:
    """Retorna la plantilla HTML/JS para el visor interactivo de eclipses en Leaflet."""
    return """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>eclipZe Eclipse Track Map</title>
  <link rel="stylesheet" href="/leaflet/leaflet.css"/>
  <script src="/leaflet/leaflet.js"></script>
  <style>
    html, body, #map {
      margin: 0; padding: 0; width: 100%; height: 100%;
      background: #111827;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .leaflet-control-attribution {
      background: rgba(17, 24, 39, 0.85) !important;
      color: #9CA3AF !important;
      font-size: 10px;
    }
    .leaflet-control-attribution a {
      color: #60A5FA !important;
    }
    .custom-popup .leaflet-popup-content-wrapper {
      background: #1F2937;
      color: #F3F4F6;
      border: 1px solid #374151;
      border-radius: 6px;
      font-size: 11px;
      line-height: 1.4;
      box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    .custom-popup .leaflet-popup-tip {
      background: #1F2937;
    }
    .map-badge {
      position: absolute;
      top: 10px;
      right: 10px;
      z-index: 1000;
      background: rgba(17, 24, 39, 0.90);
      backdrop-filter: blur(4px);
      color: #ECEFF4;
      padding: 6px 10px;
      border-radius: 6px;
      font-size: 11px;
      border: 1px solid #374151;
      pointer-events: none;
      box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .legend-dot {
      display: inline-block;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      margin-right: 6px;
      vertical-align: middle;
    }
  </style>
</head>
<body>
  <div id="map"></div>
  <div class="map-badge" id="mapBadge">
    <div><span class="legend-dot" style="background:#38BDF8; border:1px solid #fff;"></span>Tu Posición (clic para mover)</div>
    <div style="margin-top:4px;"><span class="legend-dot" id="legendTotalityDot" style="background:#A855F7; border:1px solid #fff;"></span>Franja de Totalidad</div>
  </div>
  <script>
    var map = L.map('map', {
      center: [40.4, -3.7],
      zoom: 5,
      zoomControl: true
    });

    L.tileLayer('/tiles/{z}/{x}/{y}.png', {
      maxZoom: 18,
      minZoom: 2,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> | eclipZe'
    }).addTo(map);

    var observerMarker = null;
    var currentObserverLat = 40.65406;
    var currentObserverLon = -3.76918;
    var currentObserverDesc = "";
    var eclipseLayerGroup = L.layerGroup().addTo(map);

    function setObserverPosition(lat, lon, desc) {
      if (lat === undefined || lon === undefined || lat === null || lon === null) return;
      currentObserverLat = lat;
      currentObserverLon = lon;
      if (desc !== undefined && desc !== null) {
        currentObserverDesc = desc;
      }
      var popupText = "<b>📍 Punto de Observación</b><br>" +
                      "Lat: " + lat.toFixed(5) + "°<br>Lon: " + lon.toFixed(5) + "°";
      if (currentObserverDesc) {
        popupText += "<br><span style='color:#38BDF8; font-weight:bold;'>" + currentObserverDesc + "</span>";
      }

      if (!observerMarker) {
        observerMarker = L.circleMarker([lat, lon], {
          radius: 8,
          fillColor: '#38BDF8',
          color: '#FFFFFF',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.95
        }).addTo(map);
        observerMarker.bindPopup(popupText, { className: 'custom-popup' });
      } else {
        observerMarker.setLatLng([lat, lon]);
        observerMarker.setPopupContent(popupText);
      }
    }

    map.on('click', function(e) {
      var lat = e.latlng.lat;
      var lon = e.latlng.lng;
      setObserverPosition(lat, lon);
      document.title = "OBSERVER:" + lat.toFixed(5) + "," + lon.toFixed(5);
    });

    function computeCorridorPolygon(centerline, widthKm) {
      if (!centerline || centerline.length < 2) return null;
      var halfWidthKm = Math.max(10, (widthKm || 200) / 2.0);

      // Subdividir segmentos largos (> 70 km) para garantizar una curvatura suave y continua sin quiebres
      var dense = [];
      for (var i = 0; i < centerline.length - 1; i++) {
        var pA = centerline[i];
        var pB = centerline[i + 1];
        dense.push(pA);

        var latA = pA.lat, lonA = pA.lon;
        var latB = pB.lat, lonB = pB.lon;
        var cosMid = Math.max(0.1, Math.cos((latA + latB) * 0.5 * Math.PI / 180.0));
        var distKm = Math.hypot((latB - latA) * 111.0, (lonB - lonA) * 111.0 * cosMid);
        if (distKm > 75.0) {
          var steps = Math.min(15, Math.ceil(distKm / 45.0));
          for (var s = 1; s < steps; s++) {
            var frac = s / steps;
            dense.push({
              lat: latA + frac * (latB - latA),
              lon: lonA + frac * (lonB - lonA)
            });
          }
        }
      }
      dense.push(centerline[centerline.length - 1]);

      var leftPoints = [];
      var rightPoints = [];

      for (var i = 0; i < dense.length; i++) {
        var p = dense[i];
        var lat = p.lat;
        var lon = p.lon;
        var pPrev = (i > 0) ? dense[i - 1] : p;
        var pNext = (i < dense.length - 1) ? dense[i + 1] : p;

        var cosLat = Math.max(0.05, Math.cos(lat * Math.PI / 180.0));
        var dLat = (pNext.lat - pPrev.lat);
        var dLon = (pNext.lon - pPrev.lon) * cosLat;
        var len = Math.hypot(dLat, dLon);
        if (len < 1e-7) {
          dLat = 0; dLon = 1; len = 1;
        }
        var tLat = dLat / len;
        var tLon = dLon / len;

        // Normal perpendicular a la trayectoria
        var nLat = tLon;
        var nLon = -tLat;

        var degLat = (halfWidthKm / 111.0) * nLat;
        var degLon = (halfWidthKm / (111.0 * cosLat)) * nLon;

        leftPoints.push([lat + degLat, lon + degLon]);
        rightPoints.push([lat - degLat, lon - degLon]);
      }

      return {
        ring: leftPoints.concat(rightPoints.slice().reverse()),
        north: leftPoints,
        south: rightPoints
      };
    }

    function setEclipsePath(data) {
      eclipseLayerGroup.clearLayers();
      if (!data) return;

      var color = data.badge_color || '#A855F7';
      var dot = document.getElementById("legendTotalityDot");
      if (dot) dot.style.background = color;

      var centerline = data.centerline || [];
      var widthKm = data.path_width_km || 200.0;
      var isAnnular = (data.type === 'solar_annular');
      var bandName = isAnnular ? 'Anularidad' : 'Totalidad';

      // 1. Polígono y límites (Norte y Sur)
      if (data.northern_limit && data.southern_limit && data.northern_limit.length > 0) {
        var ring = (data.path_polygon && data.path_polygon.length > 0) ?
                   data.path_polygon :
                   data.northern_limit.concat(data.southern_limit.slice().reverse());

        var poly = L.polygon(ring, {
          color: color,
          fillColor: color,
          fillOpacity: 0.22,
          weight: 1.5,
          opacity: 0.8
        }).addTo(eclipseLayerGroup);
        poly.bindTooltip("Franja de " + bandName + " (" + Math.round(widthKm) + " km de ancho)", { sticky: true });

        L.polyline(data.northern_limit, {
          color: color,
          weight: 1.5,
          dashArray: '4, 4',
          opacity: 0.8
        }).addTo(eclipseLayerGroup);

        L.polyline(data.southern_limit, {
          color: color,
          weight: 1.5,
          dashArray: '4, 4',
          opacity: 0.8
        }).addTo(eclipseLayerGroup);
      } else if (centerline.length >= 2) {
        var corridor = computeCorridorPolygon(centerline, widthKm);
        if (corridor) {
          var poly = L.polygon(corridor.ring, {
            color: color,
            fillColor: color,
            fillOpacity: 0.22,
            weight: 1.5,
            opacity: 0.8
          }).addTo(eclipseLayerGroup);
          poly.bindTooltip("Franja de " + bandName + " (" + Math.round(widthKm) + " km de ancho)", { sticky: true });

          L.polyline(corridor.north, {
            color: color,
            weight: 1.5,
            dashArray: '4, 4',
            opacity: 0.7
          }).addTo(eclipseLayerGroup);

          L.polyline(corridor.south, {
            color: color,
            weight: 1.5,
            dashArray: '4, 4',
            opacity: 0.7
          }).addTo(eclipseLayerGroup);
        }
      }

      // 2. Línea central punteada y nodos
      if (centerline.length >= 2) {
        var lineCoords = centerline.map(function(pt) { return [pt.lat, pt.lon]; });
        L.polyline(lineCoords, {
          color: '#F59E0B',
          weight: 2.5,
          dashArray: '6, 6',
          opacity: 0.95
        }).addTo(eclipseLayerGroup);

        var step = centerline.length > 40 ? Math.ceil(centerline.length / 25) : 1;
        centerline.forEach(function(pt, idx) {
          if (idx % step !== 0 && idx !== centerline.length - 1) return;
          var durText = pt.duration_s ? Math.round(pt.duration_s) + "s" : "";
          var timeText = pt.utc_iso ? pt.utc_iso.substring(11, 19) + " UTC" : "";
          var tip = "<b>" + (data.name || "Eclipse") + "</b><br>" +
                    "Máximo: " + timeText + "<br>" +
                    "Duración central: " + durText;
          var m = L.circleMarker([pt.lat, pt.lon], {
            radius: 4,
            fillColor: '#F59E0B',
            color: '#FFFFFF',
            weight: 1.5,
            fillOpacity: 1
          }).addTo(eclipseLayerGroup);
          m.bindPopup(tip, { className: 'custom-popup' });
        });

        try {
          var bounds = L.latLngBounds(lineCoords);
          map.fitBounds(bounds, { padding: [35, 35], maxZoom: 7 });
        } catch (e) {}
      } else if (centerline.length === 1) {
        var pt = centerline[0];
        L.circleMarker([pt.lat, pt.lon], {
          radius: 12,
          fillColor: color,
          color: '#FFFFFF',
          weight: 2,
          fillOpacity: 0.5
        }).addTo(eclipseLayerGroup).bindPopup(data.name || "Eclipse", { className: 'custom-popup' });
        map.setView([pt.lat, pt.lon], 4);
      }
    }

    // Inicializar posición observador
    setObserverPosition(40.65406, -3.76918);
  </script>
</body>
</html>"""


class MapServer:
    """Servidor HTTP multi-hilo local para servir mapas y teselas a QWebEngineView."""

    def __init__(self, tile_manager: Optional[MapTileManager] = None):
        self.tile_manager = tile_manager or MapTileManager()
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.leaflet_dir = os.path.join(root, "ui", "leaflet")

        # Intentar enlazar puerto dinámico (puerto 0 selecciona un puerto libre del SO)
        self.server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), _MapHTTPHandler)
        self.server.tile_manager = self.tile_manager
        self.server.leaflet_dir = self.leaflet_dir
        self.port = self.server.server_address[1]

        self._thread: Optional[threading.Thread] = None
        self._is_running = False

    def start(self):
        if not self._is_running:
            self._is_running = True
            self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self._thread.start()

    def stop(self):
        if self._is_running:
            self._is_running = False
            self.server.shutdown()
            self.server.server_close()
            if self._thread:
                self._thread.join(timeout=1.0)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/map"

    @property
    def calendar_url(self) -> str:
        return f"http://127.0.0.1:{self.port}/calendar_map"
