# Insira esta string base64 logo acima da função get_form()
LOGO_BASE64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


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
            .card {{ 
                background: #ffffff; 
                border-radius: 12px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.3); 
                width: 100%; 
                max-width: 520px; 
                overflow: hidden;
            }}
            .header-banner {{
                width: 100%;
                background-color: #031027;
                border-bottom: 4px solid #ffc107;
                padding: 10px 0;
            }}
            .header-banner img {{
                width: 100%;
                max-height: 140px;
                display: block;
                object-fit: contain;
            }}
            .info-box {{
                background-color: #fff9e6;
                border-left: 5px solid #ffc107;
                padding: 15px 20px;
                margin: 20px 30px 0 30px;
                border-radius: 6px;
            }}
            .info-box-title {{ font-weight: 700; color: #0b192c; font-size: 14px; margin-bottom: 6px; }}
            .info-box-text {{ font-size: 12px; color: #444; line-height: 1.5; margin-bottom: 8px; }}
            .info-box-time {{ font-weight: 700; color: #b78103; background: #fff0c2; padding: 4px 8px; border-radius: 4px; display: inline-block; margin-bottom: 8px; font-size: 12px; }}
            .info-box-alert {{ font-weight: 700; color: #0b192c; background: #ffe89c; padding: 6px 10px; border-radius: 4px; display: block; margin-bottom: 12px; font-size: 12px; }}
            .btn-manual {{ display: inline-block; width: 100%; text-align: center; background-color: #0b192c; color: #ffc107; padding: 10px; border-radius: 6px; font-size: 13px; font-weight: 700; text-decoration: none; }}
            .form-body {{ padding: 20px 30px 25px 30px; }}
            .form-group {{ margin-bottom: 18px; }}
            label {{ display: block; margin-bottom: 6px; font-weight: 600; color: #2b2b2b; font-size: 13px; }}
            input, select {{ width: 100%; padding: 12px 14px; border: 1.5px solid #dcdfe6; border-radius: 6px; font-size: 14px; font-family: inherit; }}
            input:focus, select:focus {{ outline: none; border-color: #0b192c; }}
            .uppercase-input {{ text-transform: uppercase; }}
            button.btn-submit {{ 
                width: 100%; padding: 14px; background: linear-gradient(90deg, #ffc107 0%, #e0a800 100%); 
                color: #0b192c; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; 
                font-weight: 700; text-transform: uppercase; margin-top: 10px; box-shadow: 0 4px 12px rgba(255, 193, 7, 0.3);
            }}
            .message {{ margin-top: 20px; padding: 15px; border-radius: 6px; display: none; text-align: center; font-size: 14px; line-height: 1.5; }}
            .success {{ background-color: #e6f4ea; color: #137333; border: 1px solid #ceead6; }}
            .error {{ background-color: #fce8e6; color: #c5221f; border: 1px solid #fad2cf; }}
            .code-highlight {{ font-size: 22px; font-weight: 700; background: #ffffff; padding: 6px 14px; border-radius: 6px; display: inline-block; margin-top: 8px; border: 2px dashed #137333; color: #137333; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header-banner">
                <img src="https://i.postimg.cc/3x2Fv4Fw/Design-sem-nome.png" alt="Diniz Alimentos" onerror="this.onerror=null; this.src='{LOGO_BASE64}';">
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
            function generateRandomCode() {{
                const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
                let code = '';
                for (let i = 0; i < 6; i++) {{
                    code += chars.charAt(Math.floor(Math.random() * chars.length));
                }}
                return code;
            }}

            function toggleContactInput() {{
                const contactType = document.getElementById('preferredContact').value;
                document.getElementById('phoneGroup').style.display = contactType === 'whatsapp' ? 'block' : 'none';
                document.getElementById('emailGroup').style.display = contactType === 'email' ? 'block' : 'none';
                document.getElementById('phone').required = contactType === 'whatsapp';
                document.getElementById('email').required = contactType === 'email';
            }}

            function toggleQuantityInput() {{
                const cargoType = document.getElementById('cargoType').value;
                document.getElementById('qtyLabel').innerText = cargoType === 'Batida' ? 'QUANTIDADE DE VOLUMES:' : 'QUANTIDADE DE PALETES:';
            }}

            document.getElementById('scheduleForm').addEventListener('submit', async (e) => {{
                e.preventDefault();
                const msgDiv = document.getElementById('responseMsg');
                msgDiv.style.display = 'none';

                const randomCode = generateRandomCode();
                const preferred = document.getElementById('preferredContact').value;
                let cleanPhone = document.getElementById('phone').value.replace(/\D/g, '');
                if (cleanPhone.length >= 10 && !cleanPhone.startsWith('55')) {{
                    cleanPhone = '55' + cleanPhone;
                }}

                const payload = {{
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
                }};

                try {{
                    const res = await fetch('/api/schedule', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(payload)
                    }});
                    const data = await res.json();
                    
                    if (res.ok) {{
                        msgDiv.className = 'message success';
                        msgDiv.innerHTML = `Solicitação enviada!<br><strong>Status: Pendente</strong><br>Sua pré-senha:<br><span class="code-highlight">${{randomCode}}</span>`;
                        document.getElementById('scheduleForm').reset();
                    }} else {{
                        msgDiv.className = 'message error';
                        msgDiv.innerText = data.detail || 'Erro ao agendar.';
                    }}
                }} catch (err) {{
                    msgDiv.className = 'message error';
                    msgDiv.innerText = 'Erro na conexão.';
                }}
                msgDiv.style.display = 'block';
            }});
        </script>
    </body>
    </html>
    """
