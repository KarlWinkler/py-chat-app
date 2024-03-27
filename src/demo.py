from client import Client
from tracker import Tracker
from torrent import Torrent
import sys


TRACKER_ADDRESS = "127.0.0.1"
# Do not change!
TRACKER_PORT = 35455


def test_tracker_connection(self, client: Client, info_hash: str):
    status_code, response = client.send_tracker_request(f"http://{TRACKER_ADDRESS}:{TRACKER_PORT}", info_hash)
    complete = response["complete"]
    incomplete = response["incomplete"]
    interval = response["interval"]
    peer_list = response["peers"]
    tracker_id = response["tracker id"]

    if status_code == 200:
        for peer_info in peer_list:
            print("PEER: ", peer_info["peer id"], peer_info["ip"], peer_info["port"])


def run_tracker():
    tracker = Tracker(TRACKER_ADDRESS, TRACKER_PORT)
    tracker.start()


# Make sure at least one tracker is running before 
def run_leecher():
    torrent = Torrent().load_from_file("torrent_files\\example_torrent123.torrent")
    client = Client("127.0.0.1", 32225)
    client.start_downloading(torrent, f"http://{TRACKER_ADDRESS}:{TRACKER_PORT}")


def run_seeder():
    torrent = Torrent().load_from_file("torrent_files\\example_torrent123.torrent")
    client = Client("127.0.0.1", 34445)
    client.start_seeding(torrent, f"http://{TRACKER_ADDRESS}:{TRACKER_PORT}")


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
