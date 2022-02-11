from enum import Enum, auto
from http.client import NotConnected
from netutils import Relay_Server
import cmd2

class shell(cmd2.Cmd):

    class error(Enum):
        NotConnected = auto()

    error_msg = {
        NotConnected: """Not connected to a Server yet.
        Please connect with 'connect <host> <port>'
        """
    }

    def __init__(self, _server : Relay_Server):
        self.server = _server

    def do_list(self):
        if not self.server.connected:
            return self.perror(self.error_msg[NotConnected])
        l = self.server.get_peers()
        
    