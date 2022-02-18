import enum
import json
import socket
from dataclasses import dataclass, field
from multiprocessing import connection
import threading
from typing import Any

i = 0


def next_int():
    global i
    i = (i + 1) % 1024
    return i - 1


@dataclass
class Peer():
    name: str
    id: int
    connection: tuple[str, int]


class PACKET_TYPE(enum.Enum):
    BASE = "BASE"
    KEEP = "KEEP"
    PING = "PING"
    LIST = "LIST"
    FILE = "FILE"

    def __eq__(self, __o: object) -> bool:
        return self.value == __o or (
            "value" in __o.__dir__() and __o.value == self.value)


@dataclass
class packet:
    name: PACKET_TYPE
    id: int = field(default_factory=next_int)
    params: dict = field(default_factory=dict)
    response: dict = field(default_factory=dict)
    responded: bool = False
    server_side: bool = False


class packet_factory:
    def new_base_packet():
        return packet(PACKET_TYPE.BASE)

    def new_list_packet():
        return packet(PACKET_TYPE.LIST)

    def new_keep_packet():
        return packet(PACKET_TYPE.KEEP)

    def new_ping_packet(_time: float):
        return packet(PACKET_TYPE.PING, params={"time": _time})

    def new_file_packet(_name: str, _size: int, _peer_id: int):
        return packet(
            PACKET_TYPE.FILE,
            params={
                "name": _name,
                "size": _size,
                "peer_id": _peer_id})


class packet_encoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, packet):
            return o.__dict__
        if isinstance(o, PACKET_TYPE):
            return o.value
        if isinstance(o, Peer):
            return o.__dict__
        if isinstance(o, socket.socket):
            return None
        if isinstance(o, threading.Thread):
            return None
        return super().default(o)


def packet_decoder(packet_dict: dict):
    if ("name" and "params" and "response") in packet_dict:
        packet_dict["name"] = PACKET_TYPE._value2member_map_[
            packet_dict["name"]]
        return packet(**packet_dict)
    return packet_dict


def loads_packet(_json: str) -> packet:
    return json.loads(_json, object_hook=packet_decoder)


def dumps_packet(_packet: packet) -> str:
    return json.dumps(_packet, cls=packet_encoder)
