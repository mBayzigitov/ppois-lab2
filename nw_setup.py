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

def setup_qos(router):
    """ Set up Traffic Shaping and Policing on the router """
    
    # Set up HTB qdisc (traffic shaping)
    router.cmd("tc qdisc add dev r1-eth0 root handle 1: htb default 30")
    router.cmd("tc qdisc add dev r1-eth1 root handle 1: htb default 30")

    # Create classes for different types of traffic
    router.cmd("tc class add dev r1-eth0 parent 1: classid 1:1 htb rate 1000kbps ceil 1000kbps")
    router.cmd("tc class add dev r1-eth0 parent 1: classid 1:2 htb rate 512kbps ceil 512kbps")
    router.cmd("tc class add dev r1-eth0 parent 1: classid 1:3 htb rate 256kbps ceil 256kbps")
    
    # Apply policing on each class (traffic policing)
    router.cmd("tc qdisc add dev r1-eth0 parent 1:1 handle 10: police rate 1000kbps burst 10kb mpu 64k")
    router.cmd("tc qdisc add dev r1-eth0 parent 1:2 handle 20: police rate 512kbps burst 10kb mpu 64k")
    router.cmd("tc qdisc add dev r1-eth0 parent 1:3 handle 30: police rate 256kbps burst 10kb mpu 64k")

    # Filters for classifying traffic based on port numbers
    router.cmd("tc filter add dev r1-eth0 protocol ip prio 1 u32 match ip sport 5060 0xffff flowid 1:1")  # Voice traffic (SIP)
    router.cmd("tc filter add dev r1-eth0 protocol ip prio 1 u32 match ip sport 5004 0xffff flowid 1:1")  # Voice traffic (RTP)
    router.cmd("tc filter add dev r1-eth0 protocol ip prio 2 u32 match ip sport 554 0xffff flowid 1:2")   # Video traffic (RTSP)
    router.cmd("tc filter add dev r1-eth0 protocol ip prio 3 u32 match ip sport 80 0xffff flowid 1:3")    # Data traffic (HTTP)

    print(f"QoS policies applied to {router.name}-eth0")

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

    print("*** Setting up QoS (Traffic Shaping and Policing)")
    setup_qos(r1)

    print("*** Testing connectivity")
    net.pingAll()

    print("*** Starting CLI")
    CLI(net)

    print("*** Stopping network")
    net.stop()

if __name__ == "__main__":
    setLogLevel("info")
    setup_network()