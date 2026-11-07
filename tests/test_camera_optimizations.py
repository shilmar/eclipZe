"""
Pruebas unitarias de las optimizaciones implementadas en camera.py:
- Conversión de velocidades de obturación a segundos
- Ejecución de rampas de horquillado (execute_bracket_ramp)
- Caché de propiedades PTP
- Batching de comandos por stdin
- Validación de D750 sin colisión de trigger_burst
"""

import pytest
from core.camera import (
    CameraDriver,
    MockCameraDriver,
    NikonSdkDriver,
    NikonPTPDriver,
    NikonD750SdkDriver,
    parse_shutter_to_ptp_u32,
)


def test_shutter_str_to_seconds():
    assert NikonSdkDriver._shutter_str_to_seconds("1/1000") == pytest.approx(0.001)
    assert NikonSdkDriver._shutter_str_to_seconds("1/4000") == pytest.approx(0.00025)
    assert NikonSdkDriver._shutter_str_to_seconds("2s") == pytest.approx(2.0)
    assert NikonSdkDriver._shutter_str_to_seconds("1.3s") == pytest.approx(1.3)
    assert NikonSdkDriver._shutter_str_to_seconds("Bulb") == pytest.approx(1.0)
    assert NikonSdkDriver._shutter_str_to_seconds("time") == pytest.approx(1.0)
    assert NikonSdkDriver._shutter_str_to_seconds("invalid") == pytest.approx(0.001)


def test_execute_bracket_ramp_mock():
    cam = MockCameraDriver()
    assert cam.connect() is True
    speeds = ["1/4000", "1/2000", "1/1000", "1/500", "1/250"]
    ok = cam.execute_bracket_ramp(speeds)
    assert ok is True
    assert len(cam.shot_history) == 5
    assert [s["shutter"] for s in cam.shot_history] == speeds


def test_nikon_ptp_prop_cache():
    cam = NikonPTPDriver()
    assert cam._cached_shutter_prop is None
    assert cam._cached_iso_prop is None

    # Simular set_shutter_speed con propiedad cacheada
    called_props = []

    def mock_set_prop(prop, val):
        called_props.append(prop)
        return True

    cam.connected = True
    cam._set_ptp_prop_u32 = mock_set_prop

    # Primer intento debe cachear
    assert cam.set_shutter_speed("1/2000") is True
    assert cam._cached_shutter_prop == 0xD100
    assert called_props == [0xD100]

    # Segundo intento debe usar directamente el cacheado
    called_props.clear()
    assert cam.set_shutter_speed("1/1000") is True
    assert called_props == [0xD100]


def test_nikon_ptp_iso_cache():
    cam = NikonPTPDriver()
    called_props = []

    def mock_set_prop(prop, val):
        called_props.append(prop)
        return True

    cam.connected = True
    cam._set_ptp_prop_u16 = mock_set_prop

    assert cam.set_iso("400") is True
    assert cam._cached_iso_prop == 0xD102
    assert called_props == [0xD102]

    called_props.clear()
    assert cam.set_iso("800") is True
    assert called_props == [0xD102]


def test_nikon_sdk_batch_payload():
    cam = NikonSdkDriver()
    written_data = bytearray()

    class FakeStdin:
        def write(self, data):
            written_data.extend(data)
        def flush(self):
            pass

    class FakeProc:
        def __init__(self):
            self.stdin = FakeStdin()
        def poll(self):
            return None

    cam.proc = FakeProc()
    cam.connected = True

    # Test set_shutter_speed via batch
    cam.set_shutter_speed("1/2000")
    # 1/2000 has index 60 -> commands ["1", "8", "60", "0"]
    assert written_data == b"1\n8\n60\n0\n"

    # Test set_iso via batch
    written_data.clear()
    cam.set_iso("400")
    # ISO 400 has index 8 -> commands ["3", "2", "8", "0"]
    assert written_data == b"3\n2\n8\n0\n"


def test_nikon_d750_sdk_driver_cleanup():
    cam = NikonD750SdkDriver()
    # Verificar que trigger_burst no arroja AttributeError por shot_history
    cam.connected = True
    cam.trigger_capture = lambda **kwargs: True
    cam.overhead_safety = 0.001
    assert cam.trigger_burst(count=3) is True
