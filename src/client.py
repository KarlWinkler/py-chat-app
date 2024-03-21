from threading import Thread
from peer_socket import PeerSocket
from torrent import Torrent
import random
import requests
import bencode
import sys
import time


# Time between tracker requests used if not specified by tracker
DEFAULT_TRACKER_INTERVAL = 3


class Client():
    def __init__(self, address: str, port: int):
        self.peer_socket = PeerSocket(address, port, Client.generate_peer_id())
        self.connected_peers = {str: PeerSocket}
        self.thread = None

    
    """ Retrieve list of peers from a tracker """
    def send_tracker_request(self, tracker_url: str, torrent: Torrent, event: str = "started", compact: int = 0):
        # Create request payload
        request_payload = {
            "info_hash": torrent.info_hash,
            "peer_id": self.peer_socket.peer_id,
            "port": self.peer_socket.port,
            "uploaded": 0,
            "downloaded": 0,
            "left": 1000, #TODO: how much of file left to download
            "event": event,
            "compact": compact
        }

        # Send GET request to tracker
        tracker_response = requests.get(tracker_url, request_payload, timeout=5)

        if tracker_response.status_code != 200:
            print(f"Failed to get peer list from tracker: {tracker_response.text}", file=sys.stderr)

        # Decode the response to retrieve the dictionary
        tracker_response = [tracker_response.status_code, bencode.decode(tracker_response.text)]

        return tracker_response


    """ 
    Generate Azureus-style 20-byte peer id
    '-', two chars for client id, '-', 4 digits for version number, followed by random numbers
    """
    @staticmethod
    def generate_peer_id():
        return '-FA0000-' + ''.join(random.choices('0123456789', k=12))


    def connect_to_peer(self, peer_info: str):
        # TODO: Create socket connection for interacting with this peer
        peer_socket = PeerSocket(
            peer_info["ip"],
            peer_info["port"],
            peer_info["peer id"]
        )
        peer_socket.request_connection()

        if peer_socket.connected:
            print("connected to: ", peer_socket["peer id"], peer_socket["ip"])
            self.connected_peers[peer_socket.peer_id] = peer_socket
            #peer_socket.send_handshake()


    def connect_to_new_peers(self, peer_list):
        for peer_info in peer_list:
            if not self.connected_peers.get(peer_info["peer id"]):
                self.connect_to_peer(peer_info)


    """Periodically send requests to all available trackers for a torrent until successful"""
    def handle_tracker_requests(self, torrent: Torrent, tracker_url: str):
        try:
            while self.running:
                # TODO: Support for multiple trackers at a time
                # for tracker_url in self.torrent.tracker_list["http"]:
                status_code, response = self.send_tracker_request(tracker_url, torrent)

                if status_code == 200:
                    self.connect_to_new_peers(response["peers"])
                    # time.sleep(response["interval"])
                    time.sleep(DEFAULT_TRACKER_INTERVAL)
                else:
                    # Default interval in case request was unsuccessful
                    time.sleep(DEFAULT_TRACKER_INTERVAL)

        except (SystemExit, KeyboardInterrupt):
            self.running = False


    def handle_seeding_requests(self):
        self.peer_socket.start_listening()

        while self.peer_socket.seeding:
            new_connection = self.peer_socket.accept_connection()
            if new_connection != None:
                pass


    def start_leeching(self, torrent: Torrent, tracker_url: str):
        self.running = True
        self.handle_tracker_requests(torrent, tracker_url) # TODO: Run on dedicated thread
        #self.thread = Thread(target = self.handle_tracker_requests, args=(torrent,tracker_url,))
        #self.thread.start()


    def start_seeding(self, torrent: Torrent, tracker_url: str):
        self.running = True
        self.thread = Thread(target = self.handle_tracker_requests, args=(torrent,tracker_url,))
        self.thread.start()
        self.handle_tracker_requests(torrent, tracker_url)


    def test_tracker_connection(self, torrent: Torrent, address: int, port: int):
        status_code, response = self.send_tracker_request(f"http://{address}:{port}", torrent)

        complete = response["complete"]
        incomplete = response["incomplete"]
        interval = response["interval"]
        peer_list = response["peers"]
        tracker_id = response["tracker id"]

        for peer_info in peer_list:
            print("PEER: ", peer_info["peer id"], peer_info["ip"], peer_info["port"])


    def stop(self):
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
                self.thread = None

