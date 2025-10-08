
import pandas as pd
import requests
import json
import sys
from datetime import datetime
from influxdb import InfluxDBClient

# --- CONFIGURAÇÕES GERAIS ---
FLASK_API_URL = "http://10.0.0.10:5000/analytics"
INFLUX_HOST = '10.0.0.10'
INFLUX_PORT = 8086
INFLUX_DB = 'mirai_flows'
INFLUX_MEASUREMENT = 'network_events'
BATCH_SIZE = 500

EXPECTED_COLUMNS_FOR_MODEL = [
    'Flow Duration', 'Header_Length', 'Time_To_Live',
    'ack_count', 'syn_count', 'urg_count', 'rst_count',
    'HTTP', 'UDP', 'Min', 'Covariance', 'Variance'
]

RENAME_COLUMNS = {
    'Flow Duration': 'flow_duration',
    'Header_Length': 'Header_Length',
    'Time_To_Live': 'Duration',
    'ack_count': 'ack_flag_number',
    'syn_count': 'syn_flag_number',
    'urg_count': 'urg_flag_number',
    'rst_count': 'rst_flag_number',
    'HTTP': 'HTTP',
    'UDP': 'UDP',
    'Min': 'Min',
    'Covariance': 'Covariance',
    'Variance': 'Variance'
}

def engineer_features(df):
    df.columns = df.columns.str.strip()
    missing_cols = [col for col in EXPECTED_COLUMNS_FOR_MODEL if col not in df.columns]
    if missing_cols:
        print(f"[ERRO] Colunas faltando no CSV: {missing_cols}")
        sys.exit(1)

    df = df[EXPECTED_COLUMNS_FOR_MODEL]
    df = df.rename(columns=RENAME_COLUMNS)
    return df

def classify_and_report_full(csv_filepath):
    df = pd.read_csv(csv_filepath, header=0, low_memory=False)
    df_engineered = engineer_features(df.copy())

    data_to_send = df_engineered.to_dict(orient='records')
    headers = {'Content-Type': 'application/json'}

    response = requests.post(FLASK_API_URL, headers=headers, data=json.dumps(data_to_send))
    api_results = response.json()
    predictions_rf = api_results.get('predictions_rf', [])
    predictions_lgbm = api_results.get('predictions_lgbm', [])

    df_engineered['prediction_rf'] = predictions_rf
    df_engineered['prediction_lgbm'] = predictions_lgbm

    # IPs e protocolo (se existirem no CSV original)
    if 'src_ip' in df.columns: df_engineered['source_ip'] = df['src_ip']
    if 'dst_ip' in df.columns: df_engineered['destination_ip'] = df['dst_ip']

    write_results_to_influxdb(df_engineered)


def write_results_to_influxdb(results_df):
    from numpy import inf
    import numpy as np

    results_df.replace(['snan', 'nan', 'NaN', 'None', ''], 0, inplace=True)
    results_df.replace([inf, -inf], 0, inplace=True)
    results_df.fillna(0, inplace=True)

    client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT, database=INFLUX_DB)
    points_to_write = []
    base_time = datetime.utcnow().timestamp()

    NUMERIC_KEYS = [
        'flow_duration', 'Header_Length', 'Duration',
        'ack_count', 'syn_count', 'urg_count', 'rst_count',
        'HTTP', 'UDP', 'Min', 'Covariance', 'Variance'
    ]

    for idx, row in results_df.iterrows():
        fields_data = {}
        for key in NUMERIC_KEYS:
            value = row.get(key, 0)
            try:
                fields_data[key] = float(value)
            except (ValueError, TypeError, SyntaxError):
                print(f"[WARN] Valor inválido para '{key}': {value}")
                fields_data[key] = 0

        json_point = {
            "measurement": INFLUX_MEASUREMENT,
            "tags": {
                "protocol": str(row.get('protocol', '')),
                "prediction_rf": str(row.get('prediction_rf', '')),
                "prediction_lgbm": str(row.get('prediction_lgbm', '')),
                "source_ip": str(row.get('source_ip', '')),
                "destination_ip": str(row.get('destination_ip', ''))
            },
            "fields": fields_data,
            "time": int((base_time + idx) * 1e9)
        }
        points_to_write.append(json_point)

    for i in range(0, len(points_to_write), BATCH_SIZE):
        batch = points_to_write[i:i+BATCH_SIZE]
        client.write_points(batch, time_precision='n')
        print(f"[INFO] Lote {i // BATCH_SIZE + 1} enviado com sucesso com {len(batch)} pontos.")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python3 sniffer_csv.py <caminho_para_o_csv>")
        sys.exit(1)

    csv_file = sys.argv[1]
    classify_and_report_full(csv_file)
