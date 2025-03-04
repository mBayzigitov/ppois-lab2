from mininet.net import Mininet
from mininet.node import Controller
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel
import threading
import time

def generate_traffic(host, server):
    """ Generate different types of traffic """
    print(f"Generating traffic from {host.name} to {server.name}")

    # Simulate Voice traffic (SIP/RTP)
    threading.Thread(target=lambda: host.cmd(f"iperf -c {server.IP()} -u -b 512k -t 60 -p 5060 &"), daemon=True).start()

    # Simulate Video traffic (RTSP/RTP)
    threading.Thread(target=lambda: host.cmd(f"iperf -c {server.IP()} -u -b 1000k -t 60 -p 554 &"), daemon=True).start()

    # Simulate Audio Streaming (HTTP streaming)
    threading.Thread(target=lambda: host.cmd(f"iperf -c {server.IP()} -u -b 256k -t 60 -p 80 &"), daemon=True).start()


def setup_network():
    net = Mininet(controller=Controller, link=TCLink)
    net.addController("c0")

    print("*** Creating nodes")
    h1 = net.addHost("h1", ip="10.0.1.2/24")
    h2 = net.addHost("h2", ip="10.0.1.3/24")
    server = net.addHost("server", ip="10.0.2.3/24")

    print("*** Creating switches")
    s1 = net.addSwitch("s1")
    s2 = net.addSwitch("s2")

    print("*** Creating links")
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(s1, s2)
    net.addLink(server, s2)

    print("*** Starting network")
    net.start()

    print("*** Configuring routing")
    h1.cmd("ip route add default via 10.0.1.1")
    h2.cmd("ip route add default via 10.0.1.1")
    server.cmd("ip route add default via 10.0.2.1")

    print("*** Generating traffic")
    generate_traffic(h1, server)
    generate_traffic(h2, server)

    time.sleep(5)  # Let the traffic generation run for a while
    CLI(net)

    print("*** Stopping network")
    net.stop()

if __name__ == "__main__":
    setLogLevel("info")
    setup_network()
