from pathlib import Path
from uuid import uuid4
from typing import Optional
import json

from fastapi import FastAPI, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

from .database import Base, engine, get_db, SessionLocal
from .models import User, Store, Case, CaseFile
from .seed import seed_users, seed_stores
from .pdf_utils import generate_case_pdf

app = FastAPI(title="TRACKER X - Flujo Cliente")
app.add_middleware(SessionMiddleware, secret_key="trackerx-secret-key-change-me")

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
PDF_DIR = BASE_DIR / "generated_pdfs"
UPLOAD_DIR.mkdir(exist_ok=True)
PDF_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))

Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    seed_users(db)
    seed_stores(db)

PROCESS_OPTIONS = ["HURTO", "DELITO"]
SUBPROCESS_OPTIONS = ["Seguimiento sospechoso", "Registro novedad"]
SECURITY_COMPANIES = ["SECURYTY WORDL", "LAAR SEGURIDAD"]
ALERT_STATES = ["Confirmado", "Descartado"]
DISCARDED_REASONS = ["No procede a la actividad delictual", "Error por manipular el dispositivo", "Simulacro"]
AFFECTATIONS = ["Directa", "Indirecta"]
NOVELTY_LOCATIONS = ["Interior del local", "Exterior del local"]
PLACES = ["Banco del Pacifico", "Banco de Guayaquil", "Wester Union", "Tuti", "Vía Pública", "Lugares de acceso público", "Local comercial", "Residencias", "Tía"]
PLACE_SUBTYPES = ["Cajero", "Tienda", "Banco del barrio", "Farmacia", "Panadería", "Hotel/motel", "Estacionamiento", "Parque", "Vía pública", "Centro comercial", "Casa/departamento", "Conjunto residencial"]
POLICE_UNITS = [
    "Unidad Policial (Desconcentración)",
    "Dirección General de Seguridad Ciudadana y Orden Público",
    "Subzona de Policía",
    "Distrito de Policía",
    "Circuito de Policía",
    "Subcircuito de Policía",
]
REQUESTED_BY = ["Centro de análisis", "Central de monitoreo", "Jefe de local", "Guardia de seguridad", "Operador CCTV", "Otro"]
NOVELTY_TYPES = ["DELITO", "CONTRAVENCIÓN", "RIESGOS", "TRÁNSITO"]
NOVELTY_MATRIX = {
    "DELITO": {
        "ROBO A UNIDADES ECONOMICAS": ["OCULTAMIENTO DE MERCADERIA", "DESCUIDEROS", "FORZAMIENTO", "INTIMIDACIÓN", "APROVECHAMIENTO DE DESCUIDO"],
        "ROBO A PERSONAS": ["ARRANCHE", "INTIMIDACIÓN", "ARREBATO", "APROVECHAMIENTO DE DESCUIDO"],
        "DAÑOS A BIEN AJENO": ["VANDALISMO", "DESTRUCCIÓN", "GRAFITI", "ROTURA DE BIENES"],
        "ASOCIACIÓN ILÍCITA": ["COORDINACIÓN DELICTIVA", "PARTICIPACIÓN GRUPAL", "PLANIFICACIÓN"],
    },
    "CONTRAVENCIÓN": {
        "ESCÁNDALO": ["ALTERACIÓN DEL ORDEN", "AGRESIÓN VERBAL", "PELEA"],
        "CONSUMO DE ALCOHOL": ["INGESTA EN EL LUGAR", "EMBRIAGUEZ", "ALTERACIÓN DEL ORDEN"],
        "ACTOS INDEBIDOS": ["ACOSO", "TOCAMIENTOS", "COMPORTAMIENTO INAPROPIADO"],
    },
    "RIESGOS": {
        "PERSONA SOSPECHOSA": ["MERODEO", "VIGILANCIA DEL ENTORNO", "CIRCULACIÓN REPETITIVA", "CONDUCTA EVASIVA"],
        "VEHÍCULO SOSPECHOSO": ["ESTACIONAMIENTO ESTRATÉGICO", "PERMANENCIA PROLONGADA", "PLACAS CUBIERTAS", "HUÍDA REPENTINA"],
        "AMENAZA": ["VERBAL", "ESCRITA", "INTIMIDACIÓN", "AMEDRENTAMIENTO"],
    },
    "TRÁNSITO": {
        "ACCIDENTE DE TRÁNSITO": ["COLISIÓN", "ATROPELLO", "CHOQUE", "DAÑOS MATERIALES"],
        "INCIDENTE VEHICULAR": ["MANIOBRA PELIGROSA", "OBSTRUCCIÓN", "INGRESO INDEBIDO"],
    },
}
SUSPECT_STATUS = ["Aprehendido", "No aprehendido", "Procesado"]
ANTECEDENTES = ["Reincidente", "Sospechoso no reconocido"]
TIPOS_ORGANIZACION = ["Delincuencia común", "Delincuencia organizada", "Delincuente habitual", "Personas en situación de calle", "Personas en estado de embriaguez", "Personas bajo efecto de sustancias psicotrópicas", "Personas con problemas mentales"]
ORG_NAMES = ["Águilas", "AguilasKiller", "Ak47", "Caballeros Oscuros", "ChoneKiller", "Choneros", "Corvicheros", "Cubanos", "Fatales", "Latin Kings", "Lobos", "Los Tiburones", "Mafia18", "R7", "Tiguerones", "No reconocida"]
NATIONALITIES = ["Ecuador", "Perú", "Colombia", "Argentina", "Brasil", "Venezuela", "Panamá", "México", "EEUU", "Canadá", "España", "Italia", "Uruguay", "Paraguay"]
PRODUCT_TYPES = ["Mercadería", "Dinero", "Bienes particulares"]
MERCH_STATES = ["Recuperada", "Sustraída", "Pagada por consumo"]
LEGAL_STATUSES = ["APREHENDIDO", "NO APREHENDIDO", "PROCESADO", "SOBRESEÍDO", "SENTENCIADO", "AUDIENCIA PENDIENTE"]
PRECAUTIONARY_MEASURES = ["Prisión preventiva", "Presentación periódica", "Prohibición de salida del país", "Medidas alternativas", "Ninguna", "En análisis"]


@app.head("/")
@app.get("/healthz")
def health() -> PlainTextResponse:
    return PlainTextResponse("ok")


def current_user(request: Request, db: Session):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


def require_login(request: Request, db: Session):
    user = current_user(request, db)
    if not user:
        raise HTTPException(status_code=401)
    return user


def require_admin(request: Request, db: Session):
    user = require_login(request, db)
    if user.role != "admin":
        raise HTTPException(status_code=403)
    return user


def build_case_number(db: Session, base_code: str):
    year = 2026
    count = db.query(func.count(Case.id)).scalar() or 0
    return f"{base_code}{year}{str(count + 1).zfill(5)}"


def save_upload(upload: Optional[UploadFile], file_type: str, case_id: int, db: Session):
    if not upload or not upload.filename:
        return None
    ext = Path(upload.filename).suffix
    safe_name = f"{uuid4().hex}{ext}"
    target = UPLOAD_DIR / safe_name
    with target.open("wb") as f:
        f.write(upload.file.read())
    rec = CaseFile(case_id=case_id, file_type=file_type, original_name=upload.filename, stored_name=safe_name)
    db.add(rec)
    return rec


def to_json(value: str | None):
    if not value:
        return "[]"
    try:
        json.loads(value)
        return value
    except Exception:
        return "[]"


def central_name_for(db: Session, central_code: str | None):
    if not central_code:
        return ""
    base = db.query(Store).filter(Store.store_code == central_code).first()
    return base.store_name if base else ""


def common_context(user):
    return {
        "user": user,
        "process_options": PROCESS_OPTIONS,
        "subprocess_options": SUBPROCESS_OPTIONS,
        "security_companies": SECURITY_COMPANIES,
        "alert_states": ALERT_STATES,
        "discarded_reasons": DISCARDED_REASONS,
        "affectations": AFFECTATIONS,
        "novelty_locations": NOVELTY_LOCATIONS,
        "places": PLACES,
        "place_subtypes": PLACE_SUBTYPES,
        "police_units": POLICE_UNITS,
        "requested_by_options": REQUESTED_BY,
        "novelty_types": NOVELTY_TYPES,
        "suspect_status_options": SUSPECT_STATUS,
        "antecedentes_options": ANTECEDENTES,
        "tipos_organizacion": TIPOS_ORGANIZACION,
        "org_names": ORG_NAMES,
        "nationalities": NATIONALITIES,
        "product_types": PRODUCT_TYPES,
        "merch_states": MERCH_STATES,
        "legal_statuses": LEGAL_STATUSES,
        "precautionary_measures": PRECAUTIONARY_MEASURES,
        "novelty_matrix": NOVELTY_MATRIX,
    }


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if user:
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None, "user": None})


@app.post("/login", response_class=HTMLResponse)
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username, User.password == password).first()
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Credenciales inválidas", "user": None})
    request.session["user_id"] = user.id
    return RedirectResponse("/dashboard", status_code=302)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = require_login(request, db)
    case_count = db.query(func.count(Case.id)).scalar() or 0
    confirmed_count = db.query(func.count(Case.id)).filter(Case.alert_state == "Confirmado").scalar() or 0
    stores_count = db.query(func.count(Store.id)).scalar() or 0
    recent_cases = db.query(Case).order_by(Case.created_at.desc()).limit(10).all()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "case_count": case_count,
        "confirmed_count": confirmed_count,
        "stores_count": stores_count,
        "recent_cases": recent_cases,
    })


@app.get("/cases/new", response_class=HTMLResponse)
def new_case(request: Request, db: Session = Depends(get_db)):
    user = require_login(request, db)
    stores = db.query(Store).order_by(Store.store_code).all()
    ctx = common_context(user)
    ctx.update({"request": request, "stores": stores})
    return templates.TemplateResponse("case_form.html", ctx)


@app.post("/cases/new")
async def create_case(
    request: Request,
    police_unit: str = Form(""),
    requested_by: str = Form(""),
    process: str = Form(""),
    sub_process: str = Form(""),
    alarm_activated: str = Form("NO"),
    chief_name: str = Form(""),
    alert_time: str = Form(""),
    security_company: str = Form(""),
    security_operator: str = Form(""),
    center_operator_time: str = Form(""),
    center_operator_name: str = Form(""),
    central_code: str = Form(""),
    store_code: str = Form(...),
    affectation: str = Form(""),
    novelty_location: str = Form(""),
    place_company: str = Form(""),
    place_subtype: str = Form(""),
    event_date: str = Form(""),
    event_time: str = Form(""),
    alert_state: str = Form(""),
    discarded_reason: str = Form(""),
    novelty_type: str = Form(""),
    novelty_subtype: str = Form(""),
    modality: str = Form(""),
    number_of_members: int = Form(1),
    detail: str = Form(""),
    victims_json: str = Form("[]"),
    suspects_json: str = Form("[]"),
    merchandise_json: str = Form("[]"),
    photo_notes_json: str = Form("[]"),
    vehicles_json: str = Form("[]"),
    processed_json: str = Form("[]"),
    delegation: str = Form(""),
    prosecutor_office: str = Form(""),
    prosecutor_name: str = Form(""),
    complaint_number: str = Form(""),
    complaint_date: str = Form(""),
    judicial_unit: str = Form(""),
    cause_number: str = Form(""),
    proceedings: str = Form(""),
    legal_status: str = Form(""),
    hearing_date: str = Form(""),
    precautionary_measure: str = Form(""),
    legal_summary: str = Form(""),
    gallery_1: UploadFile | None = File(None),
    gallery_2: UploadFile | None = File(None),
    gallery_3: UploadFile | None = File(None),
    gallery_4: UploadFile | None = File(None),
    gallery_5: UploadFile | None = File(None),
    gallery_6: UploadFile | None = File(None),
    gallery_7: UploadFile | None = File(None),
    gallery_8: UploadFile | None = File(None),
    gallery_9: UploadFile | None = File(None),
    gallery_10: UploadFile | None = File(None),
    gallery_11: UploadFile | None = File(None),
    gallery_12: UploadFile | None = File(None),
    gallery_13: UploadFile | None = File(None),
    gallery_14: UploadFile | None = File(None),
    gallery_15: UploadFile | None = File(None),
    gallery_16: UploadFile | None = File(None),
    gallery_17: UploadFile | None = File(None),
    gallery_18: UploadFile | None = File(None),
    gallery_19: UploadFile | None = File(None),
    gallery_20: UploadFile | None = File(None),
    merchandise_photo: UploadFile | None = File(None),
    denuncia_pdf: UploadFile | None = File(None),
    diligencias_pdf: UploadFile | None = File(None),
    audiencia_pdf: UploadFile | None = File(None),
    db: Session = Depends(get_db)
):
    user = require_login(request, db)
    store = db.query(Store).filter(Store.store_code == store_code).first()
    if not store:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")

    process_value = process if alarm_activated == "SI" else ""
    base_code = central_code if process_value == "HURTO" and central_code else store_code
    case_number = build_case_number(db, base_code)
    case = Case(
        case_number=case_number,
        police_unit=police_unit,
        requested_by=requested_by,
        process=process_value,
        sub_process=sub_process if alarm_activated == "SI" else "",
        alarm_activated=alarm_activated,
        chief_name=chief_name if alarm_activated == "SI" else "",
        alert_time=alert_time if alarm_activated == "SI" else "",
        security_company=security_company if alarm_activated == "SI" else "",
        security_operator=security_operator if alarm_activated == "SI" else "",
        center_operator_time=center_operator_time if alarm_activated == "SI" else "",
        center_operator_name=center_operator_name if alarm_activated == "SI" else "",
        central_code=central_code if process_value == "HURTO" else "",
        central_name=central_name_for(db, central_code) if process_value == "HURTO" else "",
        store_code=store.store_code,
        store_name=store.store_name,
        format=store.format,
        region=store.region,
        district=store.district,
        zone=store.zone,
        province=store.province,
        canton=store.canton,
        parish=store.parish,
        subzone=store.subzone,
        police_district=store.police_district,
        circuit=store.circuit,
        subcircuit=store.subcircuit,
        subcircuit_code=store.subcircuit_code,
        lat=str(store.lat or ""),
        lng=str(store.lng or ""),
        affectation=affectation,
        novelty_location=novelty_location,
        place_company=place_company,
        place_subtype=place_subtype,
        event_date=event_date,
        event_time=event_time,
        alert_state=alert_state,
        discarded_reason=discarded_reason,
        novelty_type=novelty_type,
        novelty_subtype=novelty_subtype,
        modality=modality,
        number_of_members=number_of_members,
        detail=detail,
        victims_json=to_json(victims_json),
        suspects_json=to_json(suspects_json),
        merchandise_json=to_json(merchandise_json),
        photo_notes_json=to_json(photo_notes_json),
        vehicles_json=to_json(vehicles_json),
        processed_json=to_json(processed_json),
        delegation=delegation,
        prosecutor_office=prosecutor_office,
        prosecutor_name=prosecutor_name,
        complaint_number=complaint_number,
        complaint_date=complaint_date,
        judicial_unit=judicial_unit,
        cause_number=cause_number,
        proceedings=proceedings,
        legal_status=legal_status,
        hearing_date=hearing_date,
        precautionary_measure=precautionary_measure,
        legal_summary=legal_summary,
        created_by=user.id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    uploads = [
        gallery_1, gallery_2, gallery_3, gallery_4, gallery_5,
        gallery_6, gallery_7, gallery_8, gallery_9, gallery_10,
        gallery_11, gallery_12, gallery_13, gallery_14, gallery_15,
        gallery_16, gallery_17, gallery_18, gallery_19, gallery_20,
    ]
    for up in uploads:
        save_upload(up, "gallery_image", case.id, db)
    for up, file_type in [
        (merchandise_photo, "merchandise_photo"),
        (denuncia_pdf, "denuncia_pdf"),
        (diligencias_pdf, "diligencias_pdf"),
        (audiencia_pdf, "audiencia_pdf"),
    ]:
        save_upload(up, file_type, case.id, db)
    db.commit()
    return RedirectResponse(f"/cases/{case.id}", status_code=302)


@app.get("/cases", response_class=HTMLResponse)
def list_cases(request: Request, db: Session = Depends(get_db)):
    user = require_login(request, db)
    cases = db.query(Case).order_by(Case.created_at.desc()).all()
    return templates.TemplateResponse("case_list.html", {"request": request, "user": user, "cases": cases})


@app.get("/cases/{case_id}", response_class=HTMLResponse)
def case_detail(case_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_login(request, db)
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("case_detail.html", {
        "request": request,
        "user": user,
        "case": case,
        "victims": json.loads(case.victims_json or "[]"),
        "suspects": json.loads(case.suspects_json or "[]"),
        "merch": json.loads(case.merchandise_json or "[]"),
        "photo_notes": json.loads(case.photo_notes_json or "[]"),
        "vehicles": json.loads(case.vehicles_json or "[]"),
        "processed": json.loads(case.processed_json or "[]"),
    })


@app.get("/cases/{case_id}/pdf")
def case_pdf(case_id: int, request: Request, db: Session = Depends(get_db)):
    require_login(request, db)
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404)
    pdf_path = generate_case_pdf(case, str(PDF_DIR))
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"{case.case_number}.pdf")


@app.get("/users", response_class=HTMLResponse)
def users_page(request: Request, db: Session = Depends(get_db)):
    user = require_admin(request, db)
    users = db.query(User).order_by(User.created_at.desc()).all()
    return templates.TemplateResponse("users.html", {"request": request, "user": user, "users": users})


@app.post("/users")
def create_user(request: Request, full_name: str = Form(...), username: str = Form(...), password: str = Form(...), role: str = Form(...), db: Session = Depends(get_db)):
    require_admin(request, db)
    exists = db.query(User).filter(User.username == username).first()
    if exists:
        return RedirectResponse("/users?error=1", status_code=302)
    db.add(User(full_name=full_name, username=username, password=password, role=role))
    db.commit()
    return RedirectResponse("/users", status_code=302)


@app.get("/api/stores/{store_code}")
def get_store_data(store_code: str, request: Request, db: Session = Depends(get_db)):
    require_login(request, db)
    store = db.query(Store).filter(Store.store_code == store_code).first()
    if not store:
        return JSONResponse({"error": "not_found"}, status_code=404)
    central_name = central_name_for(db, store.central_code)
    return {
        "store_code": store.store_code,
        "central_code": store.central_code,
        "central_name": central_name,
        "format": store.format,
        "store_name": store.store_name,
        "region": store.region,
        "district": store.district,
        "zone": store.zone,
        "lat": store.lat,
        "lng": store.lng,
        "province": store.province,
        "canton": store.canton,
        "parish": store.parish,
        "subzone": store.subzone,
        "police_district": store.police_district,
        "circuit": store.circuit,
        "subcircuit": store.subcircuit,
        "subcircuit_code": store.subcircuit_code,
    }
