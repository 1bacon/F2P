import socket, time, threading
from struct import pack
from packets import packet_factory, packet, dumps_packet, loads_packet
from dataclasses import dataclass

PACKET_TIMEOUT = 10

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
        self.pending_packet_dict : dict [int, tuple[packet, float, threading.Event]]= {}

    def connect(self, host: str, port: int) -> None:
        self.host = (host, port)
        self.sock.connect(self.host)
        self.connected = True

    def handle_packet(self, packet : packet) -> None:
        if packet.responded == False:
            raise RuntimeError(f"Recieved packet without responded Flag. p={packet}")
        if packet.id not in self.pending_packet_dict:
            raise RuntimeError(f"Recieved packet while no packet is pending on id:{packet.id}, p={packet}")

        self.pending_packet_dict[packet.id][0].responded = True
        self.pending_packet_dict[packet.id][0].response = packet.response
        self.pending_packet_dict[packet.id][2].set()
        self.pending_packet_dict.pop(packet.id)

    def send_packet(self, packet : packet) -> packet:
        evt = threading.Event()
        text = dumps_packet(packet)                     #Packet to json
        self.sock.send(bytes(text, encoding="utf-8"))   #Send packet
        self.pending_packet_dict[packet.id] = (packet, time.time(), evt)    #Save packet to write response when it comes back
        if evt.wait(timeout=PACKET_TIMEOUT):            #Not timed out
            if not packet.responded:
                raise RuntimeError(f"Packet: {packet} marked as responded but has no response.")
            return packet
        else:                                           #Timed out
            raise TimeoutError(f"Packet: {packet} did not get answered in {PACKET_TIMEOUT} seconds.")


    def get_peers(self ,) -> list[Peer]:
        p = packet_factory.new_list_packet()
        p = self.send_packet(p)
        if "peers" in p.response:
            return p.response["peers"]
        else:
            raise RuntimeError("Da hell")