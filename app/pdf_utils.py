from pathlib import Path
import base64, tempfile
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


def _proceedings_payload(value):
    if not value:
        return {"summary": "", "items": []}
    try:
        data = json.loads(value)
        if isinstance(data, dict):
            return {"summary": data.get("summary", "") or "", "items": data.get("items", []) or []}
    except Exception:
        pass
    return {"summary": value, "items": []}


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
    proceedings_payload = _proceedings_payload(case.proceedings)
    for chunk in _wrap_text(f"Solicitud de diligencias y actuaciones: {proceedings_payload.get('summary', '')}"):
        line(chunk)
    for idx, item in enumerate(proceedings_payload.get("items", []), 1):
        line(f"Diligencia {idx}: fecha {item.get('fecha', '')} | estado {item.get('estado', '')} | documento {item.get('documento', '')}")
    y -= 6

    title("Pantalla 09 - Situación legal del sospechoso")
    for chunk in _wrap_text(case.legal_summary or ""):
        line(chunk)

    c.save()
    if 'embedded_temp' in locals() and embedded_temp:
        try:
            Path(embedded_temp).unlink(missing_ok=True)
        except Exception:
            pass
    return str(path)


from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape

def generate_case_sheet_pdf(case, output_dir="generated_pdfs", image_path=None):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    path = Path(output_dir) / f"{case.case_number}_ficha.pdf"
    c = canvas.Canvas(str(path), pagesize=landscape(A4))
    width, height = landscape(A4)

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height-28, "FICHA DE IDENTIFICACIÓN DE NOVEDADES")
    c.line(30, height-42, width-30, height-42)

    left_x = 30
    top_y = height - 70
    label_w = 170
    left_w = width * 0.39
    img_x = left_x + left_w + 10
    img_w = width - img_x - 30
    row_h = 28

    suspects = _json_list(getattr(case, 'suspects_json', '[]'))
    first_suspect = suspects[0] if suspects else {}

    top_rows = [
        ("FECHA", case.event_date or ""),
        ("HORA", case.event_time or ""),
        ("CODIGO TIENDA", f"{case.store_code or ''}-{case.store_name or ''}"),
        ("UBICACION DE LA NOVEDAD", (case.novelty_location or "").upper()),
        ("NOVEDAD", (case.novelty_type or case.process or "").upper()),
        ("SUB TIPO NOVEDAD", (case.novelty_subtype or "").upper()),
        ("MODALIDAD", (case.modality or "").upper()),
        ("NUMERO DE INTEGRANTES", str(case.number_of_members or "")),
        ("MOVILIZACIÓN", str(first_suspect.get("movilizacion","") or "").lower()),
        ("ARMA IDENTIFICADA", str(first_suspect.get("arma_identificada","") or "").upper()),
        ("SUBZONA", case.subzone or ""),
        ("DISTRITO", case.police_district or ""),
        ("CIRCUITO", case.circuit or ""),
        ("SUBCIRCUITO", case.subcircuit or ""),
        ("COORDENADAS", f"({case.lat or ''}-{case.lng or ''})"),
    ]

    y = top_y
    value_w = left_w - label_w
    c.setFont("Helvetica", 10)
    for label, value in top_rows:
        c.rect(left_x, y-row_h, label_w, row_h)
        c.rect(left_x+label_w, y-row_h, value_w, row_h)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left_x+6, y-19, label)
        c.setFont("Helvetica", 10)
        c.drawString(left_x+label_w+6, y-19, str(value)[:60])
        y -= row_h

    photo_top = top_y
    photo_bottom = y
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(img_x + img_w/2, height-62, "FOTOGRAFÍA")
    c.rect(img_x, photo_bottom, img_w, photo_top - photo_bottom)
    if image_path and Path(image_path).exists():
        try:
            c.drawImage(ImageReader(str(image_path)), img_x+6, photo_bottom+6, img_w-12, (photo_top - photo_bottom)-12, preserveAspectRatio=True, anchor='c')
        except Exception:
            c.setFont("Helvetica", 10)
            c.drawCentredString(img_x + img_w/2, photo_bottom + (photo_top-photo_bottom)/2, "No se pudo renderizar la fotografía")
    else:
        c.setFont("Helvetica", 10)
        c.drawCentredString(img_x + img_w/2, photo_bottom + (photo_top-photo_bottom)/2, "Sin fotografía disponible")

    # Mantener la misma alineación vertical que la tabla principal superior
    full_label_w = label_w
    full_value_w = width - left_x - 30 - full_label_w

    actividad = first_suspect.get("actividad","") or ""
    actividad_lines = _wrap_text(actividad, 110)
    actividad_h = max(30, 13 * len(actividad_lines) + 10)
    c.rect(left_x, y-actividad_h, full_label_w, actividad_h)
    c.rect(left_x+full_label_w, y-actividad_h, full_value_w, actividad_h)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left_x+6, y-18, "ACTIVIDAD SOSPECHOSA")
    c.setFont("Helvetica", 10)
    vy = y-17
    for line in actividad_lines:
        c.drawString(left_x+full_label_w+6, vy, line)
        vy -= 12
    y -= actividad_h

    detalle = case.detail or ""
    detalle_lines = _wrap_text(detalle, 120)
    detalle_h = max(44, 13 * len(detalle_lines) + 14)
    c.rect(left_x, y-detalle_h, full_label_w, detalle_h)
    c.rect(left_x+full_label_w, y-detalle_h, full_value_w, detalle_h)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left_x+6, y-18, "DETALLE NOVEDAD")
    c.setFont("Helvetica", 10)
    vy = y-17
    for line in detalle_lines:
        c.drawString(left_x+full_label_w+6, vy, line)
        vy -= 12

    c.save()
    return path

def generate_summary_pdf(summary, output_dir="generated_pdfs"):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    path = Path(output_dir) / "reporte_resumen_tracker.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    y = height - 40

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "REPORTE EJECUTIVO - GDN")
    y -= 28

    def draw_table(title, data, x, y_top):
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y_top, title)
        y = y_top - 16
        for k, v in data:
            c.rect(x, y-18, 120, 22)
            c.rect(x+120, y-18, 60, 22)
            c.setFont("Helvetica", 10)
            c.drawString(x+4, y-4, str(k))
            c.drawRightString(x+172, y-4, str(v))
            y -= 22
        return y

    y1 = draw_table("TOTAL CASOS", [("INTERIOR", summary["location_counts"].get("Interior del local",0)), ("EXTERIOR", summary["location_counts"].get("Exterior del local",0)), ("TOTAL", summary["total_cases"])], 40, y)
    y2 = draw_table("NOVEDAD", list(summary["novelty_counts"].items()) + [("TOTAL", sum(summary["novelty_counts"].values()))], 250, y)
    y3 = draw_table("AFECTACIÓN", list(summary["affectation_counts"].items()) + [("TOTAL", summary["affectation_total"])], 40, y1-25)
    y4 = draw_table("ALERTAS", list(summary["alert_counts"].items()) + [("TOTAL", summary["alert_total"])], 40, y3-25)
    y5 = draw_table("TIENDAS", list(summary["store_format_counts"].items()) + [("TOTAL", summary["store_format_total"])], 40, y4-25)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, 90, "REGIÓN")
    x = 40
    for name, count in list(summary["region_counts"].items())[:10]:
        c.rect(x, 40, 70, 36)
        c.drawCentredString(x+35, 60, str(count))
        c.setFont("Helvetica", 8)
        c.drawCentredString(x+35, 46, str(name)[:12])
        x += 70

    c.save()
    return path




def generate_executive_dashboard_pdf(summary, output_dir="generated_pdfs"):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    path = Path(output_dir) / "reporte_ejecutivo_gdn.pdf"
    c = canvas.Canvas(str(path), pagesize=landscape(A4))
    width, height = landscape(A4)

    margin = 24
    gap = 14
    col_w = (width - margin * 2 - gap * 2) / 3
    top = height - 30

    c.setFont("Helvetica-Bold", 17)
    c.drawCentredString(width / 2, top, "REPORTE EJECUTIVO CONSOLIDADO - GDN")
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, top - 14, "Resumen gráfico y tabular construido a partir de los casos registrados en el sistema")

    def panel(x, y_top, w, h, title, title_fill=colors.HexColor("#f2f2f2")):
        c.setStrokeColor(colors.HexColor("#9a9a9a"))
        c.rect(x, y_top - h, w, h, stroke=1, fill=0)
        c.setFillColor(title_fill)
        c.rect(x, y_top - 24, w, 24, stroke=1, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x + w / 2, y_top - 16, title)
        return y_top - 28

    def simple_bar_chart(x, y_top, w, h, title, data_dict):
        body_top = panel(x, y_top, w, h, title)
        items = list(data_dict.items())
        items = items[:10]
        if not items:
            c.setFont("Helvetica", 9)
            c.drawCentredString(x + w / 2, y_top - h / 2, "Sin datos")
            return
        vals = [v for _, v in items]
        max_val = max(vals) or 1
        base_y = y_top - h + 32
        chart_h = h - 58
        count = len(items)
        slot = w / max(count, 1)
        bar_w = min(28, max(12, slot * 0.45))
        for idx, (label, value) in enumerate(items):
            bar_h = (value / max_val) * (chart_h - 26)
            bar_x = x + idx * slot + (slot - bar_w) / 2
            c.setFillColor(colors.HexColor("#7f7f7f"))
            c.rect(bar_x, base_y, bar_w, bar_h, stroke=1, fill=1)
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 7)
            c.drawCentredString(bar_x + bar_w / 2, base_y + bar_h + 8, str(value))
            short = str(label)[:12]
            c.drawCentredString(bar_x + bar_w / 2, base_y - 10, short)

    def simple_table(x, y_top, w, h, title, rows, header_fill=colors.HexColor("#f2f2f2")):
        body_top = panel(x, y_top, w, h, title, title_fill=header_fill)
        row_y = body_top
        usable_h = h - 30
        row_h = 18
        max_rows = max(1, int((usable_h - 4) / row_h))
        rows = rows[:max_rows]
        for idx, row in enumerate(rows):
            if isinstance(row, tuple) and len(row) == 2:
                left, right = row
            else:
                left, right = str(row), ""
            c.rect(x, row_y - row_h, w * 0.82, row_h, stroke=1, fill=0)
            c.rect(x + w * 0.82, row_y - row_h, w * 0.18, row_h, stroke=1, fill=0)
            c.setFont("Helvetica-Bold" if idx == 0 and title.upper().startswith("SUBTIPO") else "Helvetica", 8)
            c.drawString(x + 4, row_y - 12, str(left)[:44])
            c.drawRightString(x + w - 6, row_y - 12, str(right))
            row_y -= row_h
        if not rows:
            c.setFont("Helvetica", 9)
            c.drawCentredString(x + w / 2, y_top - h / 2, "Sin datos")

    left_x = margin
    mid_x = margin + col_w + gap
    right_x = margin + (col_w + gap) * 2
    grid_top = top - 24

    # left column
    simple_bar_chart(left_x, grid_top, col_w, 126, "AFECTACION", summary.get("affectation_counts", {}))
    simple_bar_chart(left_x, grid_top - 126 - gap, col_w, 126, "FORMATOS", summary.get("store_format_counts", {}))
    simple_bar_chart(left_x, grid_top - 252 - gap * 2, col_w, 170, "REGION", summary.get("region_counts", {}))

    # middle column
    simple_bar_chart(mid_x, grid_top, col_w, 126, "NOVEDAD", summary.get("novelty_counts", {}))
    subtype_rows = list(summary.get("subtype_counts", {}).items())
    simple_table(mid_x, grid_top - 126 - gap, col_w, 310, "SUBTIPO DE NOVEDAD", subtype_rows, header_fill=colors.HexColor("#d71920"))

    # right column
    ranking_rows = list(summary.get("store_ranking", {}).items())
    simple_table(right_x, grid_top, col_w, 450, "RANKING TIENDAS CASOS", ranking_rows, header_fill=colors.HexColor("#8c8c8c"))

    c.save()
    return str(path)


def generate_preinforme_pdf(case, output_dir: str, image_path: str | None = None, seguimiento_images=None, annex_images=None, analyst_name: str = "", asunto: str = "", detalle_asunto: str = "", acciones_realizadas: str = "", selected_annexes=None):
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from pathlib import Path
    from io import BytesIO

    seguimiento_images = list(seguimiento_images or [])
    annex_images = list(annex_images or [])
    selected_annexes = list(selected_annexes or [])

    path = Path(output_dir) / f"{case.case_number}_preinforme.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    left = 50
    right = width - 50
    top = height - 42

    def footer(page_no: int):
        c.setFont("Times-Italic", 11)
        c.setFillColor(colors.HexColor("#666666"))
        c.drawString(left, 22, "Sistema de Seguridad Corporativa TIA")
        c.drawRightString(right, 22, str(page_no))
        c.setFillColor(colors.black)

    def header(page_no: int):
        c.setFont("Helvetica-Bold", 22)
        c.setFillColor(colors.HexColor("#D71920"))
        c.drawString(left, top, "GDN")
        c.setFont("Helvetica", 8)
        c.drawString(left, top - 12, "CENTRO DE ANÁLISIS")
        c.drawString(left, top - 22, "Y SEGURIDAD EMPRESARIAL")
        c.setFont("Helvetica-Bold", 24)
        c.drawRightString(right, top, "Tía")
        c.setFillColor(colors.black)
        c.line(left, top - 30, right, top - 30)
        footer(page_no)

    def wrap_lines(text, max_chars=95):
        raw_words = str(text or "").replace("\r", " ").replace("\n", " ").split()
        if not raw_words:
            return [""]
        words = []
        for word in raw_words:
            if len(word) <= max_chars:
                words.append(word)
            else:
                for i in range(0, len(word), max_chars):
                    words.append(word[i:i+max_chars])
        lines, current = [], []
        for word in words:
            probe = " ".join(current + [word]).strip()
            if len(probe) <= max_chars:
                current.append(word)
            else:
                if current:
                    lines.append(" ".join(current))
                current = [word]
        if current:
            lines.append(" ".join(current))
        return lines or [""]

    def _split_word_to_width(word, max_width, font, size):
        if c.stringWidth(word, font, size) <= max_width:
            return [word]
        pieces = []
        current = ""
        for ch in word:
            probe = current + ch
            if current and c.stringWidth(probe, font, size) > max_width:
                pieces.append(current)
                current = ch
            else:
                current = probe
        if current:
            pieces.append(current)
        return pieces or [word]

    def layout_text(text, max_width, font="Helvetica", size=11):
        paragraphs = str(text or "").replace("\r", "").split("\n")
        laid_out = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                laid_out.append({"blank": True})
                continue
            words = []
            for raw_word in para.split():
                words.extend(_split_word_to_width(raw_word, max_width, font, size))
            current = []
            for word in words:
                if not current:
                    current = [word]
                    continue
                probe = " ".join(current + [word])
                if c.stringWidth(probe, font, size) <= max_width:
                    current.append(word)
                else:
                    laid_out.append({"words": current[:]})
                    current = [word]
            if current:
                laid_out.append({"words": current[:], "last": True})
        return laid_out

    def draw_layout_lines(y, laid_out, x, max_width, font="Helvetica", size=11, leading=16, min_y=78, page_ref=None):
        c.setFont(font, size)
        space_width = c.stringWidth(" ", font, size)
        for line in laid_out:
            if y < min_y:
                c.showPage()
                if page_ref is not None:
                    page_ref[0] += 1
                    header(page_ref[0])
                else:
                    header(1)
                y = top - 50
                c.setFont(font, size)
                space_width = c.stringWidth(" ", font, size)
            if line.get("blank"):
                y -= leading
                continue
            words = line.get("words", [])
            text_line = " ".join(words)
            if len(words) <= 1 or line.get("last"):
                c.drawString(x, y, text_line)
            else:
                words_width = sum(c.stringWidth(w, font, size) for w in words)
                gaps = len(words) - 1
                base_total = words_width + space_width * gaps
                extra = max(0, max_width - base_total)
                gap_extra = extra / gaps if gaps else 0
                cursor_x = x
                for idx, word in enumerate(words):
                    c.drawString(cursor_x, y, word)
                    cursor_x += c.stringWidth(word, font, size)
                    if idx < gaps:
                        cursor_x += space_width + gap_extra
            y -= leading
        return y

    def draw_label_value(y, label, value, value_x=162, value_width=None):
        c.setFont("Helvetica-Bold", 12)
        c.drawString(left, y, label)
        value_width = value_width or (right - value_x)
        lines = layout_text(value, value_width, font="Helvetica-Oblique", size=12)
        y_end = draw_layout_lines(y, lines, value_x, value_width, font="Helvetica-Oblique", size=12, leading=16, min_y=78)
        return y_end - 10

    def draw_text_block(y, text, x=None, width_chars=92, font="Helvetica-Oblique", size=12, leading=18, min_y=78, page_ref=None, max_width=None):
        x = x or left + 42
        if max_width is None:
            max_width = right - x
        lines = layout_text(text, max_width, font=font, size=size)
        return draw_layout_lines(y, lines, x, max_width, font=font, size=size, leading=leading, min_y=min_y, page_ref=page_ref)

    def draw_image_box(x, y_top, w, h, path_img=None, placeholder="Sin imagen disponible"):
        c.rect(x, y_top - h, w, h)
        if path_img:
            try:
                img_source = None
                if isinstance(path_img, str) and path_img.startswith("data:image"):
                    raw = path_img.split(",", 1)[1]
                    img_source = ImageReader(BytesIO(base64.b64decode(raw)))
                elif isinstance(path_img, str) and Path(path_img).exists():
                    img_source = ImageReader(str(path_img))
                if img_source is not None:
                    c.drawImage(img_source, x + 6, y_top - h + 6, w - 12, h - 12, preserveAspectRatio=True, anchor='c')
                    return
            except Exception:
                pass
        c.setFont("Helvetica", 10)
        c.drawCentredString(x + w / 2, y_top - h / 2, placeholder)

    def draw_person_card(x, y_top, w, h, person):
        c.rect(x, y_top - h, w, h)
        img_h = 84
        person_img = person.get("foto_persona", "") or person.get("foto", "")
        if person_img:
            draw_image_box(x + 6, y_top - 6, w - 12, img_h, person_img, "Sin fotografía")
        else:
            draw_image_box(x + 6, y_top - 6, w - 12, img_h, None, "")
            c.setFillColor(colors.HexColor("#222222"))
            c.circle(x + w / 2, y_top - 43, 17, stroke=0, fill=1)
            c.roundRect(x + w / 2 - 26, y_top - 92, 52, 32, 9, stroke=0, fill=1)
            c.setFillColor(colors.black)
        row_y = y_top - img_h - 8
        rows = [
            ("Nombre:", person.get("nombre", "")),
            ("Sexo:", person.get("sexo", "")),
            ("Edad aprox.:", person.get("edad_aprox", person.get("edad", ""))),
            ("Etnia:", person.get("etnia", "")),
            ("Antecedentes:", person.get("antecedentes", "")),
            ("Movilización:", person.get("movilizacion", "")),
            ("Arma:", person.get("arma_identificada", "")),
            ("Organización:", person.get("organizacion_nombre", "")),
        ]
        label_w = 78
        value_x = x + label_w + 6
        value_w = w - label_w - 12
        for label, value in rows:
            c.line(x, row_y, x + w, row_y)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(x + 4, row_y - 10, label)
            c.setFont("Helvetica", 8)
            value_lines = layout_text(str(value or ""), value_w, font="Helvetica", size=8)
            value_lines = [ln for ln in value_lines if not ln.get("blank")][:2] or [{"words":[""]}]
            yy = row_y - 10
            for ln in value_lines:
                c.drawString(value_x, yy, " ".join(ln.get("words", [])))
                yy -= 8
            row_y -= 18

    def draw_vehicle_card(x, y_top, w, h, vehicle):
        c.rect(x, y_top - h, w, h)
        img_h = 90
        vehicle_img = vehicle.get("foto_vehiculo", "") or vehicle.get("foto", "")
        if vehicle_img:
            draw_image_box(x + 6, y_top - 6, w - 12, img_h, vehicle_img, "Sin fotografía")
        else:
            draw_image_box(x + 6, y_top - 6, w - 12, img_h, None, "")
            c.setStrokeColor(colors.black)
            c.setLineWidth(2)
            base = y_top - 56
            c.line(x + 32, base, x + w - 32, base)
            c.circle(x + 52, base - 5, 13, stroke=1, fill=0)
            c.circle(x + w - 52, base - 5, 13, stroke=1, fill=0)
            c.roundRect(x + 40, base + 2, w - 80, 24, 9, stroke=1, fill=0)
            c.setLineWidth(1)
        row_y = y_top - img_h - 8
        rows = [
            ("Tipo vehículo:", vehicle.get("tipo_vehiculo", "")),
            ("Marca:", vehicle.get("marca", "")),
            ("Placas:", vehicle.get("placas", "")),
            ("Color:", vehicle.get("color", "")),
        ]
        label_w = 96
        value_x = x + label_w + 6
        value_w = w - label_w - 12
        for label, value in rows:
            c.line(x, row_y, x + w, row_y)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x + 4, row_y - 10, label)
            c.setFont("Helvetica", 9)
            value_lines = layout_text(str(value or ""), value_w, font="Helvetica", size=9)
            value_lines = [ln for ln in value_lines if not ln.get("blank")][:2] or [{"words":[""]}]
            yy = row_y - 10
            for ln in value_lines:
                c.drawString(value_x, yy, " ".join(ln.get("words", [])))
                yy -= 9
            row_y -= 20

    # Data
    try:
        photo_notes = json.loads(case.photo_notes_json or "[]")
        if not isinstance(photo_notes, list):
            photo_notes = []
    except Exception:
        photo_notes = []

    try:
        suspects = json.loads(case.suspects_json or "[]")
        if not isinstance(suspects, list):
            suspects = []
    except Exception:
        suspects = []

    try:
        vehicles = json.loads(case.vehicles_json or "[]")
        if not isinstance(vehicles, list):
            vehicles = []
    except Exception:
        vehicles = []

    detalle_asunto = detalle_asunto or " / ".join([v for v in [case.novelty_type or "", case.novelty_subtype or "", case.modality or ""] if v])
    actions_text = (acciones_realizadas or "").strip()

    # PAGE 1
    header(1)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, top - 78, "PREINFORME")
    c.drawCentredString(width / 2, top - 100, "DE MONITOREO")

    y = top - 142
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, top - 122, f"No. {case.case_number or ''}")
    y += 2
    y = draw_label_value(y, "ASUNTO:", asunto or case.novelty_subtype or case.novelty_type or "")
    y = draw_label_value(y, "FORMATO:", case.format or "")
    y = draw_label_value(y, "NOMBRE TIENDA:", f"{case.store_code or ''} - {case.store_name or ''}")
    y = draw_label_value(y, "SUBZONA:", case.subzone or "")
    y = draw_label_value(y, "DISTRITO:", case.police_district or "")
    y = draw_label_value(y, "SUBCIRCUITO:", case.subcircuit or "")
    y = draw_label_value(y, "FECHA:", case.event_date or "")
    y = draw_label_value(y, "HORA:", case.event_time or "")
    y = draw_label_value(y, "DETALLE ASUNTO:", detalle_asunto or "")

    c.setFont("Helvetica-Bold", 13)
    c.drawString(left, y - 6, "NARRACIÓN DE LOS HECHOS:")
    page_ref = [1]
    y = draw_text_block(y - 28, case.detail or "", x=left + 10, font="Helvetica", size=11, leading=16, min_y=78, page_ref=page_ref, max_width=right - (left + 10))

    # PAGE 2+ (seguimiento de la novedad con todas las fotos registradas)
    current_page = page_ref[0]
    if y < 330:
        current_page += 1
        c.showPage()
        header(current_page)
        y = top - 50
    else:
        y -= 18
    c.setFont("Helvetica-Bold", 14)
    c.drawString(left, y, "I.    SEGUIMIENTO DE LA NOVEDAD:")
    y -= 26

    display_images = list(seguimiento_images or [])
    notes = list(photo_notes or [])

    total_registros = max(len(display_images), len(notes), 1)
    while len(display_images) < total_registros:
        display_images.append(None)
    while len(notes) < total_registros:
        notes.append("Sin descripción registrada")

    note_x = left + 14
    note_width = right - note_x
    image_w = width - 120
    box_h = 145

    for idx in range(total_registros):
        img = display_images[idx]
        note_text = notes[idx] if idx < len(notes) else "Sin descripción registrada"
        note_lines = layout_text(note_text, note_width, font="Helvetica", size=11)
        visible_lines = len(note_lines) if note_lines else 1
        text_height = max(18, visible_lines * 15)
        required_height = 18 + text_height + box_h + 16

        # Si no hay espacio suficiente, crear nueva página y continuar
        if y - required_height < 70:
            current_page += 1
            c.showPage()
            header(current_page)
            y = top - 50

        c.setFont("Helvetica-Bold", 12)
        c.drawString(left + 14, y, f"REGISTRO {idx + 1}")
        y -= 20

        y = draw_layout_lines(y, note_lines, note_x, note_width, font="Helvetica", size=11, leading=15, min_y=60)

        draw_image_box(left + 14, y - 2, image_w, box_h, img, "Sin imagen registrada")
        y -= (box_h + 14)

    # PAGE 3+  (perfiles completos)
    current_page += 1
    c.showPage()
    header(current_page)
    y = top - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(left, y, "II.    PERFILES:")
    y -= 24

    people = list(suspects or [])
    vehicle_list = list(vehicles or [])

    c.setFont("Helvetica-Bold", 12)
    c.drawString(left + 14, y, "Personas:")
    y -= 14

    person_card_w = 205
    person_card_h = 236
    person_gap = 12
    person_x1 = left + 28
    person_x2 = person_x1 + person_card_w + person_gap

    if not people:
        if y - person_card_h < 90:
            current_page += 1
            c.showPage()
            header(current_page)
            y = top - 50
            c.setFont("Helvetica-Bold", 14)
            c.drawString(left, y, "II.    PERFILES:")
            y -= 24
            c.setFont("Helvetica-Bold", 12)
            c.drawString(left + 14, y, "Personas:")
            y -= 14
        draw_person_card(person_x1, y, person_card_w, person_card_h, {})
        draw_person_card(person_x2, y, person_card_w, person_card_h, {})
        y -= person_card_h + 30
    else:
        for i in range(0, len(people), 2):
            if y - person_card_h < 90:
                current_page += 1
                c.showPage()
                header(current_page)
                y = top - 50
                c.setFont("Helvetica-Bold", 14)
                c.drawString(left, y, "II.    PERFILES:")
                y -= 24
                c.setFont("Helvetica-Bold", 12)
                c.drawString(left + 14, y, "Personas:")
                y -= 14

            draw_person_card(person_x1, y, person_card_w, person_card_h, people[i])
            if i + 1 < len(people):
                draw_person_card(person_x2, y, person_card_w, person_card_h, people[i + 1])
            y -= person_card_h + 24

    if y < 150:
        current_page += 1
        c.showPage()
        header(current_page)
        y = top - 50

    c.setFont("Helvetica-Bold", 12)
    c.drawString(left + 14, y, "Vehículos:")
    y -= 14

    vehicle_card_w = 220
    vehicle_card_h = 178
    vehicle_gap = 16
    vehicle_x1 = left + 14
    vehicle_x2 = vehicle_x1 + vehicle_card_w + vehicle_gap

    if not vehicle_list:
        if y - vehicle_card_h < 90:
            current_page += 1
            c.showPage()
            header(current_page)
            y = top - 50
            c.setFont("Helvetica-Bold", 12)
            c.drawString(left + 14, y, "Vehículos:")
            y -= 14
        draw_vehicle_card(vehicle_x1, y, vehicle_card_w, vehicle_card_h, {})
        y -= vehicle_card_h + 28
    else:
        for i in range(0, len(vehicle_list), 2):
            if y - vehicle_card_h < 90:
                current_page += 1
                c.showPage()
                header(current_page)
                y = top - 50
                c.setFont("Helvetica-Bold", 12)
                c.drawString(left + 14, y, "Vehículos:")
                y -= 14

            draw_vehicle_card(vehicle_x1, y, vehicle_card_w, vehicle_card_h, vehicle_list[i])
            if i + 1 < len(vehicle_list):
                draw_vehicle_card(vehicle_x2, y, vehicle_card_w, vehicle_card_h, vehicle_list[i + 1])
            y -= vehicle_card_h + 24

    # PAGE 4+
    if not selected_annexes and annex_images:
        for idx, path_img in enumerate(annex_images, start=1):
            selected_annexes.append({"title": f"Anexo {idx}", "path": path_img})
    if not selected_annexes and image_path:
        selected_annexes.append({"title": "Anexo 1", "path": image_path})

    current_page += 1
    c.showPage()
    header(current_page)
    y = top - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(left, y, "III.    ANEXO:")
    y -= 28

    box_w = 175
    box_h = 150

    for idx, annex in enumerate(selected_annexes, start=1):
        required = 210
        if y - required < 120:
            current_page += 1
            c.showPage()
            header(current_page)
            y = top - 50
        c.setFont("Helvetica-Bold", 12)
        c.drawString(left + 26, y, f"Anexo {idx}")
        y -= 22
        c.setFont("Helvetica-Bold", 12)
        c.drawString(left + 26, y, f"Título: {annex.get('title', f'Anexo {idx}')}")
        y -= 14
        draw_image_box(left + 22, y, box_w, box_h, annex.get("path"), f"Sin anexo {idx}")
        y -= 192

    if y < 180:
        current_page += 1
        c.showPage()
        header(current_page)
        y = top - 50

    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#4C72D9"))
    c.drawString(left, y, "IV.    ACCIONES REALIZADAS:")
    c.setFillColor(colors.black)
    y -= 28
    y = draw_text_block(y, actions_text, x=left + 22, font="Helvetica-Oblique", size=12, leading=18, max_width=(right - (left + 22)), page_ref=[current_page])

    c.setFont("Helvetica-Oblique", 12)
    c.drawCentredString(width / 2, 82, analyst_name or "Usuario del sistema")
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(width / 2, 60, "FIRMA DEL ANALISTA")

    c.save()
    return str(path)
