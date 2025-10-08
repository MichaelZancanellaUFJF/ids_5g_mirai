#!/bin/bash

# Script orquestrador que roda em loop para captura e análise contínua.

# --- CONFIGURAÇÕES ---
# Interface de rede do UPF
INTERFACE="ogstun" 
# Duração da captura em segundos
CAPTURE_DURATION=30
# Caminho para o diretório das capturas
CAPTURE_DIR="./pcap_origin"

# Garante que os diretórios existam
mkdir -p $CAPTURE_DIR

echo "--- Orquestrador de Detecção Iniciado ---"
echo "Capturando tráfego em ciclos de $CAPTURE_DURATION segundos."

# Loop infinito
while true; do
    # Define um nome de arquivo único com base na data e hora
    FILENAME="capture_$(date +%Y-%m-%d_%H-%M-%S).pcap"
    CAPTURE_PATH="$CAPTURE_DIR/$FILENAME"
    
    echo -e "\n[$(date)] Iniciando nova captura: $FILENAME"
    
    # 1. Capturar tráfego por um período determinado
    sudo timeout "$CAPTURE_DURATION" tcpdump -i "$INTERFACE" -w "$CAPTURE_PATH"

    
    # Verifica se o arquivo de captura foi criado e tem tamanho maior que zero
    if [ -s "$CAPTURE_PATH" ]; then
        echo "[$(date)] Captura concluída."
    else
        echo "[$(date)] Nenhuma atividade de rede capturada neste ciclo."
        rm $CAPTURE_PATH # Remove o arquivo pcap vazio
    fi
    
    echo "[$(date)] Ciclo concluído. Aguardando o próximo..."
done
