from threading import Thread, Lock
from peer_socket import PeerSocket
from torrent import Torrent
import random
import requests
import bencode
import sys
import time
import select


# Time between tracker requests used if not specified by tracker
DEFAULT_TRACKER_INTERVAL = 9


class Client():
    def __init__(self, address: str, port: int):
        self.peer_socket = PeerSocket(address, port, Client.generate_peer_id())
        self.connected_peers = {str: PeerSocket}
        self.thread = None
        self.running = False


    """
    Generate Azureus-style 20-byte peer id
    '-', two chars for client id, '-', 4 digits for version number, followed by random numbers
    """
    @staticmethod
    def generate_peer_id():
        return '-FA0000-' + ''.join(random.choices('0123456789', k=12))


    """ Retrieve list of peers from a tracker """
    def send_tracker_request(self, tracker_url: str, info_hash: str, event: str = "started", compact: int = 0):
        # Create request payload
        request_payload = {
            "info_hash": info_hash,
            "peer_id": self.peer_socket.peer_id,
            "port": self.peer_socket.port,
            "uploaded": 0,
            "downloaded": 0,
            "left": 1000, #TODO: How much of file is left to download
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


    def try_connect_to_peer(self, peer_info: dict):
        if self.connected_peers.get(peer_info["peer id"]): return

        # TODO: Create socket connection for interacting with this peer
        peer_socket = PeerSocket(
            peer_info["ip"],
            peer_info["port"],
            peer_info["peer id"]
        )
        print("requesting")
        connected = peer_socket.request_connection()

        if connected:
            print("connected to: ", peer_socket.peer_id, peer_socket.address)
            self.connected_peers[peer_socket.peer_id] = peer_socket
            #peer_socket.send_handshake()


    """Periodically send requests to all available trackers for a torrent until successful"""
    def handle_tracker_requests(self, torrent: Torrent, tracker_url: str, send_connection_requests: bool):
        try:
            while self.running:
                # TODO: Support for multiple trackers at a time
                # for tracker_url in self.torrent.tracker_list["http"]:
                status_code, response = self.send_tracker_request(tracker_url, torrent.info_hash)

                if status_code == 200:
                    if send_connection_requests:
                        for peer_info in response["peers"]:
                            print("PEER:", peer_info)
                            self.try_connect_to_peer(peer_info)
                    # time.sleep(response["interval"])
                    time.sleep(DEFAULT_TRACKER_INTERVAL)
                else:
                    # Default interval in case request was unsuccessful
                    time.sleep(DEFAULT_TRACKER_INTERVAL)
        except (SystemExit, KeyboardInterrupt):
            self.stop()


    def start_tracker_requests(self, torrent: Torrent, tracker_url: str, send_connection_requests: bool):
        self.running = True
        self.thread = Thread(target = self.handle_tracker_requests, args=(torrent,tracker_url,send_connection_requests,))
        self.thread.daemon = True
        self.thread.start()


    def start_leeching(self, torrent: Torrent, tracker_url: str):
        self.start_tracker_requests(torrent, tracker_url, True)

        try:
            while self.running:
                time.sleep(DEFAULT_TRACKER_INTERVAL)

        except (SystemExit, KeyboardInterrupt):
            self.stop()


    def start_seeding(self, torrent: Torrent, tracker_url: str):
        self.start_tracker_requests(torrent, tracker_url, False)
        self.peer_socket.start_listening()
        socket_list = [self.peer_socket.socket]

        try:
            while self.running:
                readable, _, exceptional = select.select(socket_list, [], socket_list, 1)

                for sock in readable:
                    if sock == self.peer_socket.socket:
                        peer_socket = self.peer_socket.accept_connection()
                        if peer_socket:
                            print("accepted:",peer_socket)
                            socket_list.append(peer_socket)
                    else:
                        pass
                
            for sock in exceptional:
                socket_list.remove(sock)

        except (SystemExit, KeyboardInterrupt):
            self.stop()


    def stop(self):
        self.running = False


    def __del__(self):
        self.stop()
