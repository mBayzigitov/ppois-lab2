from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Controller, OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink

class QoSTopo(Topo):
    def build(self):
        # Создаём маршрутизаторы
        r1 = self.addSwitch('s1')
        r2 = self.addSwitch('s2')

        # Добавляем хосты (клиенты)
        h1 = self.addHost('h1', ip='192.168.1.1/24')
        h2 = self.addHost('h2', ip='192.168.1.2/24')
        h3 = self.addHost('h3', ip='192.168.1.3/24')

        # Добавляем сервер
        server = self.addHost('server', ip='192.168.2.1/24')

        # Соединяем маршрутизаторы
        self.addLink(r1, r2, bw=10)  # Пропускная способность 10 Мбит/с

        # Подключаем хосты к r1
        self.addLink(h1, r1, bw=1)  # 1 Мбит/с
        self.addLink(h2, r1, bw=1)
        self.addLink(h3, r1, bw=1)

        # Подключаем сервер к r2
        self.addLink(server, r2, bw=10)  # 10 Мбит/с


# Запуск Mininet с топологией
if __name__ == '__main__':
    topo = QoSTopo()
    net = Mininet(topo=topo, controller=Controller, switch=OVSKernelSwitch, link=TCLink)
    net.start()

    print("Сеть запущена. Проверяем соединения:")
    net.pingAll()

    CLI(net)  # Открываем CLI Mininet
    net.stop()