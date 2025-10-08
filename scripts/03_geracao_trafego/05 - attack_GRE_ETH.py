from scapy.all import IP, GRE, Ether, Raw, send
import time, random

src_ip = "10.45.0.10"
dst_ip = "10.45.0.1"

rate_pps = 8000
num_flows = 20
packets_per_flow = 200
inter_packet_delay = 1.0 / rate_pps
inter_flow_delay = 0.5

# Flags GRE (bitmask clássica)
GRE_CSUM = 0x8000  # checksum present
GRE_KEY  = 0x2000  # key present
# (não usamos SEQ para evitar incompatibilidade)

def pick_gre_flags_and_key():
    r = random.random()
    if r < 0.25:
        # 24 B (IP20 + GRE4)
        return 0x0000, None
    elif r < 0.50:
        # 28 B (IP20 + GRE8) -> KEY
        return GRE_KEY, random.getrandbits(32)
    else:
        # 32 B (IP20 + GRE12) -> KEY + CHECKSUM
        return GRE_KEY | GRE_CSUM, random.getrandbits(32)

# Ajuste para Min ≈ 528 no "Tot size"
# Tot ≈ IP(20) + GRE(4/8/12) + Ether(14) + payload
# Para garantir Min com GRE=4: 20+4+14+payload_min ≈ 528 → payload_min ≈ 490
BASE_INNER_PAYLOAD = 498   # base ~498
SIZE_JITTER = 8            # ±8 → mínimo ~490

def enviar_fluxo(_sport, _dport):
    for _ in range(packets_per_flow):
        flags, keyval = pick_gre_flags_and_key()

        inner_len = max(0, BASE_INNER_PAYLOAD + random.randint(-SIZE_JITTER, SIZE_JITTER))
        inner = Ether(dst="ff:ff:ff:ff:ff:ff", src="00:11:22:33:44:55") / Raw(bytes([random.randint(0,255) for _ in range(inner_len)]))

        gre = GRE(proto=0x6558, flags=flags)
        if flags & GRE_KEY:
            gre.key = keyval  # só define 'key' quando a flag K estiver setada

        pkt = IP(src=src_ip, dst=dst_ip, proto=47) / gre / inner
        send(pkt, verbose=0)
        time.sleep(inter_packet_delay)

print(f"Iniciando {num_flows} fluxos GRE-ETH (IP proto 47)...")
for i in range(num_flows):
    sport = random.randint(1024, 65535)  # só para log
    dport = random.randint(1024, 65535)
    print(f"[{i+1}/{num_flows}] Fluxo GRE-ETH: {src_ip} -> {dst_ip} (sport={sport}, dport={dport})")
    enviar_fluxo(sport, dport)
    time.sleep(inter_flow_delay)

print("✅ Simulação GRE-ETH concluída.")
