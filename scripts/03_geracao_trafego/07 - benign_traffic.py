
from scapy.all import IP, TCP, send, sr1, Raw
import time
import random

DST_IP = "10.45.0.1"
SRC_IP = "10.45.0.2"
DST_PORT = 80
SRC_PORT_BASE = 1024
FLOWS = 10

for i in range(FLOWS):
    sport = SRC_PORT_BASE + i
    seq = random.randint(1000, 9000)

    syn = IP(src=SRC_IP, dst=DST_IP)/TCP(sport=sport, dport=DST_PORT, flags="S", seq=seq)
    syn_ack = sr1(syn, timeout=1, verbose=0)

    if syn_ack and syn_ack.haslayer(TCP) and syn_ack[TCP].flags == "SA":
        ack = IP(src=SRC_IP, dst=DST_IP)/TCP(sport=sport, dport=DST_PORT, flags="A",
                                              seq=syn_ack.ack, ack=syn_ack.seq + 1)
        send(ack, verbose=0)

        get_pkt = IP(src=SRC_IP, dst=DST_IP)/TCP(sport=sport, dport=DST_PORT, flags="PA",
                                                  seq=syn_ack.ack, ack=syn_ack.seq + 1)/Raw(b"GET / HTTP/1.1\r\n\r\n")
        send(get_pkt, verbose=0)

    time.sleep(0.5)
