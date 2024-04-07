from client import Client
from tracker import Tracker
from torrent import Torrent
from dotenv import load_dotenv
import sys
import os

load_dotenv()

DEFAULT_TRACKER_ADDRESS = os.getenv("DEFAULT_TRACKER_ADDRESS", "127.0.0.1")
DEFAULT_TRACKER_PORT = os.getenv("DEFAULT_TRACKER_PORT", 35222)

DEFAULT_ADDRESS = os.getenv("ADDRESS", "127.0.0.1")
DEFAULT_PORT = os.getenv("PORT", 34324)

# Torrent that will be used in the demo
# Bee movie torrent has trackers urls ["http://127.0.0.1:35222", "http://127.0.0.1:35333"]
DEMO_TORRENT_PATH = os.getenv("DEMO_TORRENT_PATH", os.path.join(os.getenv('USERPROFILE', os.path.expanduser("~")), 'Documents', 'bee_movie.torrent'))

# Folder where downloaded files are stored
SAVE_PATH = os.getenv("SAVE_PATH", os.path.join(os.getenv('USERPROFILE', os.path.expanduser("~")), 'Downloads'))


def test_read_bitfield():
    pass


def test_tracker_connection(client: Client, info_hash: str, tracker_url: str):
    status_code, response = Tracker.send_tracker_request(client.client_peer.address, client.client_peer.port, client.client_peer.address, tracker_url, info_hash)

    if status_code == 200:
        complete = response["complete"]
        incomplete = response["incomplete"]
        interval = response["interval"]
        peer_list = response["peers"]
        tracker_id = response["tracker id"]

        for peer_info in peer_list:
            print("PEER: ", peer_info["peer id"], peer_info["ip"], peer_info["port"])
    else:
        print(f"Failed to connect to tracker: {response['failure reason']}")


def run_tracker(address: str, port: int):
    tracker = Tracker(address, port)
    tracker.start()


# Make sure at least one tracker is running before 
def run_downloader(address, port):
    torrent = Torrent.load_metainfo_from_file(DEMO_TORRENT_PATH)
    torrent.load_pieces(SAVE_PATH)
    for piece in torrent.pieces:
        print(piece.index)
    #torrent.write_piece(SAVE_PATH, torrent.pieces[2], "bee_move2.txt")

    client = Client(address, port, SAVE_PATH)
    client.start_downloading(torrent)
    #self.test_tracker_connection(client, torrent.info_hash, f"http://127.0.0.1:35222")


def run_seeder(address, port):
    torrent = Torrent.load_metainfo_from_file(DEMO_TORRENT_PATH)
    torrent.load_pieces(SAVE_PATH)

    client = Client(address, port, SAVE_PATH)
    client.start_seeding(torrent)


def main():
    endpoint_type = input("Enter 0 for leecher, 1 for seeder, 2 for tracker: ")

    if endpoint_type == "0" or endpoint_type == "1":
        address = input(f"Enter IP address (default={DEFAULT_ADDRESS}): ") or DEFAULT_ADDRESS
        port = int(input(f"Enter port (default={DEFAULT_PORT}): ") or DEFAULT_PORT)
        if endpoint_type == "0":
            run_downloader(address, port)
        elif endpoint_type == "1":
            run_seeder(address, port)
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
