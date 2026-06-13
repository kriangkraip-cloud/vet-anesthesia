from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    full_name: Optional[str]
    role: str


class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: str
    role: str = "staff"


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: Optional[str]
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime


class PatientCreate(BaseModel):
    hn: str
    name: str
    species: Optional[str] = None
    breed: Optional[str] = None
    sex: Optional[str] = None
    neuter_status: Optional[str] = None
    age: Optional[str] = None
    weight: Optional[float] = None
    owner_name: Optional[str] = None


class PatientUpdate(PatientCreate):
    hn: Optional[str] = None
    name: Optional[str] = None


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    hn: str
    name: str
    species: Optional[str]
    breed: Optional[str]
    sex: Optional[str]
    neuter_status: Optional[str]
    age: Optional[str]
    weight: Optional[float]
    owner_name: Optional[str]
    created_at: datetime
    updated_at: datetime


class DrugEntryCreate(BaseModel):
    entry_type: str
    drug_name: Optional[str] = None
    dose: Optional[float] = None
    dose_unit: Optional[str] = None
    concentration: Optional[float] = None
    concentration_unit: Optional[str] = None
    calculated_total_dose: Optional[float] = None
    calculated_volume: Optional[float] = None
    is_manual_override: bool = False
    route: Optional[str] = None
    time: Optional[datetime] = None
    note: Optional[str] = None
    rate: Optional[float] = None
    rate_unit: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_volume_delivered: Optional[float] = None
    gas_type: Optional[str] = None
    induction_method: Optional[str] = None
    repeat_dose_interval: Optional[float] = None
    technique: Optional[str] = None
    site: Optional[str] = None
    sort_order: int = 0


class DrugEntryOut(DrugEntryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    record_id: int
    created_at: datetime


class MonitoringEntryCreate(BaseModel):
    time: datetime
    gas_percent: Optional[float] = None
    hr: Optional[float] = None
    rr: Optional[float] = None
    spo2: Optional[float] = None
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None
    map_bp: Optional[float] = None
    etco2: Optional[float] = None
    body_temp: Optional[float] = None
    o2_flow: Optional[float] = None
    fluid_rate: Optional[float] = None
    pulse: Optional[str] = None
    ventilation_mode: Optional[str] = None
    breathing_pattern: Optional[str] = None
    note: Optional[str] = None


class MonitoringEntryOut(MonitoringEntryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    record_id: int
    created_at: datetime


class FluidEntryCreate(BaseModel):
    fluid_type: Optional[str] = None
    rate: Optional[float] = None
    rate_unit: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_volume: Optional[float] = None
    is_manual_volume: bool = False
    note: Optional[str] = None
    sort_order: int = 0


class FluidEntryOut(FluidEntryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    record_id: int
    created_at: datetime


class EmergencyEventCreate(BaseModel):
    time: datetime
    event_type: Optional[str] = None
    drug_name: Optional[str] = None
    dose: Optional[float] = None
    dose_unit: Optional[str] = None
    volume: Optional[float] = None
    route: Optional[str] = None
    response: Optional[str] = None
    note: Optional[str] = None


class EmergencyEventOut(EmergencyEventCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    record_id: int
    created_at: datetime


class SurgicalProcedureCreate(BaseModel):
    procedure_name: Optional[str] = None
    surgeon: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    note: Optional[str] = None
    sort_order: int = 0


class SurgicalProcedureOut(SurgicalProcedureCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    record_id: int
    created_at: datetime


class RecordCreate(BaseModel):
    patient_id: int
    record_date: Optional[date] = None
    status: str = "draft"
    asa_status: Optional[str] = None
    weight_at_record: Optional[float] = None
    pcv: Optional[float] = None
    bun: Optional[float] = None
    creatinine: Optional[float] = None
    ast: Optional[float] = None
    alt: Optional[float] = None
    crt: Optional[str] = None
    hr_pre: Optional[float] = None
    rr_pre: Optional[float] = None
    pulse_quality: Optional[str] = None
    temp_pre: Optional[float] = None
    current_medications: Optional[str] = None
    clinical_notes: Optional[str] = None
    anesthetic_concerns: Optional[str] = None
    risk_assessment: Optional[str] = None
    diagnosis: Optional[str] = None
    surgical_procedure: Optional[str] = None
    surgeon: Optional[str] = None
    anesthesiologist: Optional[str] = None
    assistant: Optional[str] = None
    o2_flow_rate: Optional[float] = None
    anesthetic_machine: Optional[str] = None
    breathing_system: Optional[str] = None
    vaporizer_gas: Optional[str] = None
    airway_device: Optional[str] = None
    ett_size: Optional[float] = None
    intubation_note: Optional[str] = None
    induction_complication: Optional[str] = None
    premed_quality: Optional[str] = None
    induction_quality: Optional[str] = None
    anesthesia_start: Optional[datetime] = None
    anesthesia_end: Optional[datetime] = None
    surgery_start: Optional[datetime] = None
    surgery_end: Optional[datetime] = None
    extubation_time: Optional[datetime] = None
    sternal_time: Optional[datetime] = None
    standing_time: Optional[datetime] = None
    recovery_quality: Optional[str] = None
    recovery_complications: Optional[str] = None
    postop_pain_management: Optional[str] = None
    sample_collection: Optional[str] = None
    postop_medications: Optional[str] = None
    postop_monitoring: Optional[str] = None
    final_note: Optional[str] = None


class RecordUpdate(RecordCreate):
    patient_id: Optional[int] = None


class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    patient_id: int
    record_date: Optional[date]
    status: str
    asa_status: Optional[str]
    weight_at_record: Optional[float]
    pcv: Optional[float]
    bun: Optional[float]
    creatinine: Optional[float]
    ast: Optional[float]
    alt: Optional[float]
    crt: Optional[str]
    hr_pre: Optional[float]
    rr_pre: Optional[float]
    pulse_quality: Optional[str]
    temp_pre: Optional[float]
    current_medications: Optional[str]
    clinical_notes: Optional[str]
    anesthetic_concerns: Optional[str]
    risk_assessment: Optional[str]
    diagnosis: Optional[str]
    surgical_procedure: Optional[str]
    surgeon: Optional[str]
    anesthesiologist: Optional[str]
    assistant: Optional[str]
    o2_flow_rate: Optional[float]
    anesthetic_machine: Optional[str]
    breathing_system: Optional[str]
    vaporizer_gas: Optional[str]
    airway_device: Optional[str]
    ett_size: Optional[float]
    intubation_note: Optional[str]
    induction_complication: Optional[str]
    premed_quality: Optional[str]
    induction_quality: Optional[str]
    anesthesia_start: Optional[datetime]
    anesthesia_end: Optional[datetime]
    surgery_start: Optional[datetime]
    surgery_end: Optional[datetime]
    extubation_time: Optional[datetime]
    sternal_time: Optional[datetime]
    standing_time: Optional[datetime]
    recovery_quality: Optional[str]
    recovery_complications: Optional[str]
    postop_pain_management: Optional[str]
    sample_collection: Optional[str]
    postop_medications: Optional[str]
    postop_monitoring: Optional[str]
    final_note: Optional[str]
    created_at: datetime
    updated_at: datetime
    drug_entries: List[DrugEntryOut] = []
    monitoring_entries: List[MonitoringEntryOut] = []
    fluid_entries: List[FluidEntryOut] = []
    emergency_events: List[EmergencyEventOut] = []
    surgical_procedures: List[SurgicalProcedureOut] = []
