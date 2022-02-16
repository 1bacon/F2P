import socket
import threading
import time
from dataclasses import dataclass

from lib.packets import (PACKET_TYPE, dumps_packet, loads_packet, packet,
                     packet_factory, Peer)

RECV_SIZE = 1024
PACKET_TIMEOUT = 10


class Server_Connection():

    def __init__(self, ) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = None
        self.connected = False
        self.recv_loop_ref = None
        self.pending_packet_dict: dict[int,
                                       tuple[packet, float, threading.Event]] = {}

    def connect(self, host: str, port: int) -> None:
        self.host = (host, port)
        self.sock.connect(self.host)
        self.connected = True

    def start_recv_loop(self, stop_event: threading.Event) -> None:
        self.recv_loop_ref = threading.Thread(
            target=self.recv_loop, args=(stop_event,))
        self.recv_loop_ref.start()

    def recv_loop(self, stop_event: threading.Event):
        while not stop_event.is_set():
            r = self.sock.recv(RECV_SIZE).decode("utf-8")
            rs = loads_packet(r)
            self.handle_packet(rs)

    def handle_packet(self, packet: packet) -> None:
        if packet.server_side:
            # Only FILE should be serveside
            if not packet.name == PACKET_TYPE.FILE:
                raise RuntimeError(
                    f"Recieved server-side packet other than FILE. p={packet}")
            return self.server_side_file(packet)
        if not packet.responded:
            raise RuntimeError(
                f"Recieved packet without responded Flag. p={packet}")
        if packet.id not in self.pending_packet_dict:
            raise RuntimeError(
                f"Recieved packet while no packet is pending on id:{packet.id}, p={packet}")

        self.pending_packet_dict[packet.id][0].responded = True
        self.pending_packet_dict[packet.id][0].response = packet.response
        self.pending_packet_dict[packet.id][2].set()
        self.pending_packet_dict.pop(packet.id)

    def send_packet(self, packet: packet) -> packet:
        evt = threading.Event()
        text = dumps_packet(packet)  # Packet to json
        # Save packet to write response when it comes back
        self.pending_packet_dict[packet.id] = (packet, time.time(), evt)
        self.sock.send(bytes(text, encoding="utf-8"))  # Send packet
        if evt.wait(timeout=PACKET_TIMEOUT):  # Not timed out
            if not packet.responded:
                raise RuntimeError(
                    f"Packet: {packet} marked as responded but has no response.")
            return packet
        else:  # Timed out
            raise TimeoutError(
                f"Packet: {packet} did not get answered in {PACKET_TIMEOUT} seconds.")

    def server_side_file(self, packet: packet) -> None:
        t = f"{packet.params['peer_id']} offered file: '{packet.params['name']}', size: {packet.params['size']}"
        print(t)

    def keep_alive(self, ) -> None:
        p = packet_factory.new_keep_packet()
        p = self.send_packet(p)

    def get_ping(self, ) -> float:
        p = packet_factory.new_ping_packet(time.time())
        p = self.send_packet(p)
        return time.time() - p.params["time"]

    def get_peers(self,) -> list[Peer]:
        p = packet_factory.new_list_packet()
        p = self.send_packet(p)
        if "peers" in p.response:
            return p.response["peers"]
        else:
            raise RuntimeError("Da hell")

    def offer_file(self, file_name: str, file_size: int, peer_id: int) -> bool:
        p = packet_factory.new_file_packet(file_name, file_size, peer_id)
        p = self.send_packet(p)
        if "sent" in p.response:
            return p.response["sent"]
