import os
import base64
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse

app = FastAPI()

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
            background-color: #0b192c;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        .container {{
            background-color: #ffffff;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 600px;
        }}
        h2 {{
            color: #0b192c;
            text-align: center;
            margin-bottom: 20px;
        }}
        .form-group {{
            margin-bottom: 20px;
        }}
        label {{
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }}
        input[type="text"], input[type="number"], select {{
            width: 100%;
            padding: 12px;
            border: 1px solid #ccc;
            border-radius: 6px;
            font-size: 14px;
        }}
        button {{
            background-color: #ff6500;
            color: white;
            border: none;
            padding: 12px;
            width: 100%;
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
        <h2 style="color: #0b192c; text-align: center; margin-bottom: 20px;">Diniz Foods</h2>
        
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
            <button type="submit">Enviar Agendamento</button>
        </form>
    </div>
</body>
</html>
    """

@app.post("/submit")
def submit_form(fornecedor: str = Form(...), nota_fiscal: str = Form(...), peso: float = Form(...)):
    return {"message": f"Agendamento de {fornecedor} recebido com sucesso!"}
