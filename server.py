from threading import Event
import lib.netserver as ns


PORT = 6969

def main():
    server = ns.Peer_Server()
    server.bind("0.0.0.0", PORT)
    server.sock.listen(5)
    stop = Event()
    server.start_accept_loop(stop)

    while True:
        try:
            i = input("> ")
            exec(i)
        except Exception as e:
            print(e)



if __name__ == "__main__":
    main()

