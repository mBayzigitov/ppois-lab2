import ipaddress
from time import sleep

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import Node
from mininet.cli import CLI
from mininet.log import setLogLevel, info


class LinuxRouter(Node):
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()

class NetworkTopo(Topo):
    def build(self, **_opts):
        r1 = self.addNode('r1', cls=LinuxRouter, ip='10.0.1.1/24')
        r2 = self.addNode('r2', cls=LinuxRouter, ip='10.0.2.1/24')

        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        self.addLink(
            s1,
            r1,
            intfName2='r1-eth1',
            params2={'ip': '10.0.1.1/24'}
        )

        self.addLink(
            s2,
            r2,
            intfName2='r2-eth1',
            params2={'ip': '10.0.2.1/24'}
        )

        self.addLink(
            r1,
            r2,
            intfName1='r1-eth2',
            intfName2='r2-eth2',
            params1={'ip': '10.100.0.1/24'},
            params2={'ip': '10.100.0.2/24'}
        )
        
        h1 = self.addHost('h1', ip='10.0.1.101/24', defaultRoute='via 10.0.1.1')
        h2 = self.addHost('h2', ip='10.0.1.102/24', defaultRoute='via 10.0.1.1')
        h3 = self.addHost('h3', ip='10.0.1.103/24', defaultRoute='via 10.0.1.1')
        
        server = self.addHost('server', ip='10.0.2.101/24', defaultRoute='via 10.0.2.1')
        
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s1)
        self.addLink(server, s2)

def configure_routes(net):
    r1, r2 = net.get('r1', 'r2')
    info(r1.cmd("ip route add 10.0.2.0/24 via 10.100.0.2 dev r1-eth2"))
    info(r2.cmd("ip route add 10.0.1.0/24 via 10.100.0.1 dev r2-eth2"))
    
    
def configure_qos(net):
    r1, r2 = net.get('r1', 'r2')
    
    for router, iface in [(r1, 'r1-eth2'), (r2, 'r2-eth2')]:
        router.cmd(f'tc qdisc del dev {iface} root') #Удаляет существующую корневую очередь пакетов (qdisc)
        router.cmd(f'tc qdisc add dev {iface} root handle 1: htb default 30') #Добавляет новую очередь пакетов (Hierarchical Token Bucket)
        
        router.cmd(f'tc class add dev {iface} parent 1: classid 1:1 htb rate 10mbit') #Ограничение скорости до 10mbit
        
        router.cmd(f'tc class add dev {iface} parent 1:1 classid 1:10 htb rate 2mbit ceil 4mbit prio 1') #2mbit гарант, приоритет выс
        router.cmd(f'tc class add dev {iface} parent 1:1 classid 1:20 htb rate 4mbit ceil 6mbit prio 2') #4mbit гарант, приоритет сред
        router.cmd(f'tc class add dev {iface} parent 1:1 classid 1:30 htb rate 1mbit ceil 10mbit prio 3') #1mbit гарант, приоритет низ
        
        #u32 match ip tos 184 0xff: Сопоставляет пакеты с TOS 184 (маска 0xff проверяет все 8 бит). flowid 1:10: Направляет пакеты в класс 1:10.
        router.cmd(f'tc filter add dev {iface} protocol ip parent 1:0 prio 1 u32 match ip tos 184 0xff flowid 1:10')
        router.cmd(f'tc filter add dev {iface} protocol ip parent 1:0 prio 2 u32 match ip tos 160 0xff flowid 1:20')
        router.cmd(f'tc filter add dev {iface} protocol ip parent 1:0 prio 3 u32 match ip tos 0 0xff flowid 1:30')     
        
        #Ограничивает скорость до 4 Мбит/с с буфером 20 Кбайт, отбрасывая превышающие пакеты.
        router.cmd(f'tc filter add dev {iface} protocol ip parent 1:0 prio 1 u32 match ip tos 184 0xff police rate 4mbit burst 20k drop')
        router.cmd(f'tc filter add dev {iface} protocol ip parent 1:0 prio 2 u32 match ip tos 160 0xff police rate 6mbit burst 40k drop')


def servers_start(net):
    server = net.get('server')

    server.cmd('iperf -s -p 6001 -u &')
    server.cmd('iperf -s -p 6002 -u &')
    server.cmd('iperf -s -p 6003 &')


# def traffic_generate(net):
#     info("Генерация трафика\n")
#     h1, h2, h3 = net.get('h1', 'h2', 'h3')

#     h1.cmd('iperf -c server -u -p 6001 -b 3M -t 4 -S 0xB8 &')
#     h2.cmd('iperf -c server -u -p 6002 -b 9M -t 4 -S 0xA0 &')
#     h3.cmd('iperf -c server -p 6003 -t 4 &')


if __name__ == '__main__':
    setLogLevel('info')
    
    topo = NetworkTopo()
    net = Mininet(topo=topo)
    
    net.start()
    
    configure_routes(net)
    configure_qos(net)
    r1 = net.get('r1')
    
    r1.cmd('python3 classifier.py r1-eth2 > classifier.log 2>&1 &')

    servers_start(net)
    # traffic_generate(net)    
    
    CLI(net)

    net.stop()

#disable qos
#r1 tc qdisc del dev r1-eth2 root
#r2 tc qdisc del dev r2-eth2 root

#traffic generate
#h1 iperf -c server -u -p 6001 -b 128K -t 120 -S 0xB8 &
#h2 iperf -c server -u -p 6002 -b 6M -t 120 -S 0xA0 &
#h3 iperf -c server -p 6003 -b 100M -t 180 -S 0 &

#iperf server start
#server iperf -s -p 6001 -u &
#server iperf -s -p 6002 -u &
#server iperf -s -p 6003 &