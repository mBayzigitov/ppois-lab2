from mininet.net import Mininet
from mininet.node import Controller, Node
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel
from time import sleep

def configure_routing(router, routes):
    for route, via in routes.items():
        router.cmd(f'ip route add {route} via {via}')


def enable_ip_forwarding(router):
    router.cmd("sysctl -w net.ipv4.ip_forward=1")

def setup_qos(router):
    for iface in ['r1-eth0', 'r1-eth1']:
        router.cmd(f"tc qdisc add dev {iface} root handle 1: htb default 30")
        router.cmd(f"tc class add dev {iface} parent 1: classid 1:1 htb rate 1000kbps ceil 1000kbps")
        router.cmd(f"tc class add dev {iface} parent 1: classid 1:2 htb rate 512kbps ceil 512kbps")
        router.cmd(f"tc class add dev {iface} parent 1: classid 1:3 htb rate 256kbps ceil 256kbps")

        router.cmd(f"tc qdisc add dev {iface} parent 1:1 handle 10: police rate 1000kbps burst 10kb mpu 64k")
        router.cmd(f"tc qdisc add dev {iface} parent 1:2 handle 20: police rate 512kbps burst 10kb mpu 64k")
        router.cmd(f"tc qdisc add dev {iface} parent 1:3 handle 30: police rate 256kbps burst 10kb mpu 64k")

        router.cmd(f"tc filter add dev {iface} protocol ip prio 1 u32 match ip sport 5060 0xffff flowid 1:1")
        router.cmd(f"tc filter add dev {iface} protocol ip prio 2 u32 match ip sport 554 0xffff flowid 1:2")
        router.cmd(f"tc filter add dev {iface} protocol ip prio 3 u32 match ip sport 80 0xffff flowid 1:3")
    print(f"QoS policies applied to {router.name}")


def generate_traffic(h1, h2, h3, server):
    print("*** Generating traffic")
    server.cmd("iperf -s -u -p 5060 &")  # Voice traffic
    server.cmd("iperf -s -u -p 554 &")  # Video traffic
    server.cmd("iperf -s -u -p 80 &")  # HTTP traffic
    sleep(1)
    h1.cmd("iperf -c 10.0.2.3 -u -p 5060 -b 800k &")  # Voice
    h2.cmd("iperf -c 10.0.2.3 -u -p 554 -b 400k &")  # Video
    h3.cmd("iperf -c 10.0.2.3 -u -p 80 -b 200k &")  # HTTP


def setup_network():
    net = Mininet(controller=Controller, link=TCLink)
    net.addController("c0")

    h1 = net.addHost("h1", ip="10.0.1.2/24")
    h2 = net.addHost("h2", ip="10.0.1.3/24")
    h3 = net.addHost("h3", ip="10.0.2.2/24")
    server = net.addHost("server", ip="10.0.2.3/24")

    r1 = net.addHost("r1")
    r2 = net.addHost("r2")

    s1 = net.addSwitch("s1")
    s2 = net.addSwitch("s2")

    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(s1, r1)
    net.addLink(r1, r2)
    net.addLink(r2, s2)
    net.addLink(h3, s2)
    net.addLink(server, s2)

    net.start()

    r1.cmd("ifconfig r1-eth0 10.0.1.1/24 up")
    r1.cmd("ifconfig r1-eth1 192.168.1.1/30 up")
    r2.cmd("ifconfig r2-eth0 192.168.1.2/30 up")
    r2.cmd("ifconfig r2-eth1 10.0.2.1/24 up")

    enable_ip_forwarding(r1)
    enable_ip_forwarding(r2)

    configure_routing(r1, {"10.0.2.0/24": "192.168.1.2"})
    configure_routing(r2, {"10.0.1.0/24": "192.168.1.1"})

    h1.cmd("ip route add default via 10.0.1.1")
    h2.cmd("ip route add default via 10.0.1.1")
    h3.cmd("ip route add default via 10.0.2.1")
    server.cmd("ip route add default via 10.0.2.1")

    setup_qos(r1)
    setup_qos(r2)

    net.pingAll()

    generate_traffic(h1, h2, h3, server)

    CLI(net)
    net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    setup_network()
