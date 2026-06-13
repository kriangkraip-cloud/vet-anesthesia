from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    full_name = Column(String(100))
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="staff")  # admin, anesthesiologist, surgeon, staff
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    hn = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    species = Column(String(50))
    breed = Column(String(100))
    sex = Column(String(10))
    neuter_status = Column(String(20))
    age = Column(String(30))
    weight = Column(Float)
    owner_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    updated_by_id = Column(Integer, ForeignKey("users.id"))

    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])
    records = relationship("AnestheticRecord", back_populates="patient", cascade="all, delete-orphan")


class AnestheticRecord(Base):
    __tablename__ = "anesthetic_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    record_date = Column(Date)
    status = Column(String(20), default="draft")  # draft, ongoing, completed, exported

    # Pre-anesthetic evaluation
    asa_status = Column(String(10))
    weight_at_record = Column(Float)
    pcv = Column(Float)
    bun = Column(Float)
    creatinine = Column(Float)
    ast = Column(Float)
    alt = Column(Float)
    crt = Column(String(20))
    hr_pre = Column(Float)
    rr_pre = Column(Float)
    pulse_quality = Column(String(50))
    temp_pre = Column(Float)
    current_medications = Column(Text)
    clinical_notes = Column(Text)
    anesthetic_concerns = Column(Text)
    risk_assessment = Column(Text)

    # Case info (can differ from patient registration)
    diagnosis = Column(String(500))
    surgical_procedure = Column(String(500))
    surgeon = Column(String(100))
    anesthesiologist = Column(String(100))
    assistant = Column(String(100))

    # Equipment and quality
    o2_flow_rate = Column(Float)
    anesthetic_machine = Column(String(100))
    breathing_system = Column(String(100))
    vaporizer_gas = Column(String(50))
    airway_device = Column(String(100))
    ett_size = Column(Float)
    intubation_note = Column(Text)
    induction_complication = Column(Text)
    premed_quality = Column(String(50))
    induction_quality = Column(String(50))

    # Timing
    anesthesia_start = Column(DateTime)
    anesthesia_end = Column(DateTime)
    surgery_start = Column(DateTime)
    surgery_end = Column(DateTime)

    # Recovery
    extubation_time = Column(DateTime)
    sternal_time = Column(DateTime)
    standing_time = Column(DateTime)
    recovery_quality = Column(String(50))
    recovery_complications = Column(Text)
    postop_pain_management = Column(Text)
    sample_collection = Column(Text)
    postop_medications = Column(Text)
    postop_monitoring = Column(Text)
    final_note = Column(Text)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    updated_by_id = Column(Integer, ForeignKey("users.id"))

    patient = relationship("Patient", back_populates="records")
    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])
    drug_entries = relationship("DrugEntry", back_populates="record", cascade="all, delete-orphan", order_by="DrugEntry.sort_order")
    monitoring_entries = relationship("MonitoringEntry", back_populates="record", cascade="all, delete-orphan", order_by="MonitoringEntry.time")
    fluid_entries = relationship("FluidEntry", back_populates="record", cascade="all, delete-orphan", order_by="FluidEntry.sort_order")
    emergency_events = relationship("EmergencyEvent", back_populates="record", cascade="all, delete-orphan", order_by="EmergencyEvent.time")
    surgical_procedures = relationship("SurgicalProcedure", back_populates="record", cascade="all, delete-orphan", order_by="SurgicalProcedure.sort_order")
    export_history = relationship("ExportHistory", back_populates="record", cascade="all, delete-orphan")


class DrugEntry(Base):
    __tablename__ = "drug_entries"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("anesthetic_records.id"), nullable=False)
    entry_type = Column(String(30))  # premedication, induction, antibiotic, local_anesthesia, cri
    drug_name = Column(String(100))
    dose = Column(Float)
    dose_unit = Column(String(20))  # mg/kg, mcg/kg, mL, total
    concentration = Column(Float)
    concentration_unit = Column(String(20))
    calculated_total_dose = Column(Float)
    calculated_volume = Column(Float)
    is_manual_override = Column(Boolean, default=False)
    route = Column(String(50))
    time = Column(DateTime)
    note = Column(Text)
    # CRI fields
    rate = Column(Float)
    rate_unit = Column(String(20))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    total_volume_delivered = Column(Float)
    # Gas induction
    gas_type = Column(String(50))
    induction_method = Column(String(50))
    # Antibiotic
    repeat_dose_interval = Column(Float)  # hours
    # Local anesthesia
    technique = Column(String(100))
    site = Column(String(100))
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"))

    record = relationship("AnestheticRecord", back_populates="drug_entries")
    created_by = relationship("User", foreign_keys=[created_by_id])


class MonitoringEntry(Base):
    __tablename__ = "monitoring_entries"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("anesthetic_records.id"), nullable=False)
    time = Column(DateTime, nullable=False)
    gas_percent = Column(Float)
    hr = Column(Float)
    rr = Column(Float)
    spo2 = Column(Float)
    systolic_bp = Column(Float)
    diastolic_bp = Column(Float)
    map_bp = Column(Float)
    etco2 = Column(Float)
    body_temp = Column(Float)
    o2_flow = Column(Float)
    fluid_rate = Column(Float)
    pulse = Column(String(50))
    ventilation_mode = Column(String(30))  # spontaneous, assisted, mechanical
    breathing_pattern = Column(String(100))
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"))

    record = relationship("AnestheticRecord", back_populates="monitoring_entries")


class FluidEntry(Base):
    __tablename__ = "fluid_entries"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("anesthetic_records.id"), nullable=False)
    fluid_type = Column(String(100))
    rate = Column(Float)
    rate_unit = Column(String(20))  # mL/kg/hr, mL/hr
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    total_volume = Column(Float)
    is_manual_volume = Column(Boolean, default=False)
    note = Column(Text)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"))

    record = relationship("AnestheticRecord", back_populates="fluid_entries")


class EmergencyEvent(Base):
    __tablename__ = "emergency_events"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("anesthetic_records.id"), nullable=False)
    time = Column(DateTime, nullable=False)
    event_type = Column(String(100))
    drug_name = Column(String(100))
    dose = Column(Float)
    dose_unit = Column(String(20))
    volume = Column(Float)
    route = Column(String(50))
    response = Column(Text)
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"))

    record = relationship("AnestheticRecord", back_populates="emergency_events")


class SurgicalProcedure(Base):
    __tablename__ = "surgical_procedures"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("anesthetic_records.id"), nullable=False)
    procedure_name = Column(String(200))
    surgeon = Column(String(100))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    note = Column(Text)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    record = relationship("AnestheticRecord", back_populates="surgical_procedures")


class ExportHistory(Base):
    __tablename__ = "export_history"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("anesthetic_records.id"), nullable=False)
    export_type = Column(String(10))  # pdf, docx
    exported_at = Column(DateTime, default=datetime.utcnow)
    exported_by_id = Column(Integer, ForeignKey("users.id"))

    record = relationship("AnestheticRecord", back_populates="export_history")
    exported_by = relationship("User", foreign_keys=[exported_by_id])
