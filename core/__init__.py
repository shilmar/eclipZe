"""
eclipZe core package.
"""
from .camera import (
    CameraDriver, MockCameraDriver, GPhotoCameraDriver, NikonPTPDriver,
    NikonSdkDriver, NikonD750SdkDriver, create_camera_driver
)
from .dispatcher import MultiCameraDispatcher, PriorityArbiter
from .equipment import EquipmentManager, CameraSlot, DiscoveredCamera
from .sequencer import EclipseSequencer, adjust_shutter_ev, SHUTTER_LADDER
from .presets import (
    EclipseEvent, get_solar_eclipse_2027_preset, get_solar_eclipse_annular_preset,
    get_lunar_eclipse_bracket_preset, get_quick_rehearsal_preset,
    get_eclipse_test_preset, get_full_rehearsal_preset
)
from .audio import AudioNotifier
from .gps import GPSReader, GPSData
from .liveview import (
    calculate_focus_score, PeakHoldFilter, FocusMetricWorker,
    is_safety_cutoff_needed, SAFETY_CUTOFF_SECONDS, check_saturation
)
from .eclipse_db import EclipseInfo, EclipseCatalogManager
from .astronomy import calculate_local_eclipse, LocalEclipseResult, calculate_solar_position
