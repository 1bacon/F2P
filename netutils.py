import socket
from struct import pack
import packets
from dataclasses import dataclass


@dataclass
class Peer():
    name: str
    id: int
    socket: tuple[str, int]


class Relay_Server():

    def __init__(self, ) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = None
        self.connected = False

    def connect(self, host: str, port: int) -> None:
        self.host = (host, port)
        self.sock.connect(self.host)
        self.connected = True

    def send_packet(self, packet : packets.packet) -> None:
        ...

    def get_peers(self ,) -> list[Peer]:
        self.sock.send("list")
