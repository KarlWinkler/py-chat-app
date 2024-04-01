from client import Client
from tracker import Tracker
from torrent import Torrent
import sys


def test_tracker_connection(client: Client, info_hash: str, tracker_url: str):
    status_code, response = Tracker.send_tracker_request(client.client_peer.address, client.client_peer.port, tracker_url, info_hash)

    if status_code == 200:
        complete = response["complete"]
        incomplete = response["incomplete"]
        interval = response["interval"]
        peer_list = response["peers"]
        tracker_id = response["tracker id"]

        for peer_info in peer_list:
            print("PEER: ", peer_info["peer id"], peer_info["ip"], peer_info["port"])
    else:
        print(f"Failed to connect to tracker: {response["failure reason"]}")


def run_tracker(address: str, port: int):
    tracker = Tracker(address, port)
    tracker.start()


# Make sure at least one tracker is running before 
def run_downloader():
    torrent = Torrent().load_from_file("torrent_samples\\localhost_tracker_demo.torrent")
    client = Client("127.0.0.1", 32225)
    client.start_downloading(torrent)
    #self.test_tracker_connection(client, torrent.info_hash, f"http://127.0.0.1:35222")


def run_seeder():
    torrent = Torrent().load_from_file("torrent_samples\\localhost_tracker_demo.torrent")
    client = Client("127.0.0.1", 34445)
    client.start_seeding(torrent)


def main():
    endpoint_type = input("Enter 0 for leecher, 1 for seeder, 2 for tracker: ")

    if endpoint_type == "0":
        run_downloader()
    elif endpoint_type == "1":
        run_seeder()
    elif endpoint_type == "2":
        try:
            address = input("Enter IP address (default=127.0.0.1): ") or "127.0.0.1"
            port = input("Enter port (default=35333): ") or 35333
            port = int(port)
        except ValueError:
            print("Invalid option, exiting", file=sys.stderr)
            sys.exit(1)

        run_tracker(address, port)
    else:
        print("Invalid option, exiting", file=sys.stderr)


if __name__ == "__main__":
    main()
