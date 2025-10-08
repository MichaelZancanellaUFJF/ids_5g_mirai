# -*- coding: utf-8 -*-
from scapy.all import IP, UDP, GRE, Raw, send
import random, time, threading

SRC_IP = "10.45.0.2"
DST_IP = "10.45.0.1"

# ------- Alvo do Min na janela -------
FORCE_MIN_TOTAL =  450 # ajuste aqui (paper ~509 p/ greip)

# GRE e Helper
TOTAL_FLOWS = 30
PKTS_PER_FLOW = (80, 160)
PPS_RANGE = (300, 800)

# UDP helper (para gerar flow_duration>0 no extrator padrão)
HELPER_UDP_FLOWS = 1           # 0 desativa; mantenha >=1 se quiser flow_duration>0
HELPER_PKTS_PER_FLOW = (500, 900)
HELPER_PPS_RANGE = (550, 900)

TTL_OUTER, TTL_INNER = 64, 55
rand_port = lambda: random.randint(1024, 65535)

def required_payload(min_total, overhead):
    return max(0, min_total - overhead)

def send_greip_flow():
    n = random.randint(*PKTS_PER_FLOW)
    pps = random.randint(*PPS_RANGE); inter = 1.0/pps
    sport, dport = rand_port(), rand_port()
    # Overhead GRE-IP sem opções: 66 bytes
    base_overhead = 66
    min_payload = required_payload(FORCE_MIN_TOTAL, base_overhead)
    for _ in range(n):
        # Pode variar um pouco acima do mínimo para dar naturalidade
        size = random.randint(min_payload, min_payload + 400)
        inner = IP(src=SRC_IP, dst=DST_IP, ttl=TTL_INNER)/UDP(sport=sport, dport=dport)/Raw(b'A'*size)
        pkt = IP(src=SRC_IP, dst=DST_IP, ttl=TTL_OUTER)/GRE(proto=0x0800)/inner
        send(pkt, verbose=0)
        time.sleep(inter * random.uniform(0.7, 1.3))

def send_udp_helper_flow():
    n = random.randint(*HELPER_PKTS_PER_FLOW)
    pps = random.randint(*HELPER_PPS_RANGE); inter = 1.0/pps
    sport, dport = rand_port(), rand_port()
    # Overhead UDP puro: 42 bytes -> payload precisa respeitar o mesmo Min
    base_overhead = 42
    min_payload = required_payload(FORCE_MIN_TOTAL, base_overhead)
    for _ in range(n):
        size = random.randint(min_payload, min_payload + 300)
        pkt = IP(src=SRC_IP, dst=DST_IP, ttl=TTL_OUTER)/UDP(sport=sport, dport=dport)/Raw(b'U'*size)
        send(pkt, verbose=0)
        time.sleep(inter * random.uniform(0.7, 1.3))

def main():
    print(f"[GRE-IP] FORCE_MIN_TOTAL={FORCE_MIN_TOTAL}B | flows={TOTAL_FLOWS} | udp_helper={HELPER_UDP_FLOWS}")
    th = [threading.Thread(target=send_greip_flow, daemon=True) for _ in range(TOTAL_FLOWS)]
    th += [threading.Thread(target=send_udp_helper_flow, daemon=True) for _ in range(HELPER_UDP_FLOWS)]
    random.shuffle(th)
    [t.start() for t in th]; [t.join() for t in th]
    print("✅ GRE-IP concluído.")

if __name__ == "__main__":
    main()
