from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(150), nullable=False)
    role = Column(String(50), nullable=False, default="usuario")
    created_at = Column(DateTime, default=datetime.utcnow)


class Store(Base):
    __tablename__ = "stores"
    id = Column(Integer, primary_key=True)
    store_code = Column(String(20), unique=True, index=True, nullable=False)
    central_code = Column(String(20), nullable=True)
    format = Column(String(50), nullable=True)
    store_name = Column(String(150), nullable=False)
    region = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    zone = Column(String(100), nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    province = Column(String(100), nullable=True)
    canton = Column(String(100), nullable=True)
    parish = Column(String(100), nullable=True)
    subzone = Column(String(100), nullable=True)
    police_district = Column(String(100), nullable=True)
    circuit = Column(String(100), nullable=True)
    subcircuit = Column(String(100), nullable=True)
    subcircuit_code = Column(String(50), nullable=True)


class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True)
    case_number = Column(String(50), unique=True, index=True, nullable=False)

    # Encabezado / Pantalla evento
    police_unit = Column(String(200), nullable=True)
    requested_by = Column(String(150), nullable=True)

    # Pantalla 01
    process = Column(String(50), nullable=False, default="")
    sub_process = Column(String(100), nullable=True)
    alarm_activated = Column(String(10), nullable=True)
    chief_name = Column(String(150), nullable=True)
    alert_time = Column(String(20), nullable=True)
    security_company = Column(String(100), nullable=True)
    security_operator = Column(String(150), nullable=True)
    center_operator_time = Column(String(20), nullable=True)
    center_operator_name = Column(String(150), nullable=True)

    # Pantalla 02
    central_code = Column(String(20), nullable=True)
    central_name = Column(String(150), nullable=True)
    store_code = Column(String(20), nullable=True)
    store_name = Column(String(150), nullable=True)
    format = Column(String(50), nullable=True)
    region = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    zone = Column(String(100), nullable=True)
    province = Column(String(100), nullable=True)
    canton = Column(String(100), nullable=True)
    parish = Column(String(100), nullable=True)
    subzone = Column(String(100), nullable=True)
    police_district = Column(String(100), nullable=True)
    circuit = Column(String(100), nullable=True)
    subcircuit = Column(String(100), nullable=True)
    subcircuit_code = Column(String(50), nullable=True)
    lat = Column(String(50), nullable=True)
    lng = Column(String(50), nullable=True)
    affectation = Column(String(50), nullable=True)
    novelty_location = Column(String(50), nullable=True)
    place_company = Column(String(100), nullable=True)
    place_subtype = Column(String(100), nullable=True)
    event_date = Column(String(20), nullable=True)
    event_time = Column(String(20), nullable=True)
    alert_state = Column(String(50), nullable=True)
    discarded_reason = Column(String(250), nullable=True)

    # Pantalla 03
    novelty_type = Column(String(100), nullable=True)
    novelty_subtype = Column(String(100), nullable=True)
    modality = Column(String(100), nullable=True)
    number_of_members = Column(Integer, nullable=True)
    detail = Column(Text, nullable=True)

    # Pantallas 04-09
    victims_json = Column(Text, nullable=True)
    suspects_json = Column(Text, nullable=True)
    merchandise_json = Column(Text, nullable=True)
    photo_notes_json = Column(Text, nullable=True)
    vehicles_json = Column(Text, nullable=True)
    processed_json = Column(Text, nullable=True)
    delegation = Column(String(150), nullable=True)
    prosecutor_office = Column(String(150), nullable=True)
    prosecutor_name = Column(String(150), nullable=True)
    complaint_number = Column(String(100), nullable=True)
    complaint_date = Column(String(20), nullable=True)
    judicial_unit = Column(String(200), nullable=True)
    cause_number = Column(String(120), nullable=True)
    proceedings = Column(Text, nullable=True)
    legal_status = Column(String(120), nullable=True)
    hearing_date = Column(String(20), nullable=True)
    precautionary_measure = Column(String(150), nullable=True)
    legal_summary = Column(Text, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    creator = relationship("User")
    files = relationship("CaseFile", back_populates="case", cascade="all, delete-orphan")


class CaseFile(Base):
    __tablename__ = "case_files"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    file_type = Column(String(50), nullable=False)
    original_name = Column(String(255), nullable=False)
    stored_name = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    case = relationship("Case", back_populates="files")
