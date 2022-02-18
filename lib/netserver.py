from concurrent.futures import thread
from msilib.schema import Error
import socket
import threading
import time
from lib.packets import PACKET_TYPE, packet, loads_packet, dumps_packet, packet_factory, Peer

RECV_SIZE = 1024
SOCKET_TIMEOUT = 0.5


class Connetion_Peer(Peer):
    sock : socket.socket = None
    recv_loop_ref : threading.Thread = None

class Peer_Server:
    def __init__(self,) -> None:
        self.clients: dict[int, Connetion_Peer] = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(SOCKET_TIMEOUT)

    def bind(self, hostname: str, port: int) -> None:
        self.sock.bind((hostname, port))

    def start_accept_loop(self, stop_event : threading.Event, event_passthrough: bool = True) -> None:
        self.accept_loop_ref = threading.Thread(
            target=self.accept_loop, args=(stop_event,event_passthrough,))
        self.accept_loop_ref.start()

    def accept_loop(self, stop_event: threading.Event, event_passthrough : bool = True) -> None:
        while not stop_event.is_set():
            r = None
            try:
                c = self.sock.accept()
            except Exception:
                continue
            print(f"New Connetion: {c[1]}")
            p = Connetion_Peer("", c[1][1], c[1])
            if p.id in self.clients:
                raise RuntimeError(f"Client with id: {p.id} already connected at {p.sock}")
            self.clients[p.id] = p
            p.sock = c[0]
            p.recv_loop_ref = self.start_recv_loop(p,stop_event if event_passthrough else threading.Event())

    def start_recv_loop(self, peer : Connetion_Peer, stop_event: threading.Event) -> threading.Thread:
        recv_loop_ref = threading.Thread(
            target=self.recv_loop, args=(peer,stop_event,))
        recv_loop_ref.stop_event = stop_event
        recv_loop_ref.start()
        return recv_loop_ref

    def recv_loop(self, peer : Connetion_Peer, stop_event: threading.Event):
        while not stop_event.is_set():
            r = None
            try:
                r = peer.sock.recv(RECV_SIZE).decode("utf-8")
            except TimeoutError:
                print("Timed out")
                continue
            except Exception as e:
                print(e)
                continue
            print(f"Recieved Packet: {r}")
            rs = loads_packet(r)
            self.handle_packet(rs, peer)

    def send_packet_to(self, packet: packet, peer: Connetion_Peer) -> None:
        js = dumps_packet(packet).encode("UTF-8")
        peer.sock.sendall(js)

    def packet_keep(self, packet: packet, peer: Connetion_Peer) -> None:
        packet.responded = True

    def packet_ping(self, packet: packet, peer: Connetion_Peer) -> None:
        packet.response["time"] = time.time()

    def packet_list(self, packet: packet, peer: Connetion_Peer) -> None:
        packet.response["peers"] = list(self.clients.values())

    def packet_file(self, packet: packet, peer: Connetion_Peer) -> None:
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

    def handle_packet(self, packet: packet, peer: Peer) -> None:
        f_name = f"packet_{packet.name.value.lower()}"
        if hasattr(self,f_name):
            getattr(self,f_name)(packet, peer)
            packet.responded = True
            self.send_packet_to(packet, peer)
        else:
            raise NameError(f"Function for packet: {packet.name} not found! {f_name=}")
