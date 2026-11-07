"""
Generador de Plan de Respaldo Manual y Hoja de Ruta de Campo para eclipZe.
Produce un documento HTML autocontenido de alto contraste optimizado para
impresión en 1 sola página A4/A5 o visualización en navegador/móvil.
"""

import os
import time
import datetime
from typing import Dict, Optional, List, Any


def format_timestamp_utc(ts: Optional[float]) -> str:
    """Formatea un timestamp epoch UTC a cadena legible 'HH:MM:SS UTC'."""
    if ts is None:
        return "--:--:--"
    dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
    return dt.strftime("%H:%M:%S UTC")


def format_timestamp_local(ts: Optional[float], tz_offset_hours: Optional[float] = None) -> str:
    """Formatea un timestamp epoch a hora local del sistema o huso indicado."""
    if ts is None:
        return "--:--:--"
    if tz_offset_hours is not None:
        tz = datetime.timezone(datetime.timedelta(hours=tz_offset_hours))
        dt = datetime.datetime.fromtimestamp(ts, tz=tz)
        sign = "+" if tz_offset_hours >= 0 else ""
        return dt.strftime(f"%H:%M:%S (UTC{sign}{tz_offset_hours:g})")
    else:
        # Usar zona horaria local del equipo
        dt = datetime.datetime.fromtimestamp(ts).astimezone()
        tz_name = dt.tzname() or "Local"
        return dt.strftime(f"%H:%M:%S ({tz_name})")


def format_duration_mm_ss(seconds: float) -> str:
    """Formatea duración en segundos a 'MMm SSs'."""
    if seconds <= 0:
        return "00m 00s"
    m = int(seconds // 60)
    s = int(round(seconds % 60))
    return f"{m:02d}m {s:02d}s"


def generate_backup_plan_html(
    eclipse_name: str = "Eclipse Solar",
    location_name: str = "Campamento de Observación",
    lat: float = 0.0,
    lon: float = 0.0,
    alt_m: float = 0.0,
    visibility: str = "totality",
    totality_duration_s: float = 0.0,
    sun_altitude_deg: float = 0.0,
    sun_azimuth_deg: float = 0.0,
    contacts: Optional[Dict[str, float]] = None,
    camera_name: str = "Nikon Z5 II",
    lens_info: str = "500mm f/8",
    iso_default: str = "200",
    aperture_default: str = "f/8",
    custom_notes: Optional[List[str]] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Genera el HTML formal del plan manual de emergencia eclipZe.
    Si output_path se proporciona, escribe el archivo en disco y devuelve la ruta.
    De lo contrario, devuelve el string HTML.
    """
    contacts = contacts or {}
    c1 = contacts.get("C1")
    c2 = contacts.get("C2") or contacts.get("U2")
    c_max = contacts.get("MAX")
    c3 = contacts.get("C3") or contacts.get("U3")
    c4 = contacts.get("C4")

    # Si hay C2, calculamos C2 - 20s para la alerta de filtro
    c2_minus_20 = (c2 - 20.0) if c2 is not None else None

    # Fecha de referencia del evento
    event_date_str = ""
    ref_ts = c2 or c_max or c1
    if ref_ts is not None:
        ref_dt = datetime.datetime.fromtimestamp(ref_ts).astimezone()
        event_date_str = ref_dt.strftime("%d/%m/%Y")
    else:
        event_date_str = datetime.date.today().strftime("%d/%m/%Y")

    totality_str = format_duration_mm_ss(totality_duration_s)
    is_annular = "anul" in visibility.lower() or "anular" in eclipse_name.lower() or "annular" in eclipse_name.lower()
    vis_badge = "ANULARIDAD" if is_annular else ("TOTALIDAD" if "total" in visibility.lower() else "PARCIAL")
    badge_bg = "#D97706" if is_annular else ("#7C3AED" if vis_badge == "TOTALIDAD" else "#0284C7")

    # Filas de cronograma
    timeline_rows = []
    
    # C1
    if c1 is not None:
        timeline_rows.append({
            "phase": "C1 (Primer Contacto)",
            "utc": format_timestamp_utc(c1),
            "local": format_timestamp_local(c1),
            "rel": f"-{format_duration_mm_ss(c2 - c1)}" if c2 else "--",
            "action": "Filtro solar instalado. Iniciar fotos parciales periódicas.",
            "alert_class": ""
        })

    # C2 - 20s (Seguridad crítica)
    if c2_minus_20 is not None:
        if is_annular:
            timeline_rows.append({
                "phase": "⚠️ C2 - 20 seg",
                "utc": format_timestamp_utc(c2_minus_20),
                "local": format_timestamp_local(c2_minus_20),
                "rel": "-00m 20s",
                "action": "<strong>🛡️ ¡SEGURIDAD: MANTENER FILTRO SOLAR PUESTO!</strong> En eclipse anular nunca se retira el filtro de los objetivos.",
                "alert_class": "alert-warning"
            })
        else:
            timeline_rows.append({
                "phase": "⚠️ C2 - 20 seg",
                "utc": format_timestamp_utc(c2_minus_20),
                "local": format_timestamp_local(c2_minus_20),
                "rel": "-00m 20s",
                "action": "<strong>🚨 ¡RETIRAR FILTRO SOLAR DE TODOS LOS OBJETIVOS!</strong>",
                "alert_class": "alert-warning"
            })

    # C2
    if c2 is not None:
        if is_annular:
            timeline_rows.append({
                "phase": "💍 C2 (Inicio Anularidad)",
                "utc": format_timestamp_utc(c2),
                "local": format_timestamp_local(c2),
                "rel": "00m 00s (T0)",
                "action": "Formación del Anillo de Fuego. Disparos con filtro solar instalado.",
                "alert_class": "alert-highlight"
            })
        else:
            timeline_rows.append({
                "phase": "🌑 C2 (Inicio Totalidad)",
                "utc": format_timestamp_utc(c2),
                "local": format_timestamp_local(c2),
                "rel": "00m 00s (T0)",
                "action": "Perlas de Baily y Anillo de Diamantes. Ráfaga rápida.",
                "alert_class": "alert-highlight"
            })

    # MAX
    if c_max is not None:
        rel_max = f"+{format_duration_mm_ss(c_max - c2)}" if c2 else "--"
        if is_annular:
            timeline_rows.append({
                "phase": "👑 Máximo del Eclipse",
                "utc": format_timestamp_utc(c_max),
                "local": format_timestamp_local(c_max),
                "rel": rel_max,
                "action": "Máxima simetría del anillo. Tomas de alta velocidad con filtro solar.",
                "alert_class": ""
            })
        else:
            timeline_rows.append({
                "phase": "👑 Máximo del Eclipse",
                "utc": format_timestamp_utc(c_max),
                "local": format_timestamp_local(c_max),
                "rel": rel_max,
                "action": "Corona solar completa y luz cenicienta. Exposiciones largas.",
                "alert_class": ""
            })

    # C3
    if c3 is not None:
        if is_annular:
            timeline_rows.append({
                "phase": "☀️ C3 (Fin Anularidad)",
                "utc": format_timestamp_utc(c3),
                "local": format_timestamp_local(c3),
                "rel": f"+{totality_str}",
                "action": "Fin del anillo de fuego. <strong>Mantener filtro solar colocado</strong> para fases parciales post-C3.",
                "alert_class": "alert-warning"
            })
        else:
            timeline_rows.append({
                "phase": "☀️ C3 (Fin Totalidad)",
                "utc": format_timestamp_utc(c3),
                "local": format_timestamp_local(c3),
                "rel": f"+{totality_str}",
                "action": "<strong>🚨 ¡COLOCAR FILTRO SOLAR INMEDIATAMENTE!</strong> Segundo diamante.",
                "alert_class": "alert-danger"
            })

    # C4
    if c4 is not None:
        timeline_rows.append({
            "phase": "C4 (Cuarto Contacto)",
            "utc": format_timestamp_utc(c4),
            "local": format_timestamp_local(c4),
            "rel": f"+{format_duration_mm_ss(c4 - c2)}" if c2 else "--",
            "action": "Fin del eclipse. Revisión de tomas e inventario.",
            "alert_class": ""
        })

    # Si no hay contactos astronómicos reales (ej: simulación sin contactos)
    if not timeline_rows:
        timeline_rows.append({
            "phase": "⚠️ Contactos pendientes de cálculo",
            "utc": "--:--:--",
            "local": "--:--:--",
            "rel": "--",
            "action": "Activa un eclipse en el Calendario de eclipZe para sincronizar horas exactas.",
            "alert_class": "alert-warning"
        })

    # Render tabla cronograma
    table_rows_html = ""
    for r in timeline_rows:
        tr_cls = f" class='{r['alert_class']}'" if r["alert_class"] else ""
        table_rows_html += f"""
        <tr{tr_cls}>
            <td style="font-weight: 600;">{r['phase']}</td>
            <td style="font-family: monospace;">{r['utc']}</td>
            <td style="font-family: monospace;">{r['local']}</td>
            <td style="font-family: monospace; text-align: center;">{r['rel']}</td>
            <td>{r['action']}</td>
        </tr>
        """

    if is_annular:
        dial_table_html = """
                <table style="margin-bottom: 4px;">
                    <thead>
                        <tr>
                            <th>Fase / Fenómeno</th>
                            <th style="width: 28%;">Velocidades</th>
                            <th>Modo de Disparo</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Fase Parcial Pre-C2 (Con Filtro)</strong></td>
                            <td style="font-family: monospace;">1/4000s &ndash; 1/2000s</td>
                            <td>Toma simple periódica</td>
                        </tr>
                        <tr>
                            <td><strong>Perlas de Baily Anulares C2/C3 (Con Filtro)</strong></td>
                            <td style="font-family: monospace;">1/4000s</td>
                            <td>Ráfaga Continua (CH)</td>
                        </tr>
                        <tr>
                            <td><strong>Anillo de Fuego Entrada / Salida (Con Filtro)</strong></td>
                            <td style="font-family: monospace;">1/2000s &ndash; 1/1000s</td>
                            <td>Ráfaga corta o horquillado</td>
                        </tr>
                        <tr>
                            <td><strong>Máxima Anularidad Simétrica (Con Filtro)</strong></td>
                            <td style="font-family: monospace;">1/2000s &ndash; 1/1000s</td>
                            <td>Horquillado AEB moderado</td>
                        </tr>
                        <tr>
                            <td><strong>Fase Parcial Post-C3 (Con Filtro)</strong></td>
                            <td style="font-family: monospace;">1/4000s &ndash; 1/2000s</td>
                            <td>Toma simple periódica</td>
                        </tr>
                    </tbody>
                </table>
                <div class="callout-rule" style="background: #FEF2F2; border-color: #EF4444; color: #991B1B;">
                    <strong>🛡️ Regla Crítica de Seguridad:</strong> En un eclipse anular la fotosfera solar NUNCA queda totalmente cubierta. <strong>NUNCA retires el filtro solar</strong> ni mires directamente sin gafas homologadas ISO 12312-2.
                </div>
        """
        golden_rule_html = "Regla de Oro: En eclipse anular <strong>NUNCA mirar directamente sin filtro homologado ISO 12312-2</strong>."
    else:
        dial_table_html = """
                <table style="margin-bottom: 4px;">
                    <thead>
                        <tr>
                            <th>Fase / Fenómeno</th>
                            <th style="width: 28%;">Velocidades</th>
                            <th>Modo de Disparo</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Perlas de Baily / Anillo</strong></td>
                            <td style="font-family: monospace;">1/4000s &ndash; 1/1000s</td>
                            <td>Ráfaga Continua (CH)</td>
                        </tr>
                        <tr>
                            <td><strong>Prominencias & Cromosfera</strong></td>
                            <td style="font-family: monospace;">1/1000s &ndash; 1/500s</td>
                            <td>Disparos directos</td>
                        </tr>
                        <tr>
                            <td><strong>Corona Interna</strong></td>
                            <td style="font-family: monospace;">1/250s &ndash; 1/125s</td>
                            <td>Toma simple o AEB</td>
                        </tr>
                        <tr>
                            <td><strong>Corona Media & Bucles</strong></td>
                            <td style="font-family: monospace;">1/60s &ndash; 1/30s</td>
                            <td>Disparador remoto</td>
                        </tr>
                        <tr>
                            <td><strong>Corona Externa & Earthshine</strong></td>
                            <td style="font-family: monospace;">1/8s, 1/4s, 1/2s, 1s</td>
                            <td>Cable remoto (sin tocar trípode)</td>
                        </tr>
                    </tbody>
                </table>
                <div class="callout-rule">
                    <strong>Atajo Rápido AEB en Cámara:</strong> Si el PC muere, pon la cámara en <strong>Modo M</strong>, mantén presionado botón <strong>BKT</strong> y gira dial a <strong>7F o 9F a 1.0 EV</strong> (o 1.7 EV). Mantén apretado el disparador de cable en ráfaga (CH).
                </div>
        """
        golden_rule_html = "Regla de Oro: Si todo falla, <strong>mira al cielo con tus propios ojos</strong>."

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>eclipZe - Plan Manual de Emergencia: {eclipse_name}</title>
    <style>
        @page {{
            size: A4 portrait;
            margin: 8mm 10mm;
        }}
        * {{
            box-sizing: border-box;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #111827;
            background-color: #FFFFFF;
            margin: 0;
            padding: 0;
            font-size: 11px;
            line-height: 1.35;
        }}
        .no-print {{
            background: #1E293B;
            color: white;
            padding: 10px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #3B82F6;
        }}
        .btn-print {{
            background: #2563EB;
            color: white;
            border: none;
            padding: 6px 16px;
            font-size: 13px;
            font-weight: bold;
            border-radius: 4px;
            cursor: pointer;
        }}
        .btn-print:hover {{
            background: #1D4ED8;
        }}
        @media print {{
            .no-print {{
                display: none !important;
            }}
            body {{
                font-size: 10px;
                line-height: 1.25;
            }}
            .card {{
                box-shadow: none !important;
                border: 1px solid #94A3B8 !important;
            }}
            .page-break {{
                page-break-after: always;
            }}
        }}

        /* Header */
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #1E293B;
            padding-bottom: 6px;
            margin-bottom: 8px;
        }}
        .header-title h1 {{
            margin: 0;
            font-size: 18px;
            font-weight: 800;
            color: #0F172A;
            letter-spacing: -0.5px;
        }}
        .header-title .sub {{
            font-size: 11px;
            color: #475569;
            font-weight: 500;
            margin-top: 2px;
        }}
        .badge {{
            display: inline-block;
            background: {badge_bg};
            color: white;
            padding: 4px 10px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
            letter-spacing: 0.5px;
        }}

        /* Meta bar */
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 6px;
            background: #F8FAFC;
            border: 1px solid #CBD5E1;
            border-radius: 4px;
            padding: 6px 10px;
            margin-bottom: 8px;
        }}
        .meta-item .lbl {{
            font-size: 9px;
            text-transform: uppercase;
            color: #64748B;
            font-weight: bold;
        }}
        .meta-item .val {{
            font-size: 11px;
            color: #0F172A;
            font-weight: 700;
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 8px;
            font-size: 10px;
        }}
        th {{
            background: #0F172A;
            color: white;
            text-align: left;
            padding: 4px 6px;
            font-weight: 700;
            font-size: 9.5px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }}
        td {{
            padding: 4px 6px;
            border-bottom: 1px solid #E2E8F0;
            border-left: 1px solid #F1F5F9;
            border-right: 1px solid #F1F5F9;
        }}
        tr:nth-child(even) {{
            background-color: #F8FAFC;
        }}
        .alert-warning {{
            background-color: #FEF3C7 !important;
            color: #92400E !important;
            font-weight: bold;
            border-left: 4px solid #F59E0B !important;
        }}
        .alert-danger {{
            background-color: #FEE2E2 !important;
            color: #991B1B !important;
            font-weight: bold;
            border-left: 4px solid #DC2626 !important;
        }}
        .alert-highlight {{
            background-color: #EDE9FE !important;
            color: #5B21B6 !important;
            font-weight: bold;
            border-left: 4px solid #7C3AED !important;
        }}

        /* Two columns layout */
        .two-cols {{
            display: grid;
            grid-template-columns: 1.15fr 0.85fr;
            gap: 10px;
        }}
        .section-title {{
            font-size: 11px;
            font-weight: 800;
            color: #0F172A;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin: 6px 0 4px 0;
            padding-bottom: 2px;
            border-bottom: 1.5px solid #0F172A;
        }}

        /* Checklist */
        .checklist {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .checklist li {{
            padding: 2.5px 0;
            font-size: 9.5px;
            border-bottom: 1px dashed #E2E8F0;
            display: flex;
            align-items: flex-start;
        }}
        .box {{
            display: inline-block;
            width: 11px;
            height: 11px;
            border: 1.5px solid #1E293B;
            margin-right: 6px;
            border-radius: 2px;
            flex-shrink: 0;
            margin-top: 1px;
        }}

        /* Callout box */
        .callout-rule {{
            background: #FFFBEB;
            border: 1.5px solid #F59E0B;
            border-radius: 4px;
            padding: 5px 8px;
            margin-top: 6px;
            font-size: 9.5px;
            color: #78350F;
        }}
        .callout-rule strong {{
            color: #B45309;
        }}
        
        .footer-note {{
            margin-top: 6px;
            border-top: 1px solid #CBD5E1;
            padding-top: 3px;
            font-size: 8.5px;
            color: #64748B;
            display: flex;
            justify-content: space-between;
        }}
    </style>
</head>
<body>

    <div class="no-print">
        <div>
            <strong>eclipZe</strong> &mdash; Plan de Respaldo de Campo (Listo para imprimir en 1 página A4 o guardar en PDF)
        </div>
        <button class="btn-print" onclick="window.print()">🖨️ Imprimir / Guardar en PDF</button>
    </div>

    <div style="padding: 10px 14px;">
        <!-- Header -->
        <div class="header">
            <div class="header-title">
                <h1>eclipZe &bull; Plan de Respaldo Manual & Hoja de Ruta</h1>
                <div class="sub">
                    {eclipse_name} &bull; Fecha: <strong>{event_date_str}</strong> &bull; Ubicación: <strong>{location_name}</strong>
                </div>
            </div>
            <div style="text-align: right;">
                <span class="badge">{vis_badge}: {totality_str}</span>
            </div>
        </div>

        <!-- Telemetry meta -->
        <div class="meta-grid">
            <div class="meta-item">
                <div class="lbl">Coordenadas GPS</div>
                <div class="val">{lat:.4f}°, {lon:.4f}° ({alt_m:.0f}m)</div>
            </div>
            <div class="meta-item">
                <div class="lbl">Posición Solar (MAX)</div>
                <div class="val">Alt: {sun_altitude_deg:.1f}° | Az: {sun_azimuth_deg:.1f}°</div>
            </div>
            <div class="meta-item">
                <div class="lbl">Equipo Principal</div>
                <div class="val">{camera_name}</div>
            </div>
            <div class="meta-item">
                <div class="lbl">Óptica y Ajuste Base</div>
                <div class="val">{lens_info} &bull; ISO {iso_default} &bull; {aperture_default}</div>
            </div>
        </div>

        <!-- Timeline Section -->
        <div class="section-title">1. Cronograma de Contactos & Seguridad Óptica</div>
        <table>
            <thead>
                <tr>
                    <th style="width: 25%;">Hito Astronómico</th>
                    <th style="width: 17%;">Hora UTC</th>
                    <th style="width: 21%;">Hora Local</th>
                    <th style="width: 12%; text-align: center;">Relativo</th>
                    <th style="width: 25%;">Acción en el Sitio / Seguridad</th>
                </tr>
            </thead>
            <tbody>
                {table_rows_html}
            </tbody>
        </table>

        <!-- Two Columns: Manual Dial Table + Physical Checklist -->
        <div class="two-cols">
            <!-- Col 1: Manual Dial Fallback -->
            <div>
                <div class="section-title">2. Receta Manual de Rueda (Fallo de PC / Cable)</div>
                {dial_table_html}
            </div>

            <!-- Col 2: Physical Checklist -->
            <div>
                <div class="section-title">3. Checklist de Campo Pre-Eclipse</div>
                <ul class="checklist">
                    <li><span class="box"></span> <strong>Enfoque Manual (MF)</strong> afinado al borde solar y <u>fijado con cinta</u>.</li>
                    <li><span class="box"></span> <strong>Estabilizador (VR/IBIS/OS) en OFF</strong> (obligatorio en trípode).</li>
                    <li><span class="box"></span> <strong>Tarjetas SD formateadas</strong> en cámara (>30 GB libres).</li>
                    <li><span class="box"></span> <strong>Batería al 100%</strong> + 2ª batería cargada en el bolsillo.</li>
                    <li><span class="box"></span> <strong>Standby / Temporizador de reposo: OFF</strong> (No apagar cámara).</li>
                    <li><span class="box"></span> <strong>Formato RAW 14-bit</strong> sin comprimir + Obturador Silencioso ON.</li>
                    <li><span class="box"></span> <strong>Disparador remoto por cable</strong> conectado como respaldo físico.</li>
                    <li><span class="box"></span> <strong>Manta térmica</strong> protegiendo la cámara del sol directo antes de C2.</li>
                </ul>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer-note">
            <div>Generado por <strong>eclipZe</strong> v2.0 &bull; Protocolo de Seguridad: ISO 12312-2 para observación solar.</div>
            <div>{golden_rule_html}</div>
        </div>
    </div>

</body>
</html>
"""

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        return output_path

    return html
