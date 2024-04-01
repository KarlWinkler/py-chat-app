from client import Client
from tracker import Tracker
from torrent import Torrent
import sys
import os

DEFAULT_TRACKER_ADDRESS = "127.0.0.1"
DEFAULT_TRACKER_PORT = 35333

# Torrent that will be used in the demo
# Bee movie torrent has trackers urls ["http://127.0.0.1:35222", "http://127.0.0.1:35333"]
DEMO_TORRENT_PATH = "torrent_samples\\bees_local_trackers.torrent"
# Folder where downloaded files are stored
SAVE_PATH = os.path.join(os.environ['USERPROFILE'], 'Documents', 'FA BitTorrent Save Files')


def test_read_bitfield():
    pass


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
    torrent = Torrent.load_metainfo_from_file(DEMO_TORRENT_PATH)
    torrent.load_pieces(SAVE_PATH)

    client = Client("127.0.0.1", 32225, SAVE_PATH)
    client.start_downloading(torrent)
    #self.test_tracker_connection(client, torrent.info_hash, f"http://127.0.0.1:35222")


def run_seeder():
    torrent = Torrent.load_metainfo_from_file(DEMO_TORRENT_PATH)
    torrent.load_pieces(SAVE_PATH)

    client = Client("127.0.0.1", 34445, SAVE_PATH)
    client.start_seeding(torrent)


def main():
    endpoint_type = input("Enter 0 for leecher, 1 for seeder, 2 for tracker: ")

    if endpoint_type == "0":
        run_downloader()
    elif endpoint_type == "1":
        run_seeder()
    elif endpoint_type == "2":
        try:
            address = input(f"Enter IP address (default={DEFAULT_TRACKER_ADDRESS}): ") or DEFAULT_TRACKER_ADDRESS
            port = input(f"Enter port (default={DEFAULT_TRACKER_PORT}): ") or DEFAULT_TRACKER_PORT
            port = int(port)
        except ValueError:
            print("Invalid option, exiting", file=sys.stderr)
            sys.exit(1)

        run_tracker(address, port)
    else:
        print("Invalid option, exiting", file=sys.stderr)


if __name__ == "__main__":
    main()
