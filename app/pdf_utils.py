from pathlib import Path
import json
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def _wrap_text(text, length=95):
    words = str(text or "").split()
    lines, current = [], []
    for word in words:
        probe = " ".join(current + [word])
        if len(probe) <= length:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines or [""]


def _ensure_room(c, y, height, margin=60):
    if y < margin:
        c.showPage()
        return height - 40
    return y


def _json_list(raw):
    try:
        return json.loads(raw or "[]")
    except Exception:
        return []


def generate_case_pdf(case, output_dir="generated_pdfs"):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    path = Path(output_dir) / f"{case.case_number}.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    y = height - 40

    def title(txt):
        nonlocal y
        y = _ensure_room(c, y, height)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, txt)
        y -= 16

    def line(txt):
        nonlocal y
        y = _ensure_room(c, y, height)
        c.setFont("Helvetica", 9)
        c.drawString(50, y, txt)
        y -= 12

    c.setFont("Helvetica-Bold", 15)
    c.drawString(40, y, "SISTEMA TRACKER - REPORTE INTEGRAL DE NOVEDAD")
    y -= 24
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Caso: {case.case_number}")
    y -= 14
    c.drawString(40, y, f"Fecha/Hora evento: {case.event_date or ''} {case.event_time or ''}")
    y -= 20

    title("Pantalla 01 - Generación de alerta")
    line(f"Activación de alarma: {case.alarm_activated or ''}")
    if (case.alarm_activated or '').upper() == 'SI':
        for t in [
            f"Proceso: {case.process or ''}",
            f"Subproceso: {case.sub_process or ''}",
            f"Jefe del local: {case.chief_name or ''}",
            f"Hora activación: {case.alert_time or ''}",
            f"Empresa de seguridad: {case.security_company or ''}",
            f"Operador empresa: {case.security_operator or ''}",
            f"Hora comunica al centro: {case.center_operator_time or ''}",
            f"Operador centro análisis: {case.center_operator_name or ''}",
        ]:
            line(t)
    else:
        line("Bloque operativo no visible ni registrado porque la activación de alarma fue NO.")
    y -= 6

    title("Pantalla 02 - Espacio tiempo / tienda")
    for t in [
        f"Central de monitoreo: {(case.central_code + ' ' + (case.central_name or '')).strip() if case.central_code else 'NO APLICA'}",
        f"Tienda: {case.store_code or ''} - {case.store_name or ''} ({case.format or ''})",
        f"Región/Distrito/Zona: {case.region or ''} / {case.district or ''} / {case.zone or ''}",
        f"Provincia/Cantón/Parroquia: {case.province or ''} / {case.canton or ''} / {case.parish or ''}",
        f"Subzona/Distrito/Circuito/Subcircuito: {case.subzone or ''} / {case.police_district or ''} / {case.circuit or ''} / {case.subcircuit or ''}",
        f"Código subcircuito: {case.subcircuit_code or ''}",
        f"Coordenadas: {case.lat or ''}, {case.lng or ''}",
        f"Afectación / Ubicación: {case.affectation or ''} / {case.novelty_location or ''}",
        f"Empresa-lugar / subtipo: {case.place_company or ''} / {case.place_subtype or ''}",
        f"Estado alerta: {case.alert_state or ''}",
        f"Razón descarte: {case.discarded_reason or ''}",
    ]:
        line(t)
    y -= 6

    title("Pantalla 03 - Novedad")
    for t in [
        f"Tipo/Subtipo/Modalidad: {case.novelty_type or ''} / {case.novelty_subtype or ''} / {case.modality or ''}",
        f"Número de integrantes: {case.number_of_members or ''}",
    ]:
        line(t)
    for chunk in _wrap_text(f"Detalle: {case.detail or ''}"):
        line(chunk)
    y -= 6

    title("Pantalla 04 - Víctimas")
    victims = _json_list(case.victims_json)
    if not victims:
        line("Sin víctimas registradas")
    else:
        for idx, victim in enumerate(victims, 1):
            line(f"Víctima {idx}: {victim.get('cedula','')} | {victim.get('nombres','')} | {victim.get('cargo','')}")
    y -= 6

    title("Pantalla 05 - Perfiles")
    suspects = _json_list(case.suspects_json)
    if not suspects:
        line("Sin sospechosos registrados")
    else:
        for idx, s in enumerate(suspects, 1):
            line(f"Sospechoso {idx}: {s.get('nombre','SIN NOMBRE')} | situación: {s.get('situacion','')} | antecedentes: {s.get('antecedentes','')} | seguimiento legal: {s.get('situacion_legal','')}")
            line(f"  Organización: {s.get('tipo_organizacion','')} / {s.get('organizacion_nombre','')}")
            line(f"  Nacionalidad: {s.get('nacionalidad','')} | Actividad: {s.get('actividad','')}")
            for chunk in _wrap_text(f"  Persona/perfil: {s.get('persona','')}"):
                line(chunk)
    y -= 6

    title("Pantalla 06 - Mercadería / bienes")
    merch = _json_list(case.merchandise_json)
    if not merch:
        line("Sin mercadería registrada")
    else:
        for idx, m in enumerate(merch, 1):
            line(f"Item {idx}: {m.get('producto','')} | estado: {m.get('estado','')} | cantidad: {m.get('cantidad','')} | estadístico: {m.get('estadistico','')} | valor: {m.get('valor','')}")
    y -= 6

    title("Pantalla 07 - Álbum fotográfico")
    photo_notes = _json_list(case.photo_notes_json)
    if not photo_notes:
        line("Sin notas de fotografías registradas")
    else:
        for idx, note in enumerate(photo_notes, 1):
            line(f"Foto {idx}: {note}")
    y -= 6

    title("Pantalla 08 - Seguimiento de la novedad")
    for t in [
        f"Delegación: {case.delegation or ''}",
        f"Fiscalía: {case.prosecutor_office or ''}",
        f"No. denuncia: {case.complaint_number or ''}",
    ]:
        line(t)
    for chunk in _wrap_text(f"Diligencias: {case.proceedings or ''}"):
        line(chunk)
    y -= 6

    title("Pantalla 09 - Situación legal del sospechoso")
    for chunk in _wrap_text(case.legal_summary or ""):
        line(chunk)

    c.save()
    return str(path)
