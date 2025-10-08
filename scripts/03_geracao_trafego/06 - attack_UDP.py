from scapy.all import IP, UDP, Raw, send
import random, time, math

# --------- CENÁRIO ----------
SRC_IP = "10.45.0.2"
DST_IP = "10.45.0.1"
TTL    = 64

# --------- ALVOS ----------
TARGET_HEADER_LEN     = 1_441_552      # ~1.441.552
HEADER_BYTES_PER_PKT  = 28             # use 42 se o extrator contar Ethernet (IP+UDP+ETH)
FLOW_DURATION_TARGET  = 2.155          # ~2.155 s como na sua classe
MEAN_TOTAL_BYTES      = 700            # média por pacote (dados + header vistos pelo extrator)
STD_TOTAL_BYTES       = 30             # baixa variância
MIN_TOTAL_BYTES       = 512            # forçar Min ≈ 512
PCT_MIN_PACKETS       = 0.05           # ~5% dos pacotes com o mínimo
JITTER_IAT            = 0.10           # ±10% de jitter

# --------- DERIVADOS ----------
# nº de pacotes para somar ~TARGET_HEADER_LEN
PACKETS_PER_FLOW = max(2, round(TARGET_HEADER_LEN / HEADER_BYTES_PER_PKT))
IAT = FLOW_DURATION_TARGET / (PACKETS_PER_FLOW - 1)

def clamp(v, lo, hi):
    return hi if v > hi else lo if v < lo else v

def gen_total_size(i):
    """Gera tamanho total 'visto pelo extrator' (header + payload)"""
    # ~5% dos pacotes batem no mínimo para consolidar "Min"
    if i < int(PCT_MIN_PACKETS * PACKETS_PER_FLOW):
        return MIN_TOTAL_BYTES
    s = random.gauss(MEAN_TOTAL_BYTES, STD_TOTAL_BYTES)
    return int(clamp(s, MIN_TOTAL_BYTES, MEAN_TOTAL_BYTES + 6*STD_TOTAL_BYTES))

def send_udp_flow():
    sport = 54321  # fixos para manter 1 fluxo (não variar portas)
    dport = 54321
    # Obs.: payload_len = total - header_per_pkt (alinhado ao que seu extrator conta)
    for i in range(PACKETS_PER_FLOW):
        total = gen_total_size(i)
        payload_len = max(0, total - HEADER_BYTES_PER_PKT)
        pkt = IP(src=SRC_IP, dst=DST_IP, ttl=TTL)/UDP(sport=sport, dport=dport)/Raw(b'U' * payload_len)
        send(pkt, verbose=0)
        # IAT pequeno -> cuidado com resolução do sleep; ajuste se necessário
        time.sleep(IAT * random.uniform(1.0 - JITTER_IAT, 1.0 + JITTER_IAT))

def main():
    expected_hlen = PACKETS_PER_FLOW * HEADER_BYTES_PER_PKT
    rate = (PACKETS_PER_FLOW - 1) / max(1e-9, FLOW_DURATION_TARGET)
    print(f"[UDP Plain] pkts≈{PACKETS_PER_FLOW} | header/pkt={HEADER_BYTES_PER_PKT} "
          f"| Header_Length≈{expected_hlen} | IAT≈{IAT:.6f}s | rate≈{rate:.1f} pps")
    send_udp_flow()
    print("✅ Concluído.")

if __name__ == "__main__":
    main()
