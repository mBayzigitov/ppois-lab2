import sys
import ipaddress

from scapy.all import sniff, IP, UDP, TCP

def classify_and_mark(packet):
    if not packet.haslayer(IP):
        return
    ip_layer = packet[IP]

    try:
        if ipaddress.IPv4Address(ip_layer.dst).is_multicast:
            return
    except Exception:
        return

    traffic_type = "data"
    if packet.haslayer(UDP):
        if ip_layer.tos == 184:
            traffic_type = "voice"
        elif ip_layer.tos == 160:
            traffic_type = "video"
    elif packet.haslayer(TCP):
        traffic_type = "data"
        
    print(f"Packer {ip_layer.src} -> {ip_layer.dst}: Type - {traffic_type}, TOS - {ip_layer.tos}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(1)

    interface = sys.argv[1]
    print(f"Classificator is running on the interface {interface}")
    sniff(iface=interface, prn=classify_and_mark, store=0)