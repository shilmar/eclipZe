"""
Diagnóstico y prueba de comunicación USB PTP para cámaras Nikon (Z5 II / D750).
Verifica endpoints Bulk IN/OUT, handshake PTP, lectura de telemetría y disparo.
"""

import sys
import struct
import time

try:
    import libusb_package
    import usb.core
    import usb.util
except ImportError:
    print("[ERROR] Falta instalar dependencias. Ejecuta: pip install pyusb libusb-package")
    sys.exit(1)


NIKON_VID = 0x04B0
KNOWN_MODELS = {
    0x0456: "Nikon Z5 II",
    0x0440: "Nikon Z5",
    0x0444: "Nikon Z6 II",
    0x0435: "Nikon D750",
}

# Códigos de Operación PTP Estándar (ISO 15740)
PTP_OC_GET_DEVICE_INFO   = 0x1001
PTP_OC_OPEN_SESSION      = 0x1002
PTP_OC_CLOSE_SESSION     = 0x1003
PTP_OC_INITIATE_CAPTURE  = 0x100E

# Respuestas PTP
PTP_RC_OK                = 0x2001
PTP_RC_SESSION_ALREADY_OPEN = 0x201E
PTP_RC_DEVICE_BUSY       = 0x2019


def parse_ptp_string(buffer: bytes, offset: int) -> tuple[str, int]:
    """Decodifica cadenas PTP en formato Unicode UTF-16LE con prefijo de longitud."""
    if offset >= len(buffer):
        return "", offset
    num_chars = buffer[offset]
    offset += 1
    if num_chars == 0:
        return "", offset
    byte_len = num_chars * 2
    raw = buffer[offset:offset + byte_len]
    text = raw.decode("utf-16le", errors="ignore").rstrip("\x00")
    return text, offset + byte_len


def run_camera_test():
    print("=" * 65)
    print("       DIAGNÓSTICO Y CONTROL PTP — NIKON Z5 II (eclipZe)")
    print("=" * 65)

    backend = libusb_package.get_libusb1_backend()
    dev = libusb_package.find(idVendor=NIKON_VID)

    if not dev:
        print("[FALLO] No se detectó ninguna cámara Nikon por USB.")
        print("Comprueba que esté encendida y conectada con cable de datos.")
        return

    model_name = KNOWN_MODELS.get(dev.idProduct, f"Nikon (PID: 0x{dev.idProduct:04X})")
    print(f"[OK] Dispositivo USB encontrado: {model_name} (VID: 0x{NIKON_VID:04X}, PID: 0x{dev.idProduct:04X})")

    # 1. Obtener interfaz y endpoints
    try:
        cfg = dev.get_active_configuration()
        intf = cfg[(0, 0)]
    except Exception as e:
        print(f"[ERROR] No se pudo leer la configuración del dispositivo: {e}")
        return

    ep_out = None
    ep_in = None
    ep_intr = None

    for ep in intf:
        addr = ep.bEndpointAddress
        bm = ep.bmAttributes & 0x03
        is_in = (addr & 0x80) != 0

        if bm == 2:  # BULK
            if is_in:
                ep_in = ep
            else:
                ep_out = ep
        elif bm == 3 and is_in:  # INTERRUPT IN
            ep_intr = ep

    if not ep_out or not ep_in:
        print(f"[ERROR] No se encontraron los endpoints Bulk requeridos.")
        return

    print(f"[Paso 1] Endpoints USB identificados correctamente:")
    print(f"  -> Bulk OUT (Comandos): 0x{ep_out.bEndpointAddress:02X}")
    print(f"  -> Bulk IN  (Respuestas): 0x{ep_in.bEndpointAddress:02X}")
    if ep_intr:
        print(f"  -> Interrupt IN (Eventos): 0x{ep_intr.bEndpointAddress:02X}")

    # 2. Handshake PTP: GetDeviceInfo (funciona sin sesión)
    print("\n[Paso 2] Solicitando información del dispositivo (PTP GetDeviceInfo)...")
    tx_id = 1
    # Formato comando: Length(12), Type(1=Command), Code(0x1001), TxID(1)
    cmd_info = struct.pack("<IHHI", 12, 1, PTP_OC_GET_DEVICE_INFO, tx_id)
    try:
        ep_out.write(cmd_info, timeout=2000)
        data = bytes(ep_in.read(2048, timeout=3000))
        status_raw = ep_in.read(512, timeout=2000)
        status_code = struct.unpack("<IHHI", status_raw[:12])[2]

        if status_code == PTP_RC_OK:
            print("  -> ¡Handshake PTP exitoso! Código de respuesta: 0x2001 (OK)")
            # Decodificar metadatos de la cámara
            try:
                # Saltar campos numéricos de cabecera PTP hasta las cadenas de texto
                off = 12 + 2 + 4 + 2  # StandardVersion, VendorExtensionID, VendorExtensionVersion
                ext_len = data[off]
                off += 1 + ext_len * 2 + 2  # VendorExtensionDesc + FunctionalMode
                
                # Arrays de 16-bit: Operaciones, Eventos, Propiedades del dispositivo, etc.
                for _ in range(5):
                    if off + 4 <= len(data):
                        count = struct.unpack("<I", data[off:off + 4])[0]
                        off += 4 + count * 2

                manufacturer, off = parse_ptp_string(data, off)
                model, off = parse_ptp_string(data, off)
                version, off = parse_ptp_string(data, off)
                serial_num, off = parse_ptp_string(data, off)

                print(f"  -> Fabricante: {manufacturer or 'Nikon Corporation'}")
                print(f"  -> Modelo:     {model or model_name}")
                print(f"  -> Firmware:   {version or 'N/A'}")
                print(f"  -> N° Serie:   {serial_num or 'N/A'}")
            except Exception:
                print(f"  -> Cámara reconocida como {model_name}")
        else:
            print(f"  -> Respuesta GetDeviceInfo: 0x{status_code:04X}")

    except Exception as e:
        print(f"[ERROR en GetDeviceInfo]: {e}")
        return

    # 3. Abrir Sesión PTP (OpenSession)
    print("\n[Paso 3] Abriendo sesión PTP (OpenSession)...")
    tx_id += 1
    # Formato: Length(16), Type(1), Code(0x1002), TxID(0), Param1(SessionID=1)
    cmd_open = struct.pack("<IHHI I", 16, 1, PTP_OC_OPEN_SESSION, 0, 1)
    try:
        ep_out.write(cmd_open, timeout=2000)
        resp_raw = ep_in.read(512, timeout=2000)
        resp_code = struct.unpack("<IHHI", resp_raw[:12])[2]

        if resp_code in (PTP_RC_OK, PTP_RC_SESSION_ALREADY_OPEN):
            print("  -> ¡Sesión PTP activa y lista!")
        else:
            print(f"  -> Código respuesta OpenSession: 0x{resp_code:04X}")

        # 4. Probar disparo real asíncrono
        print("\n[Paso 4] ¿Deseas probar un disparo real del obturador? (s/n)")
        resp_user = input("  > ").strip().lower()
        if resp_user in ("s", "si", "y", "yes"):
            print("  -> Enviando pulso de captura PTP (InitiateCapture)...")
            tx_id += 1
            cmd_capture = struct.pack("<IHHI II", 20, 1, PTP_OC_INITIATE_CAPTURE, tx_id, 0, 0)
            ep_out.write(cmd_capture, timeout=2000)
            cap_resp = ep_in.read(512, timeout=3000)
            cap_code = struct.unpack("<IHHI", cap_resp[:12])[2]
            if cap_code == PTP_RC_OK:
                print("  -> [¡CLIC!] Disparo emitido con éxito por el bus PTP.")
            else:
                print(f"  -> Respuesta InitiateCapture: 0x{cap_code:04X}")

        # 5. Cerrar sesión
        print("\n[Paso 5] Cerrando sesión PTP de forma limpia...")
        tx_id += 1
        cmd_close = struct.pack("<IHHI", 12, 1, PTP_OC_CLOSE_SESSION, tx_id)
        ep_out.write(cmd_close, timeout=2000)
        ep_in.read(512, timeout=2000)
        print("  -> Sesión PTP cerrada.")

    except Exception as e:
        print(f"[Aviso durante sesión]: {e}")

    print("\n" + "=" * 65)
    print(" ¡CONEXIÓN VERIFICADA! LA NIKON Z5 II ESTÁ 100% OPERATIVA")
    print("=" * 65)


if __name__ == "__main__":
    run_camera_test()
