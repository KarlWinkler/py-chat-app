from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer
from prettytable import PrettyTable
import bencode
import time
import urllib.parse
import requests
import sys


DEBUG_MODE = True


class TrackerRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, tracker: 'Tracker', *args, **kwargs):
        self.tracker = tracker
        super().__init__(*args, **kwargs)


    """This is tracker._server.handle_request()"""
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        if not query_params:
            self.send_error_response("Payload required")
            return

        peer_address = self.client_address[0]
        peer_id = query_params.get("peer_id")[0]
        peer_port = query_params.get("port")[0]
        info_hash = query_params.get("info_hash")[0]
        event = query_params.get("event")[0]

        try:
            peer_port = int(peer_port)
        except ValueError:
            self.send_error_response("Bad port")
            return

        if event == "started":
            self.tracker.try_add_peer(info_hash, peer_id, peer_address, peer_port)
        elif event == "stopped":
            # Peer has requested to remove itself from the peer list
            self.tracker.remove_peer(info_hash, peer_id)
        elif event == "completed":
            # TODO: Handle actions when peer is finished downloading
            pass
        else:
            self.send_error_response("Bad event")
            return
        
        # Display peer table stored by tracker
        if DEBUG_MODE:
            print(self.tracker)

        self.send_success_response(info_hash, peer_id)
    

    def send_success_response(self, info_hash: str, requesting_peer_id: str):
        response_payload = {
            "interval": self.tracker.interval,
            "tracker id": self.tracker.tracker_id,
            "complete": 0,
            "incomplete": 0,
            "peers": self.tracker.build_verbose_peer_list(info_hash, requesting_peer_id)
        }
        self.send_response(200)
        self.end_headers()
        self.wfile.write(bencode.encode(response_payload))


    def send_error_response(self, failure_reason: str):
        response_payload = {
            "failure reason": failure_reason
        }
        self.send_response(403)
        self.end_headers()
        self.wfile.write(bencode.encode(response_payload))


class Tracker():
    # Remove peers from the peer list who do not request continuous updates from the tracker after this many seconds
    PEER_INACTIVITY_TIMEOUT = 10
    # Time between tracker requests used if not specified by tracker
    DEFAULT_TRACKER_INTERVAL = 9


    def __init__(self, address: str, port: int, interval: int = 9):
        self.port = port
        self.running = False
        self.interval = interval
        self.torrents = {str: {}}
        self.tracker_id = 0 # TODO: Unique tracker ids are not needed currently
        self.thread = None

        self._server = HTTPServer(
            # Empty string automatically defaults to loopback address
            (address, self.port),
            # Pass a reference to the tracker to the http server
            lambda *args, **kwargs: TrackerRequestHandler(self, *args, **kwargs)
        )
        # Block for 5 seconds before checking for keyboard interrupts if running on main thread
        self._server.timeout = 5
        self.address = self._server.server_address
    

    def build_verbose_peer_list(self, info_hash: str, requesting_peer_id: str) -> list[dict]:
        peers = []

        for peer_id, peer in self.torrents[info_hash].items():
            # Exclude the peer who requested the peer list from the response
            if peer_id != requesting_peer_id:
                peer_data = {
                    "peer id": peer_id,
                    "ip": peer[0],
                    "port": peer[1]
                }
                peers.append(peer_data)
        
        return peers


    def try_add_peer(self, info_hash: str, peer_id: str, address: str, port: int):
        peer_tuple = (address, port, time.time())

        if info_hash in self.torrents:
            self.torrents[info_hash][peer_id] = peer_tuple
        else:
            self.torrents[info_hash] = {peer_id: peer_tuple}
    

    def remove_peer(self, info_hash, peer_id):
        del self.torrents[info_hash][peer_id]


    def remove_unresponsive_peers(self, info_hash: str):
        peers_to_remove = []

        for peer_id, peer in self.torrents[info_hash].items():
            timestamp = peer[2]
            if time.time() - timestamp >= Tracker.PEER_INACTIVITY_TIMEOUT:
                peers_to_remove.append(peer_id)

        for peer_id in peers_to_remove:
            if DEBUG_MODE:
                print("Dead peer removed: ", peer[0], peer[1], time.time() - peer[2])
            self.remove_peer(info_hash, peer_id)


    def handle_requests(self):
        if DEBUG_MODE:
            print(f"Listening for peer requests on {self.address}...")
        try:
            while self.running:
                self._server.handle_request()

                for info_hash in self.torrents:
                    self.remove_unresponsive_peers(info_hash)

        except (SystemExit, KeyboardInterrupt):
            self.running = False


    """ Retrieve list of peers from a tracker """
    @classmethod
    def send_tracker_request(cls, peer_id: str, peer_port: int, tracker_url: str, info_hash: str, event: str = "started", compact: int = 0):
        # Create request payload
        request_payload = {
            "info_hash": info_hash,
            "peer_id": peer_id,
            "port": peer_port,
            "uploaded": 0,
            "downloaded": 0,
            "left": 1000,
            "event": event,
            "compact": compact
        }

        # Send GET request to tracker
        try:
            tracker_response = requests.get(tracker_url, request_payload, timeout=5)
        except requests.exceptions.ConnectionError:
            return [503, {"failure reason": "Service unavailable: No response"}]

        # Decode the response to retrieve the dictionary
        response_text = bencode.decode(tracker_response.text)

        if tracker_response.status_code != 200:
            print(f"Failed to get peer list from tracker: {response_text["failure reason"]}", file=sys.stderr)

        return [tracker_response.status_code, response_text]


    def start(self, new_thread: bool = False):
        self.running = True

        if new_thread:
            self.thread = Thread(target = self.handle_requests)
            self.thread.start()
        else:
            self.handle_requests()
    

    def stop(self):
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
                self.thread = None


    def __str__(self):
        table = PrettyTable()
        table.field_names = ["Peer ID", "IP", "Port"]

        for info_hash in self.torrents:
            for peer_id, peer in self.torrents[info_hash].items():
                table.add_row([peer_id, peer[0], peer[1]])
        
        return table.get_string()


    def __del__(self):
        self.stop()
        self._server.server_close()

