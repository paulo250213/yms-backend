import os
import base64
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Mapeia a pasta atual para servir arquivos estáticos (como logo.png)
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/", response_class=HTMLResponse)
def get_form():
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diniz Alimentos - Agendamento de Carga</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #0b192c 0%, #1e3e62 100%);
            min-height: 100vh;
            margin: 0;
            padding: 20px 10px;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .container {{
            background-color: #ffffff;
            width: 100%;
            max-width: 500px;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        }}
        .logo-container {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .logo-container img {{
            max-width: 220px;
            height: auto;
        }}
        h2 {{
            color: #0b192c;
            text-align: center;
            margin-top: 0;
            margin-bottom: 20px;
            font-weight: 600;
        }}
        .form-group {{
            margin-bottom: 15px;
        }}
        label {{
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-size: 14px;
            font-weight: 600;
        }}
        input[type="text"], input[type="number"], input[type="datetime-local"] {{
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #ccc;
            border-radius: 6px;
            font-size: 14px;
            outline: none;
        }}
        input:focus {{
            border-color: #1e3e62;
        }}
        button {{
            width: 100%;
            background-color: #0b192c;
            color: white;
            padding: 12px;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 10px;
            transition: background 0.3s;
        }}
        button:hover {{
            background-color: #1e3e62;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo-container">
            <img src="/static/logo.png" alt="Diniz Alimentos Logo">
        </div>
        <h2>Agendamento de Carga</h2>
        <form action="/submit" method="post">
            <div class="form-group">
                <label for="fornecedor">Nome do Fornecedor:</label>
                <input type="text" id="fornecedor" name="fornecedor" required>
            </div>
            <div class="form-group">
                <label for="nota_fiscal">Número da Nota Fiscal:</label>
                <input type="text" id="nota_fiscal" name="nota_fiscal" required>
            </div>
            <div class="form-group">
                <label for="peso">Peso da Carga (kg):</label>
                <input type="number" id="peso" name="peso" step="0.01" required>
            </div>
            <div class="form-group">
                <label for="data_agendamento">Data e Horário Pretendido:</label>
                <input type="datetime-local" id="data_agendamento" name="data_agendamento" required>
            </div>
            <button type="submit">Enviar Agendamento</button>
        </form>
    </div>
</body>
</html>
    """

@app.post("/submit", response_class=HTMLResponse)
def submit_form(
    fornecedor: str = Form(...),
    nota_fiscal: str = Form(...),
    peso: float = Form(...),
    data_agendamento: str = Form(...)
):
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Agendamento Recebido</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f6f9;
            padding: 40px;
            text-align: center;
        }}
        .card {{
            background: white;
            max-width: 400px;
            margin: 0 auto;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }}
        h2 {{ color: #2e7d32; }}
    </style>
</head>
<body>
    <div class="card">
        <h2>Agendamento Realizado!</h2>
        <p><strong>Fornecedor:</strong> {fornecedor}</p>
        <p><strong>NF:</strong> {nota_fiscal}</p>
        <p><strong>Peso:</strong> {peso} kg</p>
        <p><strong>Data/Hora:</strong> {data_agendamento}</p>
        <br>
        <a href="/">Fazer outro agendamento</a>
    </div>
</body>
</html>
    """
