from threading import Thread, Lock
from peer import Peer
from torrent import Torrent
from message import Handshake
import random
import requests
import bencode
import sys
import time
import select
import socket


# Time between tracker requests used if not specified by tracker
DEFAULT_TRACKER_INTERVAL = 9


class Client():
    def __init__(self, address: str, port: int):
        self.client_peer = Peer(address, port, Client.generate_peer_id(), False)
        self.connected_peers: dict[str, Peer] = {}
        self.thread = None
        self.running = False
        self.seeding = False
        self.peer_list = []
        #self.peer_list_lock = Lock()


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
            "peer_id": self.client_peer.peer_id,
            "port": self.client_peer.port,
            "uploaded": 0,
            "downloaded": 0,
            "left": 1000, #TODO: How much of file is left to download
            "event": event,
            "compact": compact
        }

        # Send GET request to tracker
        tracker_response = requests.get(tracker_url, request_payload, timeout=5)
        response_text = bencode.decode(tracker_response.text)

        if tracker_response.status_code != 200:
            print(f"Failed to get peer list from tracker: {response_text["failure reason"]}", file=sys.stderr)

        # Decode the response to retrieve the dictionary
        tracker_response = [tracker_response.status_code, response_text]

        return tracker_response


    def try_connect_to_peer(self, info_hash: str, peer_info: dict):
        if self.connected_peers.get(peer_info["peer id"]): return

        peer = Peer(
            peer_info["ip"],
            peer_info["port"],
            peer_info["peer id"]
        )
        connected = peer.request_connection()

        if connected and peer.initiate_handshake(info_hash, self.client_peer.peer_id):
            self.connected_peers[peer.peer_id] = peer
            print("Connected to: ", peer.peer_id, peer.address)
            print(f"Completed handshake with {peer.address, peer.port}")


    """Periodically send requests to all available trackers for a torrent until successful"""
    def handle_tracker_requests(self, torrent: Torrent, tracker_url: str):
        try:
            while self.running:
                # TODO: Support for multiple trackers at a time
                # for tracker_url in self.torrent.tracker_list["http"]:
                status_code, response = self.send_tracker_request(tracker_url, torrent.info_hash)

                if status_code == 200:
                    if not self.seeding:
                        for peer_info in response["peers"]:
                            self.try_connect_to_peer(torrent.info_hash, peer_info)

                    #self.peer_list_lock.acquire()
                    self.peer_list = response["peers"]
                    #self.peer_list_lock.release()

                    time.sleep(response["interval"])
                else:
                    # Default interval in case request was unsuccessful
                    time.sleep(DEFAULT_TRACKER_INTERVAL)
        except (SystemExit, KeyboardInterrupt):
            self.stop()


    def start_tracker_requests(self, torrent: Torrent, tracker_url: str, seeding: bool):
        if self.running: return

        self.running = True
        self.seeding = seeding

        # TODO: Remove
        if self.seeding:
            print("MY PEER INFO: ", self.client_peer.peer_id, self.client_peer.address, self.client_peer.port)
        else:
            print("MY PEER INFO: ", self.client_peer.peer_id, self.client_peer.address)

        self.thread = Thread(target = self.handle_tracker_requests, args=(torrent,tracker_url,))
        self.thread.daemon = True
        self.thread.start()


    def start_downloading(self, torrent: Torrent, tracker_url: str):
        self.start_tracker_requests(torrent, tracker_url, False)

        try:
            while self.running:
                time.sleep(DEFAULT_TRACKER_INTERVAL)

        except (SystemExit, KeyboardInterrupt):
            self.stop()


    def get_peer_by_socket(self, socket: socket.socket):
        for peer in self.connected_peers.values():
            if peer.socket == socket:
                return peer
        return None


    def start_seeding(self, torrent: Torrent, tracker_url: str):
        self.start_tracker_requests(torrent, tracker_url, True)

        self.client_peer.start_listening()

        try:
            while self.running:
                socket_list = [self.client_peer.socket]
                readable, _, exceptional = select.select(socket_list, [], socket_list, 1)

                for sock in readable:
                    if sock == self.client_peer.socket:
                        peer_socket, _ = self.client_peer.accept_connection()
                        if peer_socket:
                            peer_address, peer_port = peer_socket.getpeername()
                            peer = Peer(peer_address, peer_port, sock=peer_socket)
                            peer.connected = True

                            print(f"Accepted connection from: {peer_address, peer_port}")

                            handshake: Handshake = peer.respond_handshake(torrent.info_hash, self.client_peer.peer_id)
                            if handshake:
                                print(f"Completed handshake with {peer_address, peer_port}")
                                self.connected_peers[handshake.peer_id] = peer
                    else:
                        sock: socket.socket

                        #Parse wire message from peer
                
                for sock in exceptional:
                    if peer := self.get_peer_by_socket(sock):
                        del self.connected_peers[peer.peer_id]

        except (SystemExit, KeyboardInterrupt):
            self.stop()


    def stop(self):
        self.running = False


    def __del__(self):
        self.stop()
