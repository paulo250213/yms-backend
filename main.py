import base64
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import psycopg2
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="DINIZ - YMS Agendamento de Entregas")

DATABASE_URL = os.getenv("DATABASE_URL")

# Configurações de E-mail
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL")
APP_URL = os.getenv("APP_URL", "https://seu-app.onrender.com")


def get_db_connection():
    if not DATABASE_URL:
        raise HTTPException(
            status_code=500, detail="DATABASE_URL não configurada."
        )
    return psycopg2.connect(DATABASE_URL)


def send_email_notification(schedule_data: dict):
    if not SMTP_EMAIL or not SMTP_PASSWORD or not NOTIFY_EMAIL:
        print("AVISO: Configurações de e-mail ausentes.")
        return

    try:
        subject = (
            "📬 Novo Agendamento Pendente -"
            f" {schedule_data.get('supplier_name')}"
        )
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px;">
                <h2 style="color: #0b192c; border-bottom: 3px solid #ffc107; padding-bottom: 10px; margin-top: 0;">
                    👨‍🍳 DINIZ ALIMENTOS - Novo Agendamento
                </h2>
                <p>Uma nova solicitação de agendamento foi registrada e está <strong>aguardando sua aprovação</strong>.</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0; background: #f9f9f9;">
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Fornecedor:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{schedule_data.get('supplier_name')}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Contato Preferencial:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{str(schedule_data.get('preferred_contact', 'whatsapp')).upper()}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Dado de Contato:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{schedule_data.get('phone') if schedule_data.get('preferred_contact') == 'whatsapp' else schedule_data.get('email')}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Placa do Veículo:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{schedule_data.get('truck_plate')}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Peso da Carga:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{schedule_data.get('cargo_weight')} kg</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Tipo de Armazenamento:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{schedule_data.get('storage_type')}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Tipo da Carga:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{schedule_data.get('cargo_type')} ({schedule_data.get('pallet_quantity')} Qtd.)</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Data Prevista:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{schedule_data.get('schedule_date')}</td></tr>
                    <tr><td style="padding: 8px;"><strong>Pré-Senha:</strong></td><td style="padding: 8px;"><strong style="color: #137333;">{schedule_data.get('access_code')}</strong></td></tr>
                </table>
                <div style="text-align: center; margin-top: 25px;">
                    <a href="{APP_URL}/agendamentos" style="background-color: #0b192c; color: #ffc107; padding: 12px 24px; text-decoration: none; font-weight: bold; border-radius: 6px; display: inline-block;">
                        👉 Acessar Painel para Aprovar ou Recusar
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_EMAIL
        msg["To"] = NOTIFY_EMAIL
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, NOTIFY_EMAIL, msg.as_string())
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")


def init_db():
    if not DATABASE_URL:
        return
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS schedules (
                        id SERIAL PRIMARY KEY,
                        supplier_name VARCHAR(100) NOT NULL,
                        truck_plate VARCHAR(20) NOT NULL,
                        cargo_weight NUMERIC(10, 2) NOT NULL,
                        storage_type VARCHAR(20) NOT NULL,
                        dock_id INT NOT NULL DEFAULT 10,
                        schedule_time DATE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        cargo_type VARCHAR(20),
                        pallet_quantity INT DEFAULT 0,
                        access_code VARCHAR(20),
                        status VARCHAR(20) DEFAULT 'Pendente',
                        phone VARCHAR(30),
                        email VARCHAR(100),
                        preferred_contact VARCHAR(20) DEFAULT 'whatsapp'
                    );
                """)
                conn.commit()
    except Exception as e:
        print("Erro ao inicializar banco:", e)


init_db()


class ScheduleRequest(BaseModel):
    supplier_name: str
    preferred_contact: str = "whatsapp"
    phone: str = ""
    email: str = ""
    truck_plate: str
    cargo_weight: float
    storage_type: str
    cargo_type: str
    pallet_quantity: int
    dock_id: int = 10
    schedule_date: str
    access_code: str


class StatusUpdateRequest(BaseModel):
    status: str


# --- ROTA DA IMAGEM COM FALLBACK AUTOMÁTICO ---
@app.get("/logo_banner.png")
def get_banner():
    banner_path = "logo_banner.png"
    alt_path = "Design sem nome_3.png"

    if os.path.exists(banner_path):
        return FileResponse(banner_path, media_type="image/png")
    elif os.path.exists(alt_path):
        return FileResponse(alt_path, media_type="image/png")
    else:
        raise HTTPException(
            status_code=404,
            detail=(
                "Imagem não encontrada. Certifique-se de que o arquivo"
                " 'logo_banner.png' está enviado no repositório."
            ),
        )


@app.get("/manual.pdf")
def get_manual():
    pdf_path = "manual.pdf"
    alt_pdf_path = "Manual do Fornecedor Diniz Foods - Versão Corrigida.pdf"
    if os.path.exists(pdf_path):
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="Manual_do_Fornecedor_Diniz.pdf",
        )
    elif os.path.exists(alt_pdf_path):
        return FileResponse(
            alt_pdf_path,
            media_type="application/pdf",
            filename="Manual_do_Fornecedor_Diniz.pdf",
        )
    else:
        raise HTTPException(
            status_code=404, detail="Manual PDF não encontrado."
        )


@app.get("/", response_class=HTMLResponse)
def get_form():
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Diniz Alimentos - Agendamento de Carga</title>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            * { box-sizing: border-box; }
            body { 
                font-family: 'Poppins', sans-serif; 
                background: linear-gradient(135deg, #0b192c 0%, #1e3e62 100%); 
                min-height: 100vh;
                margin: 0; 
                padding: 20px 10px; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
            }
            .card { 
                background: #ffffff; 
                border-radius: 12px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.3); 
                width: 100%; 
                max-width: 520px; 
                overflow: hidden;
            }
            .header-banner {
                width: 100%;
                background-color: #031027;
                border-bottom: 4px solid #ffc107;
                padding: 10px 0;
            }
            .header-banner img {
                width: 100%;
                max-height: 140px;
                display: block;
                object-fit: contain;
            }
            
            .info-box {
                background-color: #fff9e6;
                border-left: 5px solid #ffc107;
                padding: 15px 20px;
                margin: 20px 30px 0 30px;
                border-radius: 6px;
            }
            .info-box-title { font-weight: 700; color: #0b192c; font-size: 14px; margin-bottom: 6px; }
            .info-box-text { font-size: 12px; color: #444; line-height: 1.5; margin-bottom: 8px; }
            .info-box-time { font-weight: 700; color: #b78103; background: #fff0c2; padding: 4px 8px; border-radius: 4px; display: inline-block; margin-bottom: 8px; font-size: 12px; }
            .info-box-alert { font-weight: 700; color: #0b192c; background: #ffe89c; padding: 6px 10px; border-radius: 4px; display: block; margin-bottom: 12px; font-size: 12px; }
            .btn-manual { display: inline-block; width: 100%; text-align: center; background-color: #0b192c; color: #ffc107; padding: 10px; border-radius: 6px; font-size: 13px; font-weight: 700; text-decoration: none; }

            .form-body { padding: 20px 30px 25px 30px; }
            .form-group { margin-bottom: 18px; }
            label { display: block; margin-bottom: 6px; font-weight: 600; color: #2b2b2b; font-size: 13px; }
            input, select { width: 100%; padding: 12px 14px; border: 1.5px solid #dcdfe6; border-radius: 6px; font-size: 14px; font-family: inherit; }
            input:focus, select:focus { outline: none; border-color: #0b192c; }
            .uppercase-input { text-transform: uppercase; }
            button.btn-submit { 
                width: 100%; padding: 14px; background: linear-gradient(90deg, #ffc107 0%, #e0a800 100%); 
                color: #0b192c; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; 
                font-weight: 700; text-transform: uppercase; margin-top: 10px; box-shadow: 0 4px 12px rgba(255, 193, 7, 0.3);
            }
            .message { margin-top: 20px; padding: 15px; border-radius: 6px; display: none; text-align: center; font-size: 14px; line-height: 1.5; }
            .success { background-color: #e6f4ea; color: #137333; border: 1px solid #ceead6; }
            .error { background-color: #fce8e6; color: #c5221f; border: 1px solid #fad2cf; }
            .code-highlight { font-size: 22px; font-weight: 700; background: #ffffff; padding: 6px 14px; border-radius: 6px; display: inline-block; margin-top: 8px; border: 2px dashed #137333; color: #137333; }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header-banner">
                <img src="/logo_banner.png" alt="Diniz Alimentos" onerror="this.onerror=null; this.src='/logo_banner.png';">
            </div>

            <div class="info-box">
                <div class="info-box-title">📌 Informações Importantes</div>
                <div class="info-box-time">⏰ Recebimento: Das 07:30 às 12:00</div>
                <div class="info-box-alert">📄 Entregar nota fiscal ao lado da doca 10</div>
                <div class="info-box-text">Todas as normas operacionais e regras de conduta estão no manual.</div>
                <a href="/manual.pdf" target="_blank" class="btn-manual">📖 Visualizar Manual do Fornecedor (PDF)</a>
            </div>
            
            <div class="form-body">
                <form id="scheduleForm">
                    <div class="form-group">
                        <label for="supplier">NOME DO FORNECEDOR:</label>
                        <input type="text" id="supplier" class="uppercase-input" required placeholder="Ex: SILVA ALIMENTOS LTDA">
                    </div>

                    <div class="form-group">
                        <label for="preferredContact">RECEBER CONFIRMAÇÃO POR:</label>
                        <select id="preferredContact" onchange="toggleContactInput()" required>
                            <option value="whatsapp" selected>📱 WhatsApp</option>
                            <option value="email">✉️ E-mail</option>
                        </select>
                    </div>

                    <div class="form-group" id="phoneGroup">
                        <label for="phone">CELULAR / WHATSAPP:</label>
                        <input type="text" id="phone" required placeholder="Ex: 11999998888 (com DDD)">
                    </div>

                    <div class="form-group" id="emailGroup" style="display: none;">
                        <label for="email">E-MAIL DE CONTATO:</label>
                        <input type="email" id="email" placeholder="Ex: contato@fornecedor.com">
                    </div>

                    <div class="form-group">
                        <label for="plate">PLACA DO VEÍCULO:</label>
                        <input type="text" id="plate" class="uppercase-input" required placeholder="Ex: ABC1D23">
                    </div>
                    <div class="form-group">
                        <label for="weight">PESO DA CARGA (KG):</label>
                        <input type="number" step="0.1" id="weight" required placeholder="Ex: 1500.50">
                    </div>
                    <div class="form-group">
                        <label for="storage">TIPO DE ARMAZENAMENTO:</label>
                        <select id="storage" required>
                            <option value="Seco">Seco</option>
                            <option value="Resfriado">Resfriado</option>
                            <option value="Congelado">Congelado</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="cargoType">TIPO DA CARGA:</label>
                        <select id="cargoType" required onchange="toggleQuantityInput()">
                            <option value="Paletizada">Paletizada</option>
                            <option value="Batida">Batida (Carga Solta)</option>
                        </select>
                    </div>
                    <div class="form-group" id="qtyGroup">
                        <label for="qtyInput" id="qtyLabel">QUANTIDADE DE PALETES:</label>
                        <input type="number" id="qtyInput" value="0" min="0" placeholder="Ex: 26" required>
                    </div>
                    <div class="form-group">
                        <label for="scheduleDate">DATA DA CHEGADA:</label>
                        <input type="date" id="scheduleDate" required>
                    </div>
                    <button type="submit" class="btn-submit">Solicitar Agendamento</button>
                </form>
                <div id="responseMsg" class="message"></div>
            </div>
        </div>

        <script>
            function generateRandomCode() {
                const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
                let code = '';
                for (let i = 0; i < 6; i++) {
                    code += chars.charAt(Math.floor(Math.random() * chars.length));
                }
                return code;
            }

            function toggleContactInput() {
                const contactType = document.getElementById('preferredContact').value;
                document.getElementById('phoneGroup').style.display = contactType === 'whatsapp' ? 'block' : 'none';
                document.getElementById('emailGroup').style.display = contactType === 'email' ? 'block' : 'none';
                document.getElementById('phone').required = contactType === 'whatsapp';
                document.getElementById('email').required = contactType === 'email';
            }

            function toggleQuantityInput() {
                const cargoType = document.getElementById('cargoType').value;
                document.getElementById('qtyLabel').innerText = cargoType === 'Batida' ? 'QUANTIDADE DE VOLUMES:' : 'QUANTIDADE DE PALETES:';
            }

            document.getElementById('scheduleForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const msgDiv = document.getElementById('responseMsg');
                msgDiv.style.display = 'none';

                const randomCode = generateRandomCode();
                const preferred = document.getElementById('preferredContact').value;
                let cleanPhone = document.getElementById('phone').value.replace(/\D/g, '');
                if (cleanPhone.length >= 10 && !cleanPhone.startsWith('55')) {
                    cleanPhone = '55' + cleanPhone;
                }

                const payload = {
                    supplier_name: document.getElementById('supplier').value.toUpperCase(),
                    preferred_contact: preferred,
                    phone: preferred === 'whatsapp' ? cleanPhone : '',
                    email: preferred === 'email' ? document.getElementById('email').value.trim() : '',
                    truck_plate: document.getElementById('plate').value.toUpperCase(),
                    cargo_weight: parseFloat(document.getElementById('weight').value),
                    storage_type: document.getElementById('storage').value,
                    cargo_type: document.getElementById('cargoType').value,
                    pallet_quantity: parseInt(document.getElementById('qtyInput').value || 0),
                    dock_id: 10,
                    schedule_date: document.getElementById('scheduleDate').value,
                    access_code: randomCode
                };

                try {
                    const res = await fetch('/api/schedule', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    const data = await res.json();
                    
                    if (res.ok) {
                        msgDiv.className = 'message success';
                        msgDiv.innerHTML = `Solicitação enviada!<br><strong>Status: Pendente</strong><br>Sua pré-senha:<br><span class="code-highlight">${randomCode}</span>`;
                        document.getElementById('scheduleForm').reset();
                    } else {
                        msgDiv.className = 'message error';
                        msgDiv.innerText = data.detail || 'Erro ao agendar.';
                    }
                } catch (err) {
                    msgDiv.className = 'message error';
                    msgDiv.innerText = 'Erro na conexão.';
                }
                msgDiv.style.display = 'block';
            });
        </script>
    </body>
    </html>
    """


@app.get("/agendamentos", response_class=HTMLResponse)
def list_schedules_page():
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Diniz Alimentos - Gestão de Agendamentos</title>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Poppins', sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; }
            .container { background: white; padding: 30px; border-radius: 12px; max-width: 1400px; margin: 0 auto; }
            .header-bar { display: flex; align-items: center; justify-content: space-between; border-bottom: 3px solid #ffc107; padding-bottom: 15px; margin-bottom: 20px; }
            .brand-banner-img { max-height: 75px; object-fit: contain; }
            .btn { padding: 10px 18px; border-radius: 6px; font-weight: 600; cursor: pointer; text-decoration: none; border: none; }
            .btn-pdf { background-color: #0b192c; color: #ffc107; }
            .btn-new { background-color: #ffc107; color: #0b192c; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th, td { padding: 10px 8px; border: 1px solid #e9ecef; text-align: center; font-size: 12px; }
            th { background-color: #0b192c; color: #ffffff; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header-bar">
                <img src="/logo_banner.png" alt="Diniz Alimentos" class="brand-banner-img">
                <div>
                    <button class="btn btn-pdf" onclick="window.print()">📄 Imprimir</button>
                    <a href="/" class="btn btn-new">➕ Novo Agendamento</a>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th><th>Senha</th><th>Status</th><th>Fornecedor</th><th>Contato</th><th>Placa</th><th>Data</th>
                    </tr>
                </thead>
                <tbody id="tableBody"></tbody>
            </table>
        </div>
        <script>
            async function loadSchedules() {
                const res = await fetch('/api/schedules');
                const data = await res.json();
                const tbody = document.getElementById('tableBody');
                tbody.innerHTML = data.map(row => `
                    <tr>
                        <td>${row.id}</td><td>${row.access_code}</td><td>${row.status}</td>
                        <td>${row.supplier_name}</td><td>${row.phone || row.email}</td>
                        <td>${row.truck_plate}</td><td>${row.schedule_time}</td>
                    </tr>
                `).join('');
            }
            window.onload = loadSchedules;
        </script>
    </body>
    </html>
    """


@app.post("/api/schedule")
def create_schedule(req: ScheduleRequest, background_tasks: BackgroundTasks):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO schedules (
                        supplier_name, preferred_contact, phone, email, truck_plate, cargo_weight, storage_type, 
                        cargo_type, pallet_quantity, dock_id, schedule_time, access_code, status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pendente');
                    """,
                    (
                        req.supplier_name.upper(),
                        req.preferred_contact,
                        req.phone,
                        req.email,
                        req.truck_plate.upper(),
                        req.cargo_weight,
                        req.storage_type,
                        req.cargo_type,
                        req.pallet_quantity,
                        req.dock_id,
                        req.schedule_date,
                        req.access_code,
                    ),
                )
                conn.commit()

        background_tasks.add_task(send_email_notification, req.dict())
        return {"status": "sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/schedules")
def list_schedules():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, supplier_name, truck_plate, cargo_weight, storage_type, 
                           cargo_type, pallet_quantity, dock_id, TO_CHAR(schedule_time, 'YYYY-MM-DD'), 
                           access_code, status, phone, email, preferred_contact
                    FROM schedules ORDER BY id DESC;
                """)
                rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "supplier_name": r[1],
                "truck_plate": r[2],
                "cargo_weight": r[3],
                "storage_type": r[4],
                "cargo_type": r[5],
                "pallet_quantity": r[6],
                "dock_id": r[7],
                "schedule_time": r[8],
                "access_code": r[9],
                "status": r[10] or "Pendente",
                "phone": r[11] or "",
                "email": r[12] or "",
                "preferred_contact": r[13] or "whatsapp",
            }
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
