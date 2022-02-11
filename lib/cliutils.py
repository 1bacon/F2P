from enum import Enum, auto
from netutils import Relay_Server
import cmd2

class shell(cmd2.Cmd):

    class error(Enum):
        NotConnected = """Not connected to a Server yet.
        Please connect with 'connect <host> <port>'"""

    def __init__(self, _server : Relay_Server):
        self.server = _server

    def do_list(self):
        if not self.server.connected:
            return self.perror(shell.error.NotConnected.value)
        l = self.server.get_peers()
        
    