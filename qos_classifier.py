from scapy.all import sniff
from collections import Counter

# Define port ranges for classification
VOICE_PORTS = {5060, 5004, 5005, 5006, 5007}  # SIP, RTP
VIDEO_PORTS = {554, 1935}  # RTSP, RTP
DATA_PORTS = {80, 443, 21, 22, 25, 110, 143}  # HTTP, HTTPS, FTP, SSH, SMTP, IMAP

# Traffic counter
traffic_stats = Counter()

def classify_packet(packet):
    """Classifies a packet based on its port number."""
    if packet.haslayer('TCP') or packet.haslayer('UDP'):
        sport = packet.sport
        dport = packet.dport
        
        if sport in VOICE_PORTS or dport in VOICE_PORTS:
            traffic_stats["Voice"] += 1
            priority = "HIGH"
        elif sport in VIDEO_PORTS or dport in VIDEO_PORTS:
            traffic_stats["Video"] += 1
            priority = "MEDIUM"
        elif sport in DATA_PORTS or dport in DATA_PORTS:
            traffic_stats["Data"] += 1
            priority = "LOW"
        else:
            traffic_stats["Unknown"] += 1
            priority = "LOW"

        print(f"Packet: Src Port {sport}, Dst Port {dport} → Classified as {priority} Priority")

def start_sniffing(interface="eth0", packet_count=100):
    """Starts sniffing packets on a given network interface."""
    print(f"Starting packet capture on {interface}...")
    sniff(iface=interface, prn=classify_packet, count=packet_count)

    print("\nTraffic Summary:")
    for category, count in traffic_stats.items():
        print(f"{category}: {count} packets")

# Run packet sniffer
if __name__ == "__main__":
    start_sniffing(interface="eth0", packet_count=100)
