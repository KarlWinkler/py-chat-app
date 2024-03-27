import struct

HANDSHAKE_PSTR = b"Modified BitTorrent"
HANDSHAKE_PSTR_LENGTH = len(HANDSHAKE_PSTR)
HANDSHAKE_MESSAGE_LENGTH = 49 + HANDSHAKE_PSTR_LENGTH


class Message():
    def __init__(self, message_length: int):
        self.message_length = message_length


    def to_bytes(self):
        raise NotImplementedError()


    @classmethod
    def from_bytes(cls, raw_data):
         raise NotImplementedError()


class Handshake(Message):
    def __init__(self, info_hash: str, peer_id: str):
        super().__init__(HANDSHAKE_MESSAGE_LENGTH)
        self.info_hash = info_hash
        self.peer_id = peer_id

    
    def to_bytes(self):
        message = struct.pack("!B", HANDSHAKE_PSTR_LENGTH)
        message += struct.pack("!{}s".format(HANDSHAKE_PSTR_LENGTH), HANDSHAKE_PSTR)
        message += struct.pack("!Q", 0x0)
        message += struct.pack("!20s", self.info_hash)
        message += struct.pack("!20s", self.peer_id.encode('utf-8'))

        return message


    @classmethod
    def from_bytes(cls, raw_message):
        message_length = len(raw_message)

        if message_length != HANDSHAKE_MESSAGE_LENGTH:
            raise Exception(f"Bad message length: {message_length}")
        
        # struct.unpack always returns a tuple
        pstr_len = struct.unpack("!B", raw_message[:1])[0]
        pstr, _, info_hash, peer_id = struct.unpack("!{}s8s20s20s".format(pstr_len), raw_message[1:message_length])

        if pstr != HANDSHAKE_PSTR:
            raise Exception(f"Bad pstr: {[pstr]}")

        return Handshake(info_hash, peer_id)
        

    def validate(self, info_hash: str, client_peer_id: str, expected_peer_id: str = None):
        if self.info_hash != info_hash:
            return False

        if expected_peer_id and self.peer_id == expected_peer_id:
            return True
        
        return self.peer_id != client_peer_id

