from threading import Event
import lib.netclient as cl

SERVER = ("localhost", 6969)


def main():
    server = cl.Server_Connection()

    server.connect(*SERVER)

    stop_event = Event()
    server.start_recv_loop(stop_event)

    while True:
        try:
            i = input("> ")
            exec(i)
        except Exception as e:
            print(e)



if __name__ == "__main__":
    main()