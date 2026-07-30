import os
import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="YMS - Agendamento de Entregas")

DATABASE_URL = os.getenv("DATABASE_URL")


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
                dock_id INT NOT NULL,
                schedule_time DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            ALTER TABLE schedules ADD COLUMN IF NOT EXISTS cargo_type VARCHAR(20);
            ALTER TABLE schedules ADD COLUMN IF NOT EXISTS pallet_quantity INT DEFAULT 0;
            ALTER TABLE schedules ADD COLUMN IF NOT EXISTS access_code VARCHAR(20);
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
    truck_plate: str
    cargo_weight: float
    storage_type: str
    cargo_type: str
    pallet_quantity: int
    dock_id: int
    schedule_date: str
    access_code: str


# --- TELA DE FORMULÁRIO (HOME - SEM O LINK DE CONSULTA) ---
@app.get("/", response_class=HTMLResponse)
def get_form():
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>YMS - Agendamento de Entregas</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; display: flex; justify-content: center; }
            .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); width: 100%; max-width: 480px; }
            h2 { color: #333; margin-top: 0; text-align: center; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; color: #555; }
            input, select { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
            .uppercase-input { text-transform: uppercase; }
            button { width: 100%; padding: 12px; background-color: #007bff; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; font-weight: bold; }
            button:hover { background-color: #0056b3; }
            .message { margin-top: 15px; padding: 15px; border-radius: 4px; display: none; text-align: center; font-size: 15px; line-height: 1.5; }
            .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .code-highlight { font-size: 20px; font-weight: bold; background: #fff; padding: 5px 10px; border-radius: 4px; display: inline-block; margin-top: 5px; border: 1px dashed #28a745; color: #155724; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Agendamento de Carga / Doca</h2>
            <form id="scheduleForm">
                <div class="form-group">
                    <label for="supplier">Nome do Fornecedor:</label>
                    <input type="text" id="supplier" class="uppercase-input" required placeholder="EX: SILVA ALIMENTOS">
                </div>
                <div class="form-group">
                    <label for="plate">Placa do Veículo:</label>
                    <input type="text" id="plate" class="uppercase-input" required placeholder="EX: ABC1D23">
                </div>
                <div class="form-group">
                    <label for="weight">Peso da Carga (kg):</label>
                    <input type="number" step="0.1" id="weight" required placeholder="Ex: 1500.50">
                </div>
                <div class="form-group">
                    <label for="storage">Tipo de Armazenamento:</label>
                    <select id="storage" required>
                        <option value="Seco">Seco</option>
                        <option value="Resfriado">Resfriado</option>
                        <option value="Congelado">Congelado</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="cargoType">Tipo da Carga:</label>
                    <select id="cargoType" required onchange="togglePalletInput()">
                        <option value="Paletizada">Paletizada</option>
                        <option value="Batida">Batida (Carga Solta)</option>
                    </select>
                </div>
                <div class="form-group" id="palletGroup">
                    <label for="palletQty">Quantidade de Paletes:</label>
                    <input type="number" id="palletQty" value="0" min="0" placeholder="Ex: 26">
                </div>
                <div class="form-group">
                    <label for="dock">Doca de Descarregamento:</label>
                    <select id="dock" required>
                        <option value="1">Doca 01</option>
                        <option value="2">Doca 02</option>
                        <option value="3">Doca 03</option>
                        <option value="4">Doca 04</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="scheduleDate">Data da Chegada:</label>
                    <input type="date" id="scheduleDate" required>
                </div>
                <button type="submit">Confirmar Agendamento</button>
            </form>
            <div id="responseMsg" class="message"></div>
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

            function togglePalletInput() {
                const cargoType = document.getElementById('cargoType').value;
                const palletQty = document.getElementById('palletQty');
                if (cargoType === 'Batida') {
                    palletQty.value = 0;
                    palletQty.disabled = true;
                } else {
                    palletQty.disabled = false;
                }
            }

            document.getElementById('scheduleForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const msgDiv = document.getElementById('responseMsg');
                msgDiv.style.display = 'none';

                const randomCode = generateRandomCode();

                const payload = {
                    supplier_name: document.getElementById('supplier').value.toUpperCase(),
                    truck_plate: document.getElementById('plate').value.toUpperCase(),
                    cargo_weight: parseFloat(document.getElementById('weight').value),
                    storage_type: document.getElementById('storage').value,
                    cargo_type: document.getElementById('cargoType').value,
                    pallet_quantity: parseInt(document.getElementById('palletQty').value || 0),
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
                        msgDiv.innerHTML = `Agendamento realizado com sucesso!<br>Sua senha de acesso é:<br><span class="code-highlight">${randomCode}</span>`;
                        document.getElementById('scheduleForm').reset();
                        togglePalletInput();
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


# --- TELA DE CONSULTA DE AGENDAMENTOS ---
@app.get("/agendamentos", response_class=HTMLResponse)
def list_schedules_page():
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>YMS - Consulta de Agendamentos</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; }
            .container { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 1150px; margin: 0 auto; }
            h2 { color: #333; margin-top: 0; text-align: center; }
            .top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; gap: 10px; }
            .btn-group { display: flex; gap: 10px; }
            .btn { padding: 10px 15px; background-color: #007bff; color: white; border: none; border-radius: 4px; text-decoration: none; font-weight: bold; cursor: pointer; display: inline-block; }
            .btn:hover { background-color: #0056b3; }
            .btn-pdf { background-color: #28a745; }
            .btn-pdf:hover { background-color: #218838; }
            .btn-delete { background-color: #dc3545; color: white; border: none; padding: 6px 10px; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 12px; }
            .btn-delete:hover { background-color: #c82333; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th, td { padding: 10px; border: 1px solid #ddd; text-align: center; font-size: 13px; }
            th { background-color: #f8f9fa; color: #333; font-weight: bold; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            tr:hover { background-color: #f1f1f1; }
            .code-badge { font-weight: bold; background: #e9ecef; padding: 4px 8px; border-radius: 4px; letter-spacing: 1px; color: #007bff; border: 1px solid #ced4da; }
            .no-data { text-align: center; padding: 20px; color: #777; }

            /* Estilos específicos para a impressão em PDF */
            @media print {
                body { background-color: #fff; padding: 0; }
                .container { box-shadow: none; max-width: 100%; padding: 0; }
                .no-print, .action-column { display: none !important; }
                h2 { margin-bottom: 15px; font-size: 20px; text-align: left; }
                table { font-size: 11px; }
                th, td { padding: 6px; }
                .code-badge { border: none; background: transparent; color: #000; padding: 0; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="top-bar no-print">
                <h2>Lista de Agendamentos Realizados</h2>
                <div class="btn-group">
                    <button class="btn btn-pdf" onclick="window.print()">📄 Exportar PDF / Imprimir</button>
                    <a href="/" class="btn">➕ Novo Agendamento</a>
                </div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Senha</th>
                        <th>Fornecedor</th>
                        <th>Placa</th>
                        <th>Peso (kg)</th>
                        <th>Armazenamento</th>
                        <th>Tipo Carga</th>
                        <th>Paletes</th>
                        <th>Doca</th>
                        <th>Data Chegada</th>
                        <th class="action-column">Ações</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                    <tr><td colspan="11" class="no-data">Carregando agendamentos...</td></tr>
                </tbody>
            </table>
        </div>

        <script>
            async function loadSchedules() {
                try {
                    const res = await fetch('/api/schedules');
                    const data = await res.json();
                    const tbody = document.getElementById('tableBody');
                    tbody.innerHTML = '';

                    if (data.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="11" class="no-data">Nenhum agendamento encontrado.</td></tr>';
                        return;
                    }

                    data.forEach(row => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td>${row.id}</td>
                            <td><span class="code-badge">${row.access_code || '-'}</span></td>
                            <td><strong>${row.supplier_name}</strong></td>
                            <td>${row.truck_plate}</td>
                            <td>${row.cargo_weight}</td>
                            <td>${row.storage_type}</td>
                            <td>${row.cargo_type || '-'}</td>
                            <td>${row.pallet_quantity}</td>
                            <td>Doca 0${row.dock_id}</td>
                            <td>${row.schedule_time}</td>
                            <td class="action-column">
                                <button class="btn-delete" onclick="deleteSchedule(${row.id})">🗑️ Excluir</button>
                            </td>
                        `;
                        tbody.appendChild(tr);
                    });
                } catch (err) {
                    console.error(err);
                    document.getElementById('tableBody').innerHTML = '<tr><td colspan="11" class="no-data" style="color:red;">Erro ao carregar dados.</td></tr>';
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


# --- API PARA SALVAR AGENDAMENTO ---
@app.post("/api/schedule")
def create_schedule(req: ScheduleRequest):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO schedules (
                supplier_name, truck_plate, cargo_weight, storage_type, 
                cargo_type, pallet_quantity, dock_id, schedule_time, access_code
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                req.supplier_name.upper(),
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
        return {"status": "sucesso", "mensagem": "Agendamento registrado com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- API PARA EXCLUIR AGENDAMENTO ---
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


# --- API PARA LISTAR OS AGENDAMENTOS EM JSON ---
@app.get("/api/schedules")
def list_schedules():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, supplier_name, truck_plate, cargo_weight, storage_type, 
                   cargo_type, pallet_quantity, dock_id, TO_CHAR(schedule_time, 'YYYY-MM-DD'), access_code
            FROM schedules
            ORDER BY id DESC;
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
                }
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
