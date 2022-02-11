import socket
import threading
import time
from lib.netclient import Peer
from lib.packets import PACKET_TYPE, packet, loads_packet, dumps_packet, packet_factory

RECV_SIZE = 1024

class Peer_Server:
    def __init__(self,) -> None:
        self.clients : dict[int, Peer] = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def bind(self, hostname : str, port : int) -> None:
        self.sock.bind((hostname, port))

    def start_recv_loop(self, stop_event: threading.Event) -> None:
        self.recv_loop_ref = threading.Thread(
            target=self.recv_loop, args=(stop_event,))
        self.recv_loop_ref.start()

    def recv_loop(self, stop_event: threading.Event):
        while not stop_event.is_set():
            r = self.sock.recv(RECV_SIZE).decode("utf-8")
            rs = loads_packet(r)
            self.handle_packet(rs)

    def send_packet_to(self, packet : packet, peer: Peer) -> None:
        js = dumps_packet(packet)
        self.sock.sendto(js, peer.socket)

    def packet_keep(self, packet : packet, peer : Peer) -> None:
        packet.responded = True
    def packet_ping(self, packet : packet, peer : Peer) -> None:
        packet.response["time"] = time.time()
    def packet_list(self, packet : packet, peer : Peer) -> None:
        packet.response["peers"] = list(self.clients.values())
    def packet_file(self, packet : packet, peer : Peer) -> None:
        if "peer_id" not in packet.params:
            raise RuntimeError(f"FILE packet without 'peer_id', p={packet}")
        if "name" not in packet.params:
            raise RuntimeError(f"FILE packet without 'name', p={packet}")
        if "size" not in packet.params:
            raise RuntimeError(f"FILE packet without 'size', p={packet}")

        id = packet.params["peer_id"]
        if id not in self.clients:
            packet.response["sent"] = False
            return
        c = self.clients[id]
        packet.server_side = True
        packet.params["from"] = peer

        self.send_packet_to(packet, peer)

        packet.server_side = False
        packet.response["sent"] = True
        self.send_packet_to(packet, peer)


    def handle_packet(self, packet : packet, peer : Peer) -> None:
        f_name = f"packet_{packet.name.value.lower()}"
        if f_name in globals():
            locals()[f_name](packet, peer)
            self.send_response(packet, peer)
        else:
            raise NameError(f"Function for packet: {packet.name} not found!")