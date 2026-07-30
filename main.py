from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import uuid
import os
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_URI = os.getenv("DATABASE_URL")

class ScheduleSchema(BaseModel):
    supplier_document: str
    cargo_weight_kg: float
    scheduled_start: datetime
    scheduled_end: datetime
    license_plate: str
    driver_name: str
    invoice_number: str

@app.get("/")
def home():
    return {"status": "API YMS Operacional", "banco": "PostgreSQL Aiven"}

@app.post("/api/agendar")
def create_appointment(data: ScheduleSchema):
    if not DB_URI:
        raise HTTPException(status_code=500, detail="URL do banco de dados não configurada.")
        
    conn = psycopg2.connect(DB_URI)
    cursor = conn.cursor()

    # 1. Valida Limite de Peso (Máximo 12.000 kg por slot)
    cursor.execute("""
        SELECT COALESCE(SUM(cargo_weight_kg), 0) 
        FROM delivery_appointments 
        WHERE scheduled_start = %s AND status != 'CANCELADO'
    """, (data.scheduled_start,))
    
    current_weight = cursor.fetchone()[0]
    if float(current_weight) + data.cargo_weight_kg > 12000:
        conn.close()
        raise HTTPException(status_code=400, detail="Capacidade de peso excedida para este horário (Máx: 12 t).")

    # 2. Valida Limite de Docas (Máximo 5 veículos por slot)
    cursor.execute("""
        SELECT COUNT(id) 
        FROM delivery_appointments 
        WHERE scheduled_start = %s AND status != 'CANCELADO'
    """, (data.scheduled_start,))
    
    current_docks = cursor.fetchone()[0]
    if current_docks >= 5:
        conn.close()
        raise HTTPException(status_code=400, detail="Todas as docas estão ocupadas para este horário.")

    # 3. Grava no banco Aiven
    code = f"YMS-{uuid.uuid4().hex[:6].upper()}"
    cursor.execute("""
        INSERT INTO delivery_appointments 
        (appointment_code, supplier_document, cargo_weight_kg, driver_name, license_plate, invoice_number, scheduled_start, scheduled_end)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (code, data.supplier_document, data.cargo_weight_kg, data.driver_name, data.license_plate, data.invoice_number, data.scheduled_start, data.scheduled_end))
    
    conn.commit()
    cursor.close()
    conn.close()

    return {"status": "SUCESSO", "codigo_agendamento": code}
