import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

app = FastAPI(title="DINIZ - YMS Agendamento de Entregas")

DATABASE_URL = os.getenv("DATABASE_URL")

# Configurações de E-mail via Variáveis de Ambiente
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL")
APP_URL = os.getenv("APP_URL", "https://seu-app.onrender.com")


def send_email_notification(schedule_data: dict):
    if not SMTP_EMAIL or not SMTP_PASSWORD or not NOTIFY_EMAIL:
        print("AVISO: Configurações de e-mail não encontradas nas variáveis de ambiente.")
        return

    try:
        subject = f"📬 Novo Agendamento Pendente - {schedule_data['supplier_name']}"
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px;">
                <h2 style="color: #0b192c; border-bottom: 3px solid #ffc107; padding-bottom: 10px; margin-top: 0;">
                    DINIZ FOODS - Novo Agendamento
                </h2>
                <p>Uma nova solicitação de agendamento foi registrada e está <strong>aguardando sua aprovação</strong>.</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0; background: #f9f9f9;">
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Fornecedor:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{schedule_data['supplier_name']}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Contato Preferencial:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{schedule_data.get('preferred_contact', 'whatsapp').upper()}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Dado de Contato:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{schedule_data.get('phone') if schedule_data.get('preferred_contact') == 'whatsapp' else schedule_data.get('email')}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Placa do Veículo:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{schedule_data['truck_plate']}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Peso da Carga:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{schedule_data['cargo_weight']} kg</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Tipo de Armazenamento:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{schedule_data['storage_type']}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Tipo da Carga:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{schedule_data['cargo_type']} ({schedule_data['pallet_quantity']} Qtd.)</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Guichê / Doca:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">Guichê {schedule_data['dock_id']}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Data Prevista:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{schedule_data['schedule_date']}</td></tr>
                    <tr><td style="padding: 8px;"><strong>Pré-Senha:</strong></td><td style="padding: 8px;"><strong style="color: #137333;">{schedule_data['access_code']}</strong></td></tr>
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

        print("E-mail de notificação enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail de notificação: {e}")


def init_db():
    if not DATABASE_URL:
        return
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schedules (
                id SERIAL PRIMARY KEY,
                supplier_name VARCHAR(100) NOT NULL,
                truck_plate VARCHAR(20) NOT NULL,
                cargo_weight NUMERIC(10, 2) NOT NULL,
                storage_type VARCHAR(20) NOT NULL,
                dock_id INT NOT NULL DEFAULT 10,
                schedule_time DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            ALTER TABLE schedules ADD COLUMN IF NOT EXISTS cargo_type VARCHAR(20);
            ALTER TABLE schedules ADD COLUMN IF NOT EXISTS pallet_quantity INT DEFAULT 0;
            ALTER TABLE schedules ADD COLUMN IF NOT EXISTS access_code VARCHAR(20);
            ALTER TABLE schedules ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'Pendente';
            ALTER TABLE schedules ADD COLUMN IF NOT EXISTS phone VARCHAR(30);
            ALTER TABLE schedules ADD COLUMN IF NOT EXISTS email VARCHAR(100);
            ALTER TABLE schedules ADD COLUMN IF NOT EXISTS preferred_contact VARCHAR(20) DEFAULT 'whatsapp';
            """
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Erro ao inicializar o banco:", e)


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


@app.get("/manual.pdf")
def get_manual():
    pdf_path = "manual.pdf"
    if os.path.exists(pdf_path):
        return FileResponse(pdf_path, media_type="application/pdf", filename="Manual_do_Fornecedor_Diniz.pdf")
    elif os.path.exists("Manual do Fornecedor Diniz Foods - Versão Corrigida.pdf"):
        return FileResponse("Manual do Fornecedor Diniz Foods - Versão Corrigida.pdf", media_type="application/pdf", filename="Manual_do_Fornecedor_Diniz.pdf")
    else:
        raise HTTPException(status_code=404, detail="Manual em PDF não encontrado no servidor.")


@app.get("/", response_class=HTMLResponse)
def get_form():
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Diniz Foods - Agendamento de Carga</title>
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
                background: linear-gradient(90deg, #0b192c 0%, #1e3e62 100%);
                padding: 25px 20px;
                text-align: center;
                border-bottom: 4px solid #ffc107;
                color: white;
            }
            .brand-title { font-size: 24px; font-weight: 700; letter-spacing: 1px; margin: 0; color: #ffffff; }
            .brand-title span { color: #ffc107; }
            .slogan { font-size: 13px; color: #ffc107; font-weight: 600; margin-top: 6px; letter-spacing: 0.5px; }
            
            .info-box {
                background-color: #fff9e6;
                border-left: 5px solid #ffc107;
                padding: 15px 20px;
                margin: 20px 30px 0 30px;
                border-radius: 6px;
            }
            .info-box-title {
                font-weight: 700;
                color: #0b192c;
                font-size: 14px;
                margin-bottom: 6px;
                display: flex;
                align-items: center;
                gap: 6px;
            }
            .info-box-text { font-size: 12px; color: #444; line-height: 1.5; margin-bottom: 8px; }
            .info-box-time {
                font-weight: 700;
                color: #b78103;
                background: #fff0c2;
                padding: 4px 8px;
                border-radius: 4px;
                display: inline-block;
                margin-bottom: 8px;
                font-size: 12px;
            }
            .info-box-alert {
                font-weight: 700;
                color: #0b192c;
                background: #ffe89c;
                padding: 6px 10px;
                border-radius: 4px;
                display: block;
                margin-bottom: 12px;
                font-size: 12px;
            }
            .btn-manual {
                display: inline-block;
                width: 100%;
                text-align: center;
                background-color: #0b192c;
                color: #ffc107;
                padding: 10px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 700;
                text-decoration: none;
                transition: background 0.2s;
            }
            .btn-manual:hover { background-color: #1e3e62; }

            .form-body { padding: 20px 30px 25px 30px; }
            .form-group { margin-bottom: 18px; }
            label { display: block; margin-bottom: 6px; font-weight: 600; color: #2b2b2b; font-size: 13px; }
            input, select { 
                width: 100%; 
                padding: 12px 14px; 
                border: 1.5px solid #dcdfe6; 
                border-radius: 6px; 
                font-size: 14px;
                font-family: inherit;
                transition: border-color 0.2s;
            }
            input:focus, select:focus { outline: none; border-color: #0b192c; }
            .uppercase-input { text-transform: uppercase; }
            button.btn-submit { 
                width: 100%; 
                padding: 14px; 
                background: linear-gradient(90deg, #ffc107 0%, #e0a800 100%); 
                color: #0b192c; 
                border: none; 
                border-radius: 6px; 
                font-size: 16px; 
                cursor: pointer; 
                font-weight: 700; 
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-top: 10px;
                box-shadow: 0 4px 12px rgba(255, 193, 7, 0.3);
                transition: transform 0.1s, box-shadow 0.2s;
            }
            button.btn-submit:hover { 
                background: linear-gradient(90deg, #e0a800 0%, #c69500 100%); 
                transform: translateY(-1px);
            }
            .message { 
                margin-top: 20px; 
                padding: 15px; 
                border-radius: 6px; 
                display: none; 
                text-align: center; 
                font-size: 14px; 
                line-height: 1.5; 
            }
            .success { background-color: #e6f4ea; color: #137333; border: 1px solid #ceead6; }
            .error { background-color: #fce8e6; color: #c5221f; border: 1px solid #fad2cf; }
            .code-highlight { 
                font-size: 22px; 
                font-weight: 700; 
                background: #ffffff; 
                padding: 6px 14px; 
                border-radius: 6px; 
                display: inline-block; 
                margin-top: 8px; 
                border: 2px dashed #137333; 
                color: #137333; 
                letter-spacing: 2px;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header-banner">
                <div class="brand-title">DINIZ <span>FOODS</span></div>
                <div class="slogan">COM A DINIZ VOCÊ FAZ MAIS!</div>
            </div>

            <div class="info-box">
                <div class="info-box-title">📌 Informações Importantes</div>
                <div class="info-box-time">⏰ Recebimento: Das 07:30 às 12:00</div>
                <div class="info-box-alert">📄 Entregar nota fiscal ao lado da doca 10</div>
                <div class="info-box-text">
                    Todas as normas operacionais, regras de conduta, EPIs e padrões de carga estão detalhados no nosso manual oficial.
                </div>
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
                        <label for="qtyLabel" id="qtyLabel">QUANTIDADE DE PALETES:</label>
                        <input type="number" id="qtyInput" value="0" min="0" placeholder="Ex: 26" required>
                    </div>
                    <div class="form-group">
                        <label for="dock">GUICHÊ DE RECEBIMENTO:</label>
                        <select id="dock" required>
                            <option value="10" selected>Guichê 10</option>
                            <option value="1">Guichê 1</option>
                            <option value="2">Guichê 2</option>
                            <option value="3">Guichê 3</option>
                            <option value="4">Guichê 4</option>
                            <option value="5">Guichê 5</option>
                        </select>
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
                const phoneGroup = document.getElementById('phoneGroup');
                const emailGroup = document.getElementById('emailGroup');
                const phoneInput = document.getElementById('phone');
                const emailInput = document.getElementById('email');

                if (contactType === 'whatsapp') {
                    phoneGroup.style.display = 'block';
                    emailGroup.style.display = 'none';
                    phoneInput.required = true;
                    emailInput.required = false;
                } else {
                    phoneGroup.style.display = 'none';
                    emailGroup.style.display = 'block';
                    phoneInput.required = false;
                    emailInput.required = true;
                }
            }

            function toggleQuantityInput() {
                const cargoType = document.getElementById('cargoType').value;
                const qtyLabel = document.getElementById('qtyLabel');
                const qtyInput = document.getElementById('qtyInput');
                
                if (cargoType === 'Batida') {
                    qtyLabel.innerText = 'QUANTIDADE DE VOLUMES:';
                    qtyInput.placeholder = 'Ex: 150 (Caixas/Sacos)';
                } else {
                    qtyLabel.innerText = 'QUANTIDADE DE PALETES:';
                    qtyInput.placeholder = 'Ex: 26';
                }
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
                    dock_id: parseInt(document.getElementById('dock').value),
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
                        msgDiv.innerHTML = `Solicitação enviada com sucesso!<br><strong>Status: Pendente de Aprovação</strong><br>Sua pré-senha é:<br><span class="code-highlight">${randomCode}</span>`;
                        document.getElementById('scheduleForm').reset();
                        toggleContactInput();
                        toggleQuantityInput();
                    } else {
                        msgDiv.className = 'message error';
                        msgDiv.innerText = data.detail || 'Erro ao realizar agendamento.';
                    }
                } catch (err) {
                    msgDiv.className = 'message error';
                    msgDiv.innerText = 'Erro na conexão com o servidor.';
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
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Diniz Foods - Gestão de Agendamentos</title>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            * { box-sizing: border-box; }
            body { 
                font-family: 'Poppins', sans-serif; 
                background-color: #f4f6f9; 
                margin: 0; 
                padding: 15px; 
            }
            .container { 
                background: white; 
                padding: 20px; 
                border-radius: 12px; 
                box-shadow: 0 4px 20px rgba(0,0,0,0.08); 
                max-width: 100%; 
                margin: 0 auto; 
            }
            .header-bar {
                display: flex;
                align-items: center;
                justify-content: space-between;
                border-bottom: 3px solid #ffc107;
                padding-bottom: 12px;
                margin-bottom: 15px;
                flex-wrap: wrap;
                gap: 15px;
            }
            .brand-info { display: flex; align-items: center; gap: 12px; }
            .brand-info h2 { margin: 0; color: #0b192c; font-size: 18px; }
            .brand-info p { margin: 0; color: #666; font-size: 11px; font-weight: 600; }
            
            .btn-group { display: flex; gap: 10px; }
            .btn { 
                padding: 8px 14px; 
                border-radius: 6px; 
                text-decoration: none; 
                font-weight: 600; 
                cursor: pointer; 
                display: inline-flex;
                align-items: center;
                gap: 6px;
                font-size: 12px;
                border: none;
            }
            .btn-pdf { background-color: #0b192c; color: #ffc107; }
            .btn-pdf:hover { background-color: #1e3e62; }
            .btn-new { background-color: #ffc107; color: #0b192c; }
            .btn-new:hover { background-color: #e0a800; }
            .btn-clear { background-color: #6c757d; color: white; padding: 8px 12px; border-radius: 6px; border: none; cursor: pointer; font-weight: 600; font-size: 12px; }
            .btn-clear:hover { background-color: #5a6268; }

            .filter-bar {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 12px 15px;
                margin-bottom: 15px;
                display: flex;
                gap: 12px;
                align-items: flex-end;
                flex-wrap: wrap;
            }
            .filter-group {
                display: flex;
                flex-direction: column;
                gap: 4px;
                flex: 1;
                min-width: 140px;
            }
            .filter-group label {
                font-size: 11px;
                font-weight: 700;
                color: #0b192c;
            }
            .filter-group input, .filter-group select {
                padding: 7px 10px;
                border: 1px solid #ced4da;
                border-radius: 6px;
                font-size: 12px;
                font-family: inherit;
            }
            .filter-group input:focus, .filter-group select:focus { outline: none; border-color: #0b192c; }

            .table-responsive {
                width: 100%;
                overflow-x: auto;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }

            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 12px 10px; border-bottom: 1px solid #e9ecef; text-align: left; font-size: 12px; }
            th { background-color: #0b192c; color: #ffffff; font-weight: 600; white-space: nowrap; }
            tr:nth-child(even) { background-color: #fcfcfc; }
            tr:hover { background-color: #f1f3f5; }

            .action-btns { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
            .btn-action {
                color: white; 
                padding: 6px 12px; 
                border-radius: 4px; 
                text-decoration: none; 
                font-size: 12px; 
                font-weight: bold; 
                border: none;
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                gap: 4px;
            }
            .btn-app { background-color: #28a745; }
            .btn-app:hover { background-color: #218838; }
            .btn-rej { background-color: #dc3545; }
            .btn-rej:hover { background-color: #c82333; }

            .btn-delete { 
                background-color: #6c757d; 
                color: white; 
                border: none; 
                padding: 6px 10px; 
                border-radius: 4px; 
                cursor: pointer; 
                font-weight: 600; 
                font-size: 12px; 
            }
            .btn-delete:hover { background-color: #5a6268; }

            .status-badge {
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 700;
                display: inline-block;
            }
            .status-pendente { background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; }
            .status-aprovado { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .status-recusado { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }

            .code-badge { 
                font-weight: 700; 
                background: #eef2f5; 
                padding: 4px 8px; 
                border-radius: 4px; 
                letter-spacing: 1px; 
                color: #0b192c; 
                border: 1px solid #ced4da; 
            }
            .no-data { text-align: center; padding: 30px; color: #777; }

            @media print {
                body { background-color: #fff; padding: 0; }
                .container { box-shadow: none; max-width: 100%; padding: 0; }
                .no-print, .action-column, .filter-bar { display: none !important; }
                .table-responsive { overflow: visible; border: none; }
                .header-bar { border-bottom: 2px solid #000; padding-bottom: 10px; }
                th { background-color: #eee !important; color: #000 !important; }
                table { font-size: 10px; }
                th, td { padding: 5px; border: 1px solid #ccc; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header-bar no-print">
                <div class="brand-info">
                    <div>
                        <h2>DINIZ FOODS - Gestão de Agendamentos</h2>
                        <p>COM A DINIZ VOCÊ FAZ MAIS!</p>
                    </div>
                </div>
                <div class="btn-group">
                    <button class="btn btn-pdf" onclick="window.print()">📄 Exportar PDF</button>
                    <a href="/" class="btn btn-new">➕ Novo Agendamento</a>
                </div>
            </div>

            <div class="filter-bar no-print">
                <div class="filter-group">
                    <label for="filterStatus">📌 Status:</label>
                    <select id="filterStatus" onchange="applyFilters()">
                        <option value="">Todos</option>
                        <option value="Pendente">⏳ Pendentes</option>
                        <option value="Aprovado">✅ Aprovados</option>
                        <option value="Recusado">❌ Recusados</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="filterDate">📅 Data de Chegada:</label>
                    <input type="date" id="filterDate" onchange="applyFilters()">
                </div>
                <div class="filter-group">
                    <label for="filterSearch">🔍 Buscar (Fornecedor, Placa, Senha):</label>
                    <input type="text" id="filterSearch" placeholder="Digite para buscar..." oninput="applyFilters()">
                </div>
                <button class="btn-clear" onclick="clearFilters()">🔄 Limpar</button>
            </div>

            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Senha</th>
                            <th>Status</th>
                            <th>Fornecedor</th>
                            <th>Contato</th>
                            <th>Placa</th>
                            <th>Guichê</th>
                            <th>Data</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody id="tableBody">
                        <tr><td colspan="9" class="no-data">Carregando agendamentos...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <script>
            let allSchedules = [];

            async function loadSchedules() {
                try {
                    const res = await fetch('/api/schedules');
                    allSchedules = await res.json();
                    renderTable(allSchedules);
                } catch (err) {
                    console.error(err);
                    document.getElementById('tableBody').innerHTML = '<tr><td colspan="9" class="no-data" style="color:red;">Erro ao carregar dados.</td></tr>';
                }
            }

            function renderTable(data) {
                const tbody = document.getElementById('tableBody');
                tbody.innerHTML = '';

                if (data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="9" class="no-data">Nenhum agendamento encontrado para os filtros selecionados.</td></tr>';
                    return;
                }

                data.forEach(row => {
                    const tr = document.createElement('tr');
                    const statusClass = row.status === 'Aprovado' ? 'status-aprovado' : (row.status === 'Recusado' ? 'status-recusado' : 'status-pendente');

                    const contactPref = row.preferred_contact || 'whatsapp';
                    const phoneNum = row.phone || '';
                    const emailAddr = row.email || '';

                    let contactDisplay = '-';
                    let btnApprove = '';
                    let btnReject = '';

                    if (contactPref === 'whatsapp' || phoneNum) {
                        contactDisplay = `📱 ${phoneNum}`;
                        const textApprove = encodeURIComponent(`Olá! Seu agendamento para o dia ${row.schedule_time} (Guichê ${row.dock_id}) na Diniz Foods foi APROVADO. Sua pré-senha é: ${row.access_code}.`);
                        const textReject = encodeURIComponent(`Olá! Infelizmente seu agendamento para o dia ${row.schedule_time} não pôde ser aprovado. Por favor, acesse nosso site e faça uma nova solicitação.`);
                        
                        btnApprove = `<a class="btn-action btn-app" href="https://wa.me/${phoneNum}?text=${textApprove}" target="_blank" onclick="updateStatus(${row.id}, 'Aprovado')">Aprovar</a>`;
                        btnReject = `<a class="btn-action btn-rej" href="https://wa.me/${phoneNum}?text=${textReject}" target="_blank" onclick="updateStatus(${row.id}, 'Recusado')">Recusar</a>`;
                    } else if (contactPref === 'email' || emailAddr) {
                        contactDisplay = `✉️ ${emailAddr}`;
                        const emailSubjApprove = encodeURIComponent(`Agendamento Aprovado - Diniz Foods`);
                        const emailBodyApprove = encodeURIComponent(`Olá,\n\nSeu agendamento para o dia ${row.schedule_time} (Guichê ${row.dock_id}) foi APROVADO.\n\nPré-Senha: ${row.access_code}\n\nAtenciosamente,\nDiniz Foods`);

                        const emailSubjReject = encodeURIComponent(`Solicitação de Agendamento Não Aprovada - Diniz Foods`);
                        const emailBodyReject = encodeURIComponent(`Olá,\n\nSua solicitação de agendamento para o dia ${row.schedule_time} não pôde ser aprovada.\n\nPor favor, acesse nosso site e realize uma nova solicitação selecionando outra data.\n\nAtenciosamente,\nDiniz Foods`);

                        btnApprove = `<a class="btn-action btn-app" href="mailto:${emailAddr}?subject=${emailSubjApprove}&body=${emailBodyApprove}" onclick="updateStatus(${row.id}, 'Aprovado')">Aprovar</a>`;
                        btnReject = `<a class="btn-action btn-rej" href="mailto:${emailAddr}?subject=${emailSubjReject}&body=${emailBodyReject}" onclick="updateStatus(${row.id}, 'Recusado')">Recusar</a>`;
                    } else {
                        btnApprove = `<button class="btn-action btn-app" onclick="updateStatus(${row.id}, 'Aprovado')">Aprovar</button>`;
                        btnReject = `<button class="btn-action btn-rej" onclick="updateStatus(${row.id}, 'Recusado')">Recusar</button>`;
                    }

                    tr.innerHTML = `
                        <td>${row.id}</td>
                        <td><span class="code-badge">${row.access_code || '-'}</span></td>
                        <td><span class="status-badge ${statusClass}">${row.status || 'Pendente'}</span></td>
                        <td><strong>${row.supplier_name}</strong></td>
                        <td>${contactDisplay}</td>
                        <td>${row.truck_plate}</td>
                        <td>Guichê ${row.dock_id}</td>
                        <td>${row.schedule_time}</td>
                        <td>
                            <div class="action-btns">
                                ${btnApprove}
                                ${btnReject}
                                <button class="btn-delete" title="Excluir" onclick="deleteSchedule(${row.id})">🗑️</button>
                            </div>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            }

            function applyFilters() {
                const statusVal = document.getElementById('filterStatus').value;
                const dateVal = document.getElementById('filterDate').value;
                const searchVal = document.getElementById('filterSearch').value.toLowerCase().trim();

                const filtered = allSchedules.filter(item => {
                    const matchStatus = !statusVal || (item.status || 'Pendente') === statusVal;
                    const matchDate = !dateVal || item.schedule_time === dateVal;
                    const matchSearch = !searchVal || 
                        (item.supplier_name && item.supplier_name.toLowerCase().includes(searchVal)) ||
                        (item.truck_plate && item.truck_plate.toLowerCase().includes(searchVal)) ||
                        (item.access_code && item.access_code.toLowerCase().includes(searchVal));

                    return matchStatus && matchDate && matchSearch;
                });

                renderTable(filtered);
            }

            function clearFilters() {
                document.getElementById('filterStatus').value = '';
                document.getElementById('filterDate').value = '';
                document.getElementById('filterSearch').value = '';
                renderTable(allSchedules);
            }

            async function updateStatus(id, newStatus) {
                try {
                    await fetch(`/api/schedule/${id}/status`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ status: newStatus })
                    });
                    setTimeout(loadSchedules, 800);
                } catch (err) {
                    console.error('Erro ao atualizar status');
                }
            }

            async function deleteSchedule(id) {
                if (confirm(`Tem certeza que deseja excluir o agendamento ID ${id}?`)) {
                    try {
                        const res = await fetch(`/api/schedule/${id}`, { method: 'DELETE' });
                        if (res.ok) {
                            loadSchedules();
                        } else {
                            alert('Erro ao excluir agendamento.');
                        }
                    } catch (err) {
                        alert('Erro de conexão ao excluir.');
                    }
                }
            }

            window.onload = loadSchedules;
        </script>
    </body>
    </html>
    """


@app.post("/api/schedule")
def create_schedule(req: ScheduleRequest):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

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
        cur.close()
        conn.close()

        send_email_notification(req.dict())

        return {"status": "sucesso", "mensagem": "Solicitação registrada com sucesso!"}
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/schedule/{schedule_id}/status")
def update_schedule_status(schedule_id: int, req: StatusUpdateRequest):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            "UPDATE schedules SET status = %s WHERE id = %s;",
            (req.status, schedule_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "sucesso", "mensagem": f"Status alterado para {req.status}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/schedule/{schedule_id}")
def delete_schedule(schedule_id: int):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("DELETE FROM schedules WHERE id = %s;", (schedule_id,))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "sucesso", "mensagem": "Agendamento excluído com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/schedules")
def list_schedules():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, supplier_name, truck_plate, cargo_weight, storage_type, 
                   cargo_type, pallet_quantity, dock_id, TO_CHAR(schedule_time, 'YYYY-MM-DD'), 
                   access_code, status, phone, email, preferred_contact
            FROM schedules
            ORDER BY supplier_name ASC;
            """
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        result = []
        for r in rows:
            result.append(
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
                    "status": r[10] if r[10] else "Pendente",
                    "phone": r[11] if len(r) > 11 and r[11] else "",
                    "email": r[12] if len(r) > 12 and r[12] else "",
                    "preferred_contact": r[13] if len(r) > 13 and r[13] else "whatsapp",
                }
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
