import sys
import peer_state
import socket
import message


# Maximum number of connections allowed by the socket
MAX_PEER_REQUESTS = 20
# Socket timeout
TIMEOUT = 5


class PeerSocket():
    def __init__(self, address: str, port: int, peer_id: str):
        self.address = address
        self.port = port
        self.peer_id = peer_id
        self.state = peer_state.INITIAL
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(TIMEOUT)
        self.connected = False
        self.completed_handshake = False
        self.seeding = False


    def start_listening(self):
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.address, self.port))
            self.socket.listen(MAX_PEER_REQUESTS)
            self.seeding = True
        except Exception as e:
            self.seeding = False
            print(f"Failed to bind to port {self.address}:{self.port}: {e}", file=sys.stderr)
        finally:
            return self.seeding


    def request_connection(self):
        try:
            self.socket.connect((self.address, self.port))
            self.connected = True
        except Exception as e:
            self.connected = False
            print(f"Failed to connect to {self.address}:{self.port}: {e}", file=sys.stderr)
        finally:
            return self.connected


    def accept_connection(self):
        connection = None
        try:
            connection = self.socket.accept()
            self.connected = True
        except OSError as e:
            self.connected = False
            print(f"Failed to accept connection request from {self.address}:{self.port}: {e}", file=sys.stderr)
        finally:
            return connection


    def send_data(self, raw_data):
        try:
            self.socket.sendall(raw_data)
            return True
        except Exception as e:
            print(f"Error while sending data: {e}")
            return False


    def receive_data(self, total_bytes):
        if not self.connected: return

        raw_data = b''
        bytes_received = 0
        bytes_remaining = total_bytes

        while (bytes_received < total_bytes):
            try:
                chunk = self.socket.recv(min(4096, bytes_remaining))
            except Exception:
                return None
            
            chunk_length = len(chunk)
            if chunk_length == 0:
                return None

            raw_data += chunk
            bytes_remaining -= chunk_length
            bytes_received += chunk_length

        return raw_data


    def disconnect(self):
        self.connected = False
        self.seeding = False
        self.leeching = False
        self.socket.close()


    def __del__(self):
        self.disconnect()
