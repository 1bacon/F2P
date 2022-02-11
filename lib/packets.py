from collections import namedtuple
from dataclasses import dataclass, field
import enum, json, random
from typing import Any


i = 0
def next_int():
    global i;i = i+1
    return i-1

class PACKET_TYPE(enum.Enum):
    BASE = "BASE"
    KEEP = "KEEP"
    PING = "PING"
    LIST = "LIST"
    CHAT = "CHAT"

    def __eq__(self, __o: object) -> bool:
        return self.value == __o or ("value" in __o.__dir__() and __o.value == self.value)

@dataclass
class packet:
    name : PACKET_TYPE
    id : int = field(default_factory=next_int)
    params : dict = field(default_factory=dict)
    response : dict = field(default_factory=dict)
    responded : bool = False


class packet_factory:
    def new_base_packet():
        return packet(PACKET_TYPE.BASE)

    def new_list_packet():
        return packet(PACKET_TYPE.LIST)
    
    def new_chat_packet(_msg : str = ""):
        return packet(PACKET_TYPE.CHAT, params={"msg":_msg})

    def new_keep_packet():
        return packet(PACKET_TYPE.KEEP)

    def new_ping_packet(_time: float):
        return packet(PACKET_TYPE.PING, params={"time": _time})

class packet_encoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if type(o) == packet:
            return o.__dict__
        if type(o) == PACKET_TYPE:
            return o.value
        return super().default(o)

def packet_decoder(packet_dict : dict):
    if ("name" and "params" and "response") in packet_dict:
        return packet(**packet_dict)
    return packet_dict


def loads_packet(_json : str) -> packet:
    return json.loads(_json, object_hook=packet_decoder)

def dumps_packet(_packet : packet) -> str:
    return json.dumps(_packet, cls=packet_encoder)
