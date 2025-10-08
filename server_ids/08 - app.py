from flask import Flask, request, jsonify
import pandas as pd
import pickle
import os
import json
from datetime import datetime

app = Flask(__name__)

# Carregar modelos treinados
import os
assert os.path.exists("../models/rf_model.pkl"), "Arquivo rf_model.pkl não encontrado"
assert os.path.exists("../models/lgbm_model.pkl"), "Arquivo lgbm_model.pkl não encontrado"
print("📦 Tentando carregar modelos...")
rf_model = pickle.load(open("../models/rf_model.pkl", "rb"))
lgbm_model = pickle.load(open("../models/lgbm_model.pkl", "rb"))
print("✅ Modelos carregados com sucesso")
print("Colunas esperadas pelo modelo RF:")
print(rf_model.feature_names_in_)
print("Colunas esperadas pelo modelo LGBMF:")
print(lgbm_model.feature_names_in_)

# Conversor seguro para JSON
def to_serializable(obj):
    if hasattr(obj, "item"):
        return obj.item()
    return obj

# Endpoint para receber e armazenar tráfego (simulando NWDAF/ADRF)
@app.route("/data-report", methods=["POST"])
def data_report():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido ou vazio"}), 400

    timestamp = datetime.now().isoformat()
    os.makedirs("storage", exist_ok=True)
    with open(f"storage/traffic_{timestamp}.json", "w") as f:
        json.dump(data, f, indent=2)

    return jsonify({"status": "received", "timestamp": timestamp})

# Endpoint de inferência com os modelos RF e LGBM
@app.route("/analytics", methods=["POST"])
def analytics():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "JSON inválido ou vazio"}), 400

    try:
        print("📥 Dados recebidos:", json_data)
        
        # Cria o DataFrame a partir da lista de dicionários recebida
        df = pd.DataFrame(json_data)

        # --- BLOCO DE LIMPEZA E VALIDAÇÃO ADICIONADO ---
        # Este bloco garante que o script não quebre com dados malformados (como o cabeçalho do CSV)

        # 1. Garante que uma coluna chave seja numérica, transformando texto (cabeçalho) em NaN
        #    Usaremos 'Flow Duration' como a coluna chave para validar as linhas.
        if 'Flow Duration' in df.columns:
            df['Flow Duration'] = pd.to_numeric(df['Flow Duration'], errors='coerce')
            # 2. Remove a linha inteira se a coluna chave for NaN (isso remove a linha do cabeçalho)
            df.dropna(subset=['Flow Duration'], inplace=True)

        # 3. Garante que todas as colunas de features sejam numéricas e preenche erros com 0
        #    Usaremos a lista de features que o próprio modelo carregado espera
        for col in rf_model.feature_names_in_:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                # Se uma coluna esperada não veio, criamos com zeros para evitar erro
                df[col] = 0 
        
        # 4. Verifica se, após a limpeza, ainda existem dados para processar
        if df.empty:
            return jsonify({"error": "Nenhum dado válido para predição após a limpeza", "predictions": []})
        # --- FIM DO BLOCO DE LIMPEZA ---

        # Agora, garantimos que o DataFrame tenha as colunas na ordem exata que o modelo espera
        features_for_model = df[rf_model.feature_names_in_]
        
        print("🧠 Colunas usadas na predição:", features_for_model.columns.tolist())

        # Faz a predição para todos os fluxos recebidos de uma vez
        rf_preds = rf_model.predict(features_for_model)
        lgbm_preds = lgbm_model.predict(features_for_model)

        # Mapear valores numéricos para strings
        label_map = {
            0: "BENIGN",
            1: "Mirai-greip_flood",
            2: "Mirai-greeth_flood",
            3: "Mirai-udpplain"
        }

        # Cria uma lista de resultados para retornar
        # O cliente que chama a API espera uma lista de predições, uma para cada fluxo enviado
        results = {
            "predictions_rf": [label_map.get(int(p), str(p)) for p in rf_preds],
            "predictions_lgbm": [label_map.get(int(p), str(p)) for p in lgbm_preds]
        }

        return jsonify(results)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erro na inferência: {str(e)}"}), 500

# Healthcheck do NWDAF
@app.route("/health")
def health():
    return jsonify({"status": "nw-daf running"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


print("🚀 Servidor Flask iniciado com sucesso")
