__author__ = "Yuval Malkan"


import scapy.all as scapy

from scapy.all import sniff, IP, IPv6, TCP, UDP, ICMP, ARP, DNSQR
from datetime import datetime






def packet_callback(packet):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

    src_ip = ""
    dst_ip = ""
    protocol = ""
    length = len(packet)
    info = ""

    #Parse Data Link / Network Layer (IP/ARP)
    if packet.haslayer(IP):
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
    elif packet.haslayer(IPv6):
        src_ip = packet[IPv6].src
        dst_ip = packet[IPv6].dst
    elif packet.haslayer(ARP):
        src_ip = packet[ARP].psrc
        dst_ip = packet[ARP].pdst
        protocol = "ARP"
        if packet[ARP].op == 1:  #arp request
            info = f"Who has {dst_ip}? Tell {src_ip}"
        elif packet[ARP].op == 2:  # arp reply
            info = f"{src_ip} is at {packet[ARP].hwsrc}"
    else:
        #Fallback for non IP traffic
        src_ip = packet.src if hasattr(packet, 'src') else "Unknown"
        dst_ip = packet.dst if hasattr(packet, 'dst') else "Unknown"
        protocol = "ETH"
        info = packet.summary()

    #parse transport /application layer
    if packet.haslayer(TCP):
        protocol = "TCP"
        src_port = packet[TCP].sport
        dst_port = packet[TCP].dport
        flags = packet[TCP].flags
        info = f"{src_port} -> {dst_port} [{flags}] Seq={packet[TCP].seq} Ack={packet[TCP].ack}"

    elif packet.haslayer(UDP):
        protocol = "UDP"
        src_port = packet[UDP].sport
        dst_port = packet[UDP].dport
        info = f"{src_port} -> {dst_port}"

        # identify dns queries within udp
        if packet.haslayer(DNSQR):
            protocol = "DNS"
            query = packet[DNSQR].qname.decode('utf-8', errors='ignore')
            info = f"Standard query {query}"

    elif packet.haslayer(ICMP):
        protocol = "ICMP"
        info = f"Type={packet[ICMP].type} Code={packet[ICMP].code}"

    elif not protocol:
        #catch all for ip packets without recognized transport layers
        protocol = f"IP"
        info = packet.summary()

    #print
    print(f"{timestamp:<12} | {src_ip:<16} | {dst_ip:<16} | {protocol:<6} | {length:<5} | {info}")






if __name__ == "__main__":
    print(f"{'Time':<12} | {'Source':<16} | {'Destination':<16} | {'Proto':<6} | {'Len':<5} | {'Info'}")
    print("-" * 100)

    packet_callback(sniff(prn=packet_callback))

