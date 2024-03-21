from peer_socket import PeerSocket
from client import Client
from tracker import Tracker
from torrent import Torrent
import sys


TRACKER_ADDRESS = "127.0.0.1"
# Do not change!
TRACKER_PORT = 35455


def run_tracker():
    tracker = Tracker(TRACKER_ADDRESS, TRACKER_PORT)
    tracker.start()


# Make sure at least one tracker is running before 
def run_leecher():
    torrent = Torrent().load_from_file("torrent_files\\example_torrent123.torrent")
    client = Client("127.0.0.1", 34225, torrent)

    #client.test_tracker_connection(torrent, TRACKER_ADDRESS, TRACKER_PORT)
    client.start_leeching(torrent, f"http://{TRACKER_ADDRESS}:{TRACKER_PORT}")


def run_seeder():
    torrent = Torrent().load_from_file("torrent_files\\TorA.torrent")
    client = Client("127.0.0.1", 34225, torrent)
    client.start_seeding(torrent)


def main():
    endpoint_type = input("Enter 0 for leecher, 1 for seeder, 2 for tracker: ")

    if endpoint_type == "0":
        run_leecher()
    elif endpoint_type == "1":
        run_seeder()
    elif endpoint_type == "2":
        run_tracker()
    else:
        print("Invalid option, exiting", file=sys.stderr)


if __name__ == "__main__":
    main()
