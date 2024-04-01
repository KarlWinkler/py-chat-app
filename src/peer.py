import sys
import peer_state
import socket
import message


# Maximum number of connections allowed by the socket
MAX_PEER_REQUESTS = 20
# Socket timeout
KEEP_ALIVE_TIMEOUT = 10


class Peer():
    def __init__(self, address: str, port: int, peer_id: str = None, sock: socket.socket = None):
        self.address = address
        self.port = port
        self.peer_id = peer_id

        self.socket = sock if sock else socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(KEEP_ALIVE_TIMEOUT)

        self.state = peer_state.INITIAL
        self.connected = False
        self.completed_handshake = False


    """Send handshake before receive (for downloading peers)"""
    def initiate_handshake(self, info_hash: str, client_peer_id: str, expected_peer_id: str):
        if not self.send_handshake(info_hash, client_peer_id):
            return False

        if not self.receive_handshake(info_hash, client_peer_id, expected_peer_id):
            return False

        self.completed_handshake = True
        return True


    """Receive handshake before send (for uploading peers)"""
    def respond_handshake(self, info_hash: str, client_peer_id: str):
        handshake = self.receive_handshake(info_hash, client_peer_id)
        if not handshake:
            return False

        if not self.send_handshake(info_hash, client_peer_id):
            return False
    
        self.completed_handshake = True
        return handshake


    def send_handshake(self, info_hash: str, client_peer_id: str):
        handshake = message.Handshake(info_hash, client_peer_id)

        if not self.send_data(handshake.to_bytes()):
            return None

        return handshake


    def receive_handshake(self, info_hash: str, client_peer_id: str, expected_peer_id: str = None):
        raw_handshake = self.receive_data(message.HANDSHAKE_MESSAGE_LENGTH)
        if raw_handshake is None:
            return None

        handshake = message.Handshake.from_bytes(raw_handshake)

        if not handshake.validate(info_hash, client_peer_id, expected_peer_id):
            return False

        return handshake


    def send_data(self, raw_data: bytes):
        try:
            self.socket.sendall(raw_data)
            return True
        except Exception as e:
            print(f"Error while sending data: {e}")
            self.disconnect()
            return False


    def receive_data(self, total_bytes: int):
        if not self.connected: return

        raw_data = b''
        bytes_received = 0
        bytes_remaining = total_bytes

        while (bytes_received < total_bytes):
            try:
                chunk = self.socket.recv(bytes_remaining)
            except socket.timeout as e:
                print(f"Socket timeout, closing connection: {e}")
                self.disconnect()
                return None
            
            chunk_length = len(chunk)
            if chunk_length == 0:
                return None

            raw_data += chunk
            bytes_remaining -= chunk_length
            bytes_received += chunk_length

        return raw_data


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
        peer = None
        try:
            peer_socket, _ = self.socket.accept()
            if not peer_socket:
                return None

            peer_address, peer_port = peer_socket.getpeername()
            peer = Peer(peer_address, peer_port, sock=peer_socket)
            peer.connected = True

        except Exception as e:
            print(f"Failed to accept connection request: {e}", file=sys.stderr)
            return None

        return peer


    def disconnect(self):
        self.state = peer_state.NULL
        self.connected = False
        self.seeding = False
        self.leeching = False
        self.socket.close()


    def __del__(self):
        self.disconnect()
