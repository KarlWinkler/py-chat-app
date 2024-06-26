from threading import Thread
from peer import Peer
from torrent import Torrent
from tracker import Tracker
import random
import time
import select
import socket

CLIENT_ID = "FA"
CLIENT_VERSION = "0000"
DEBUG_MODE = True

class Client():
    def __init__(self, address: str, port: int, save_path: str):
        self.client_peer = Peer(address, port, Client.generate_peer_id(), False)
        self.save_path = save_path
        self.connected_peers: dict[str, Peer] = {}
        self.current_tracker_url = None
        self.thread = None
        self.running = False
        self.seeding = False


    """
    Generate Azureus-style 20-byte peer id
    '-', two chars for client id, '-', 4 digits for version number, followed by random numbers
    """
    @staticmethod
    def generate_peer_id():
        return '-' + CLIENT_ID + CLIENT_VERSION + '-' + ''.join(random.choices('0123456789', k=12))


    def try_tracker_urls(self, torrent: Torrent, tracker_urls: list):
        latest_response = None

        for tracker_url in tracker_urls:
            tracker_response = Tracker.send_tracker_request(
                self.client_peer.peer_id,
                self.client_peer.port,
                self.client_peer.address,
                tracker_url,
                torrent.info_hash,
                self.seeding
            )
            latest_response = tracker_response

            if tracker_response[0] == 200:
                self.current_tracker_url = tracker_url
                return tracker_response

        return latest_response


    def join_swarm(self, torrent: Torrent):
        # Already in swarm, send GET to current tracker
        if self.current_tracker_url:
            tracker_response = self.try_tracker_urls(torrent, [self.current_tracker_url])
            # Check if status code is success
            if tracker_response[0] == 200:
                return tracker_response

        # Not in swarm or lost connection with current tracker
        if tracker_urls := torrent.tracker_list.get("http"):
            return self.try_tracker_urls(torrent, tracker_urls)

        return None


    def try_connect_to_peer(self, info_hash: str, peer_info: dict):
        peer = Peer(
            peer_info["ip"],
            peer_info["port"],
            peer_info["peer id"],
            peer_info["seeding"]
        )
        connected = peer.request_connection()

        if connected and peer.initiate_handshake(info_hash, self.client_peer.peer_id, peer.peer_id):
            return peer
        
        return None


    def connect_to_peers(self, info_hash: str, tracker_response: dict):
        for peer_info in tracker_response["peers"]:
            # Only attempt to connect with seeding peers
            if self.connected_peers.get(peer_info["peer id"]) or not peer_info["seeding"]:
                continue
            if peer := self.try_connect_to_peer(info_hash, peer_info):
                self.connected_peers[peer.peer_id] = peer

                if DEBUG_MODE:
                    print(f"Connected to: {peer.peer_id, peer.address, peer.port}")
                    print(f"Completed handshake with {peer.peer_id, peer.address, peer.port}")


    """Periodically send requests to all available trackers for a torrent until successful"""
    def handle_tracker_requests(self, torrent: Torrent):
        try:
            while self.running:
                tracker_response = self.join_swarm(torrent)

                if tracker_response:
                    status_code = tracker_response[0]
                    response_dict: dict = tracker_response[1]

                    if not self.seeding and status_code == 200:
                        self.connect_to_peers(torrent.info_hash, response_dict)

                    time.sleep(response_dict.get("interval", Tracker.DEFAULT_TRACKER_INTERVAL))
                else:
                    time.sleep(Tracker.DEFAULT_TRACKER_INTERVAL)
        except (SystemExit, KeyboardInterrupt):
            self.stop()


    def start_tracker_requests(self, torrent: Torrent):
        if self.running: return
        self.running = True

        self.thread = Thread(target = self.handle_tracker_requests, args=(torrent,))
        self.thread.daemon = True
        self.thread.start()


    def start_downloading(self, torrent: Torrent):
        self.start_tracker_requests(torrent)

        if DEBUG_MODE:
            print("MY PEER INFO: ", self.client_peer.peer_id, self.client_peer.address)

        try:
            while self.running:
                # TODO: SEND REQUEST MESSAGES FOR PIECES
                #Download from connected peers
                for peer in self.connected_peers.values():
                    peer: Peer
                    peer.recv_message(torrent)

        except (SystemExit, KeyboardInterrupt):
            self.stop()


    def get_peer_by_socket(self, socket: socket.socket):
        for peer in self.connected_peers.values():
            if peer.socket == socket:
                return peer
        return None


    def accept_connection(self, torrent: Torrent):
        peer = self.client_peer.accept_connection()
        if not peer:
            return None
        
        if DEBUG_MODE:
            print(f"Accepted connection from: {peer.address, peer.port}")

        received_handshake = peer.respond_handshake(torrent.info_hash, self.client_peer.peer_id)
        if not received_handshake:
            return None

        peer.peer_id = received_handshake.peer_id
        self.connected_peers[peer.peer_id] = peer

        if DEBUG_MODE:
            print(f"Completed handshake with {peer.peer_id, peer.address, peer.port}")

        return peer


    def start_seeding(self, torrent: Torrent):
        self.seeding = True
        self.start_tracker_requests(torrent)

        self.client_peer.start_listening()

        if DEBUG_MODE:
            print("MY PEER INFO: ", self.client_peer.peer_id, self.client_peer.address, self.client_peer.port)

        try:
            while self.running:
                socket_list = [self.client_peer.socket]
                readable, _, exceptional = select.select(socket_list, [], socket_list, 1)

                for sock in readable:
                    if sock == self.client_peer.socket:
                        peer: Peer = self.accept_connection(torrent)
                        if peer is None:
                            continue

                        # Test: Send a block to the connected peer
                        for piece in torrent.pieces:
                            for i in range(len(piece.blocks)):
                                peer.send_block(piece, i)
                    else:
                        sock: socket.socket

                        # TODO: SEND PARSE MESSAGES FROM PEERS
                        # RESPOND TO REQUESTS WITH PIECE MESSAGE
                
                for sock in exceptional:
                    if peer := self.get_peer_by_socket(sock):
                        del self.connected_peers[peer.peer_id]

        except (SystemExit, KeyboardInterrupt):
            self.stop()


    def stop(self):
        self.running = False


    def __del__(self):
        self.stop()
