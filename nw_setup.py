from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink

def configure_qos(host):
    host.cmd('tc qdisc add dev ' + host.defaultIntf().name + ' root handle 1: htb default 30')
    host.cmd('tc class add dev ' + host.defaultIntf().name + ' parent 1: classid 1:1 htb rate 100mbit')
    host.cmd('tc class add dev ' + host.defaultIntf().name + ' parent 1:1 classid 1:10 htb rate 50mbit ceil 100mbit')  # Голосовой трафик
    host.cmd('tc class add dev ' + host.defaultIntf().name + ' parent 1:1 classid 1:20 htb rate 30mbit ceil 80mbit')   # Видеотрафик
    host.cmd('tc class add dev ' + host.defaultIntf().name + ' parent 1:1 classid 1:30 htb rate 20mbit ceil 50mbit')   # Данные

    host.cmd('tc filter add dev ' + host.defaultIntf().name + ' protocol ip parent 1:0 prio 1 u32 match ip dport 5060 0xffff flowid 1:10')  # Голосовой
    host.cmd('tc filter add dev ' + host.defaultIntf().name + ' protocol ip parent 1:0 prio 2 u32 match ip dport 554 0xffff flowid 1:20')   # Видео
    host.cmd('tc filter add dev ' + host.defaultIntf().name + ' protocol ip parent 1:0 prio 3 u32 match ip protocol 6 0xff flowid 1:30')    # Данные (TCP)

def create_network():
    net = Mininet(controller=RemoteController, switch=OVSKernelSwitch, link=TCLink)

    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)

    h1 = net.addHost('h1', ip='10.0.0.1/24')
    h2 = net.addHost('h2', ip='10.0.0.2/24')
    h3 = net.addHost('h3', ip='10.0.0.3/24')
    server = net.addHost('server', ip='10.0.1.1/24')
    r1 = net.addHost('r1', ip='10.0.0.254/24')
    r2 = net.addHost('r2', ip='10.0.1.254/24')

    net.addLink(h1, r1)
    net.addLink(h2, r1)
    net.addLink(h3, r1)
    net.addLink(r1, r2)
    net.addLink(r2, server)

    net.start()

    h1.cmd('ip route add default via 10.0.0.254')
    h2.cmd('ip route add default via 10.0.0.254')
    h3.cmd('ip route add default via 10.0.0.254')
    server.cmd('ip route add default via 10.0.1.254')

    configure_qos(r1)
    configure_qos(r2)

    CLI(net)

    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    create_network()