from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSSwitch, Node
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel

def configure_routing(router, routes):
    """ Configure routing table for a router """
    for route, via in routes.items():
        router.cmd(f'ip route add {route} via {via}')

def enable_ip_forwarding(router):
    """ Enable IP forwarding for routers """
    router.cmd("sysctl -w net.ipv4.ip_forward=1")

def configure_qos(router, name):
    router.cmd(f'tc qdisc add dev {name} root handle 1: htb default 30')
    router.cmd(f'tc class add dev {name} parent 1: classid 1:1 htb rate 100mbit')
    router.cmd(f'tc class add dev {name} parent 1:1 classid 1:10 htb rate 50mbit ceil 100mbit')  # Голосовой трафик
    router.cmd(f'tc class add dev {name} parent 1:1 classid 1:20 htb rate 30mbit ceil 80mbit')   # Видеотрафик
    router.cmd(f'tc class add dev {name} parent 1:1 classid 1:30 htb rate 20mbit ceil 50mbit')   # Данные

    router.cmd(f'tc filter add dev {name} protocol ip parent 1:0 prio 1 u32 match ip dport 5060 0xffff flowid 1:10')  # Голосовой
    router.cmd(f'tc filter add dev {name} protocol ip parent 1:0 prio 2 u32 match ip dport 554 0xffff flowid 1:20')   # Видео
    router.cmd(f'tc filter add dev {name} protocol ip parent 1:0 prio 3 u32 match ip protocol 6 0xff flowid 1:30')    # Данные (TCP)

def start_iperf_server(server):
    """
    Запуск iperf сервера на хосте server.
    """
    print(f"*** Starting iperf server on {server.name}")
    server.cmd('iperf -s -p 5060 &')  # Сервер для голосового трафика
    server.cmd('iperf -s -p 554 &')   # Сервер для видеотрафика
    server.cmd('iperf -s -p 80 &')    # Сервер для данных

def generate_traffic(net):
    """
    Генерация трафика с использованием iperf.
    """
    print("*** Generating traffic")

    # Голосовой трафик (UDP, низкая полоса пропускания)
    h1 = net.get('h1')
    h1.cmd('iperf -u -c 10.0.2.3 -p 5060 -b 1M -t 60 &')  # Голосовой трафик

    # Видеотрафик (UDP, высокая полоса пропускания)
    h2 = net.get('h2')
    h2.cmd('iperf -u -c 10.0.2.3 -p 554 -b 10M -t 60 &')  # Видеотрафика

    # Данные (TCP, случайная нагрузка)
    h3 = net.get('h3')
    h3.cmd('iperf -c 10.0.2.3 -p 80 -b 100M -t 60 &')  # Данные

    print("*** Traffic generation started")

def setup_network():
    net = Mininet(controller=Controller, link=TCLink)

    print("*** Adding controller")
    net.addController("c0")

    print("*** Creating nodes")
    h1 = net.addHost("h1", ip="10.0.1.2/24")
    h2 = net.addHost("h2", ip="10.0.1.3/24")
    h3 = net.addHost("h3", ip="10.0.2.2/24")
    server = net.addHost("server", ip="10.0.2.3/24")

    r1 = net.addHost("r1")  # Router 1
    r2 = net.addHost("r2")  # Router 2

    print("*** Creating switches")
    s1 = net.addSwitch("s1")
    s2 = net.addSwitch("s2")

    print("*** Creating links")
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(s1, r1)  # r1-eth1 connects to s1

    net.addLink(r1, r2)  # r1-eth2 <-> r2-eth1 (direct router link)

    net.addLink(r2, s2)  # r2-eth2 connects to s2
    net.addLink(h3, s2)
    net.addLink(server, s2)

    print("*** Starting network")
    net.start()

    print("*** Configuring IP addresses")
    # Router 1 interfaces
    r1.cmd("ifconfig r1-eth0 10.0.1.1/24 up")   # LAN side (to h1, h2 via s1)
    r1.cmd("ifconfig r1-eth1 192.168.1.1/30 up")  # Link to Router 2

    # Router 2 interfaces
    r2.cmd("ifconfig r2-eth0 192.168.1.2/30 up")  # Link to Router 1
    r2.cmd("ifconfig r2-eth1 10.0.2.1/24 up")   # LAN side (to h3, server via s2)

    print("*** Enabling IP forwarding")
    enable_ip_forwarding(r1)
    enable_ip_forwarding(r2)

    print("*** Configuring static routing")
    configure_routing(r1, {"10.0.2.0/24": "192.168.1.2"})  # Route to h3, server via r2
    configure_routing(r2, {"10.0.1.0/24": "192.168.1.1"})  # Route to h1, h2 via r1

    print("*** Setting default gateways for hosts")
    h1.cmd("ip route add default via 10.0.1.1")
    h2.cmd("ip route add default via 10.0.1.1")
    h3.cmd("ip route add default via 10.0.2.1")
    server.cmd("ip route add default via 10.0.2.1")

    print("*** Configuring QoS policies")
    configure_qos(r1,"r1-eth0")  # Настройка QoS на r1
    configure_qos(r1,"r1-eth1")  # Настройка QoS на r1
    configure_qos(r2, "r2-eth0")  # Настройка QoS на r2
    configure_qos(r2, "r2-eth1")  # Настройка QoS на r2

    print("*** Starting iperf server on server")
    start_iperf_server(net.get('server'))  # Запуск iperf сервера

    print("*** Testing connectivity")
    net.pingAll()

    print("*** Generating traffic")
    generate_traffic(net)  # Генерация трафика

    print("*** Starting CLI")
    CLI(net)

    print("*** Stopping network")
    net.stop()

if __name__ == "__main__":
    setLogLevel("info")
    setup_network()