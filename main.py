import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import psycopg2

app = FastAPI(title="YMS - Agendamento de Entregas")

# Pega a URL do banco configurada no Render
DATABASE_URL = os.getenv("DATABASE_URL")


class ScheduleRequest(BaseModel):
    supplier_name: str
    truck_plate: str
    cargo_weight: float
    storage_type: str
    cargo_type: str
    pallet_quantity: int
    dock_id: int
    schedule_date: str


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
            button { width: 100%; padding: 12px; background-color: #007bff; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; font-weight: bold; }
            button:hover { background-color: #0056b3; }
            .message { margin-top: 15px; padding: 10px; border-radius: 4px; display: none; text-align: center; }
            .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Agendamento de Carga / Doca</h2>
            <form id="scheduleForm">
                <div class="form-group">
                    <label for="supplier">Nome do Fornecedor:</label>
                    <input type="text" id="supplier" required placeholder="Ex: Silva Alimentos">
                </div>
                <div class="form-group">
                    <label for="plate">Placa do Veículo:</label>
                    <input type="text" id="plate" required placeholder="Ex: ABC1D23">
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

                const payload = {
                    supplier_name: document.getElementById('supplier').value,
                    truck_plate: document.getElementById('plate').value,
                    cargo_weight: parseFloat(document.getElementById('weight').value),
                    storage_type: document.getElementById('storage').value,
                    cargo_type: document.getElementById('cargoType').value,
                    pallet_quantity: parseInt(document.getElementById('palletQty').value || 0),
                    dock_id: parseInt(document.getElementById('dock').value),
                    schedule_date: document.getElementById('scheduleDate').value
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
                        msgDiv.innerText = 'Agendamento realizado com sucesso!';
                        document.getElementById('scheduleForm').reset();
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


@app.post("/api/schedule")
def create_schedule(req: ScheduleRequest):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO schedules (
                supplier_name, truck_plate, cargo_weight, storage_type, 
                cargo_type, pallet_quantity, dock_id, schedule_time
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                req.supplier_name,
                req.truck_plate,
                req.cargo_weight,
                req.storage_type,
                req.cargo_type,
                req.pallet_quantity,
                req.dock_id,
                req.schedule_date,
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "sucesso", "mensagem": "Agendamento registrado com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
