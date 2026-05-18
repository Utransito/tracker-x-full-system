from pathlib import Path
from sqlalchemy.orm import Session
import openpyxl
from .models import User, Store


ROLES = [
    ("Administrador General", "admin", "admin123", "admin"),
    ("Usuario Central de Monitoreo", "central", "123456", "central_monitoreo"),
    ("Analista de Hurtos", "hurtos", "123456", "analista_hurtos"),
    ("Analista de Delitos", "delitos", "123456", "analista_delitos"),
]


def seed_users(db: Session):
    if db.query(User).count() == 0:
        for full_name, username, password, role in ROLES:
            db.add(User(full_name=full_name, username=username, password=password, role=role))
        db.commit()


def _to_str(v):
    return "" if v is None else str(v).replace("\n", " ").strip()


def _to_float(v):
    if v is None or v == "":
        return None
    try:
        return float(str(v).replace(",", "."))
    except Exception:
        return None


def seed_stores(db: Session):
    if db.query(Store).first():
        return
    excel_path = Path(__file__).resolve().parent.parent / "lista de tias_geo operaciones.xlsx"
    inserted = 0
    if excel_path.exists():
        wb = openpyxl.load_workbook(excel_path, data_only=True)
        ws = wb[wb.sheetnames[0]]
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or row[0] is None:
                continue
            values = list(row) + [None] * (18 - len(row))
            db.add(Store(
                store_code=_to_str(values[0]),
                central_code=_to_str(values[1]) or _to_str(values[0]),
                format=_to_str(values[2]),
                store_name=_to_str(values[3]),
                region=_to_str(values[4]),
                district=_to_str(values[5]),
                zone=_to_str(values[6]),
                lat=_to_float(values[9]),
                lng=_to_float(values[10]),
                province=_to_str(values[11]),
                canton=_to_str(values[12]),
                parish=_to_str(values[13]),
                subzone=_to_str(values[14]),
                police_district=_to_str(values[15]),
                circuit=_to_str(values[16]),
                subcircuit=_to_str(values[17]),
                subcircuit_code=_to_str(values[18]) if len(values) > 18 else "",
            ))
            inserted += 1
        db.commit()
    if inserted == 0:
        fallback = [
            dict(store_code="116", central_code="103", format="TIA", store_name="OLMEDO", region="REGION 2", district="NO APLICA", zone="ZONA 12", lat=-2.198406, lng=-79.884537, province="GUAYAS", canton="GUAYAQUIL", parish="GUAYAQUIL-CHILE", subzone="DMG", police_district="9 DE OCTUBRE", circuit="CHILE", subcircuit="CHILE 3", subcircuit_code="09D03C01S03"),
            dict(store_code="310", central_code="310", format="TIA EXPRESS", store_name="TULIPANES", region="REGION 2", district="NO APLICA", zone="ZONA 10", lat=-2.246129, lng=-79.890374, province="GUAYAS", canton="GUAYAQUIL", parish="GUAYAQUIL-7 LAGOS", subzone="DMG", police_district="SUR", circuit="7 LAGOS", subcircuit="7 LAGOS 3", subcircuit_code="09D01C04S03"),
        ]
        for row in fallback:
            db.add(Store(**row))
        db.commit()
