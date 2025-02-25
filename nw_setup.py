from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSKernelSwitch, Node
from mininet.cli import CLI
from mininet.log import setLogLevel

def setup_network():
    net = Mininet(controller=Controller, switch=OVSKernelSwitch)

    print("*** Creating nodes")
    r1 = net.addHost('r1', ip='10.0.1.1/24')
    r2 = net.addHost('r2', ip='10.0.2.1/24')

    h1 = net.addHost('h1', ip='10.0.1.10/24')
    h2 = net.addHost('h2', ip='10.0.1.11/24')
    h3 = net.addHost('h3', ip='10.0.2.10/24')
    server = net.addHost('server', ip='10.0.2.20/24')

    print("*** Creating switches")
    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')

    print("*** Creating links")
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(r1, s1)
    net.addLink(r1, r2)
    net.addLink(r2, s2)
    net.addLink(h3, s2)
    net.addLink(server, s2)

    print("*** Starting network")
    net.start()

    print("*** Configuring routers")
    r1.cmd('sysctl -w net.ipv4.ip_forward=1')
    r2.cmd('sysctl -w net.ipv4.ip_forward=1')

    print("*** Setting up IP routes")
    r1.cmd('ip addr add 10.0.1.1/24 dev r1-eth1')
    r1.cmd('ip addr add 192.168.1.1/30 dev r1-eth2')
    r2.cmd('ip addr add 192.168.1.2/30 dev r2-eth1')
    r2.cmd('ip addr add 10.0.2.1/24 dev r2-eth2')

    r1.cmd('ip route add 10.0.2.0/24 via 192.168.1.2 dev r1-eth2')
    r2.cmd('ip route add 10.0.1.0/24 via 192.168.1.1 dev r2-eth1')

    h1.cmd('ip route add default via 10.0.1.1')
    h2.cmd('ip route add default via 10.0.1.1')
    h3.cmd('ip route add default via 10.0.2.1')
    server.cmd('ip route add default via 10.0.2.1')

    print("*** Running CLI")
    CLI(net)

    print("*** Stopping network")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    setup_network()
