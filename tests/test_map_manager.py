"""
Pruebas unitarias para el gestor de mapas offline y servidor de teselas.
"""

import os
import sys
import tempfile
import shutil

# Asegurar path raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.map_manager import (
    lat_lon_to_tile,
    get_tiles_in_radius,
    MapTileManager,
    MapServer
)


def test_tile_math():
    # Coordenadas conocidas: 40.654 N, -3.769 W en zoom 14
    xtile, ytile = lat_lon_to_tile(40.654, -3.769, 14)
    assert xtile == 8020, f"xtile esperado 8020, obtenido {xtile}"
    assert ytile == 6163, f"ytile esperado 6163, obtenido {ytile}"

    # Radio en km
    tiles = get_tiles_in_radius(40.654, -3.769, 1.0, [12])
    assert len(tiles) >= 1, "Debe generar al menos 1 tesela para 1km a zoom 12"
    for z, x, y in tiles:
        assert z == 12


def test_map_tile_manager_and_metadata():
    temp_dir = tempfile.mkdtemp()
    try:
        manager = MapTileManager(cache_dir=temp_dir)
        assert manager.get_metadata() is None

        # Guardar metadatos sintéticos
        dummy_meta = {
            "last_download_iso": "2026-11-04 12:00:00",
            "center_lat": 40.654,
            "center_lon": -3.769,
            "radius_km": 5.0,
            "total_cached_tiles": 10,
            "total_cache_size_mb": 0.2
        }
        manager.save_metadata(dummy_meta)

        loaded = manager.get_metadata()
        assert loaded is not None
        assert loaded["radius_km"] == 5.0
        assert loaded["center_lat"] == 40.654

        # Crear una tesela sintética
        tile_path = manager.get_tile_path(12, 2004, 1540)
        os.makedirs(os.path.dirname(tile_path), exist_ok=True)
        with open(tile_path, "wb") as f:
            f.write(b"PNG_FAKE_DATA")

        assert manager.has_tile(12, 2004, 1540) is True
        data = manager.get_tile_data(12, 2004, 1540)
        assert data == b"PNG_FAKE_DATA"

        count, mb = manager.count_cached_tiles()
        assert count == 1
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_zone_deletion_and_purge():
    temp_dir = tempfile.mkdtemp()
    try:
        mgr = MapTileManager(cache_dir=temp_dir)
        t1 = mgr.get_tile_path(12, 100, 100)
        t2 = mgr.get_tile_path(12, 100, 101)
        t3 = mgr.get_tile_path(12, 100, 102)
        for p in [t1, t2, t3]:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "wb") as f:
                f.write(b"X" * 1024)

        meta = {
            "zones": [
                {"id": "zoneA", "name": "Zone A", "date": "2026-11-01", "tiles": ["12/100/100.png", "12/100/101.png"]},
                {"id": "zoneB", "name": "Zone B", "date": "2026-11-04", "tiles": ["12/100/101.png", "12/100/102.png"]}
            ]
        }
        mgr.save_metadata(meta)

        deleted, freed = mgr.delete_zone("zoneA")
        assert deleted == 1, f"Debió borrar 1 tesela, borró {deleted}"
        assert not os.path.exists(t1), "t1 debió ser borrada"
        assert os.path.exists(t2), "t2 debió preservarse porque Zone B la comparte"
        assert os.path.exists(t3), "t3 debió preservarse"
        assert len(mgr.get_zones()) == 1

        # Probar renombrado de zona
        renamed = mgr.rename_zone("zoneB", "Eclipse Total Cádiz 2027")
        assert renamed is True
        assert mgr.get_zones()[0]["name"] == "Eclipse Total Cádiz 2027"

        # Nombre vacío debe ser rechazado
        assert mgr.rename_zone("zoneB", "   ") is False

        import time
        old_time = time.time() - (10 * 86400)
        os.utime(t3, (old_time, old_time))
        del_count, del_mb = mgr.purge_older_than(days=5)
        assert del_count == 1
        assert not os.path.exists(t3), "t3 debió ser purgada por antigüedad"
        assert os.path.exists(t2), "t2 era reciente y debió conservarse"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_map_server():
    import urllib.request
    import socket
    import struct

    manager = MapTileManager()
    server = MapServer(manager)
    server.start()
    try:
        assert server.port > 0
        assert server.url.startswith("http://127.0.0.1:")
        with urllib.request.urlopen(server.url, timeout=3) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
            assert "eclipZe Map" in html
            assert "initDownloadZone" in html
            assert "setDownloadTarget" in html
            assert "setDownloadRadius" in html

        # Simular desconexión abrupta del cliente (RST) al pedir tesela
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", server.port))
        s.sendall(b"GET /tiles/10/500/500.png HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
        s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
        s.close()
    finally:
        server.stop()


if __name__ == "__main__":
    print("Ejecutando tests de Map Manager & Offline Tiles...")
    test_tile_math()
    print("  [OK] Tile coordinate math")
    test_map_tile_manager_and_metadata()
    print("  [OK] MapTileManager cache & metadata")
    test_zone_deletion_and_purge()
    print("  [OK] Selective zone deletion & age-based purge")
    test_map_server()
    print("  [OK] Local Map HTTP Server")
    print("Todos los tests de mapas pasaron exitosamente.")
