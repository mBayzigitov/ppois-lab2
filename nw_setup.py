from mininet.topo import Topo

class MyTopo(Topo):
    def __init__(self):
        Topo.__init__(self)

        # Добавляем два маршрутизатора
        r1 = self.addHost('r1')
        r2 = self.addHost('r2')

        # Добавляем три хоста (клиента)
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')

        # Добавляем сервер
        server = self.addHost('server')

        # Соединяем устройства
        self.addLink(h1, r1)
        self.addLink(h2, r1)
        self.addLink(h3, r1)
        self.addLink(r1, r2)
        self.addLink(r2, server)

topos = {'mytopo': (lambda: MyTopo())}