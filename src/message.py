import struct
from bitstring import BitArray

HANDSHAKE_PSTR = b"Modified BitTorrent"
HANDSHAKE_PSTR_LENGTH = len(HANDSHAKE_PSTR)
HANDSHAKE_MESSAGE_LENGTH = 49 + HANDSHAKE_PSTR_LENGTH

PEER_WIRE_PREFIX_LENGTH = 4
PEER_WIRE_ID_LENGTH = 1
PEER_WIRE_MESSAGE_LENGTH = PEER_WIRE_PREFIX_LENGTH + PEER_WIRE_ID_LENGTH

KEEP_ALIVE_ID = None
CHOKE_ID = 0
UNCHOKE_ID = 1
INTERESTED_ID = 2
NOT_INTERESTED_ID = 3
HAVE_ID = 4
BITFIELD_ID = 5
REQUEST_ID = 6
PIECE_ID = 7

class Message():
    def __init__(self, message_length: int):
        self.message_length = message_length


    def to_bytes(self):
        raise NotImplementedError()


    @classmethod
    def from_bytes(cls, raw_data: bytes):
         raise NotImplementedError()


class Handshake(Message):
    def __init__(self, info_hash: str, peer_id: str):
        super().__init__(HANDSHAKE_MESSAGE_LENGTH)
        self.info_hash = info_hash.encode('utf-8')
        self.peer_id = peer_id

    
    def to_bytes(self):
        message = struct.pack("!B", HANDSHAKE_PSTR_LENGTH)
        message += struct.pack("!{}s".format(HANDSHAKE_PSTR_LENGTH), HANDSHAKE_PSTR)
        message += struct.pack("!Q", 0x0)
        message += struct.pack("!20s", self.info_hash)
        message += struct.pack("!20s", self.peer_id.encode("utf-8"))

        return message


    @classmethod
    def from_bytes(cls, raw_message: bytes):
        message_length = len(raw_message)

        if message_length != HANDSHAKE_MESSAGE_LENGTH:
            raise Exception(f"Bad message length: {message_length}")
        
        # struct.unpack always returns a tuple
        pstr_length = struct.unpack("!B", raw_message[:1])[0]
        pstr, _, info_hash, peer_id = struct.unpack("!{}s8s20s20s".format(pstr_length), raw_message[1:message_length])
        peer_id: bytes = peer_id.decode("utf-8")
        info_hash: bytes = info_hash.decode("utf-8")

        if pstr != HANDSHAKE_PSTR:
            raise Exception(f"Bad pstr: {[pstr]}")

        return Handshake(info_hash, peer_id)
        

    def validate(self, info_hash: str, client_peer_id: str, expected_peer_id: str = None):
        return self.info_hash == info_hash
        # if self.info_hash != info_hash:
        #     return False
        # if expected_peer_id and self.peer_id == expected_peer_id:
        #     return True
        
        # return self.peer_id != client_peer_id


class KeepAlive(Message):
    def __init__(self):
        super().__init__(PEER_WIRE_PREFIX_LENGTH)
        self.payload_length = 0


    def to_bytes(self):
        return struct.pack("!I", self.payload_length)


    @classmethod
    def from_bytes(cls, raw_message: bytes):
        message = struct.unpack("!I", raw_message[:PEER_WIRE_PREFIX_LENGTH])

        if message != 0:
            raise Exception("Malformed KeepAlive message")

        return KeepAlive()


class Bitfield(Message):
    PAYLOAD_LENGTH = None

    def __init__(self, bifield: BitArray):
        super().__init__(PEER_WIRE_MESSAGE_LENGTH)
        self.payload_length = 1
        self.message_id = BITFIELD_ID
        self.bifield = bifield
        self.raw_bitfield = self.bifield.tobytes()
        self.PAYLOAD_LENGTH = len(self.bifield)
        self.message_length = PEER_WIRE_MESSAGE_LENGTH + self.PAYLOAD_LENGTH


    def to_bytes(self):
        message = struct.pack("!IB", self.payload_length, self.message_id)
        message += struct.pack("!{}s".format(self.PAYLOAD_LENGTH), self.raw_bitfield)

        return message


    @classmethod
    def from_bytes(cls, raw_message: bytes):
        payload_length, message_id = struct.unpack("!IB", raw_message[:PEER_WIRE_MESSAGE_LENGTH])

        if message_id != BITFIELD_ID:
            raise Exception("Malformed Bitfield message")
        
        raw_bitfield = struct.unpack("!{}s".format(cls.PAYLOAD_LENGTH), raw_message[PEER_WIRE_MESSAGE_LENGTH:PEER_WIRE_MESSAGE_LENGTH + cls.PAYLOAD_LENGTH])
        bitfield = BitArray(bytes=raw_bitfield)

        return Bitfield(bitfield)


class Choke(Message):
    def __init__(self):
        super().__init__(PEER_WIRE_MESSAGE_LENGTH)
        self.payload_length = 1
        self.message_id = CHOKE_ID


    def to_bytes(self):
        return struct.pack("!IB", self.payload_length, self.message_id)


    @classmethod
    def from_bytes(cls, raw_message: bytes):
        payload_length, message_id = struct.unpack("!IB", raw_message[:PEER_WIRE_MESSAGE_LENGTH])

        if message_id != CHOKE_ID:
            raise Exception("Malformed Choke message")

        return Choke()


class Unchoke(Message):
    def __init__(self):
        super().__init__(PEER_WIRE_MESSAGE_LENGTH)
        self.payload_length = 1
        self.message_id = UNCHOKE_ID


    def to_bytes(self):
        return struct.pack("!IB", self.payload_length, self.message_id)


    @classmethod
    def from_bytes(cls, raw_message: bytes):
        payload_length, message_id = struct.unpack("!IB", raw_message[:PEER_WIRE_MESSAGE_LENGTH])

        if message_id != UNCHOKE_ID:
            raise Exception("Malformed Unchoke message")

        return Unchoke()


class Interested(Message):
    def __init__(self):
        super().__init__(PEER_WIRE_MESSAGE_LENGTH)
        self.payload_length = 1
        self.message_id = INTERESTED_ID


    def to_bytes(self):
        return struct.pack("!IB", self.payload_length, self.message_id)


    @classmethod
    def from_bytes(cls, raw_message: bytes):
        payload_length, message_id = struct.unpack("!IB", raw_message[:PEER_WIRE_MESSAGE_LENGTH])

        if message_id != INTERESTED_ID:
            raise Exception("Malformed Interested message")

        return Interested()


class NotInterested(Message):
    def __init__(self):
        super().__init__(PEER_WIRE_MESSAGE_LENGTH)
        self.payload_length = 1
        self.message_id = NOT_INTERESTED_ID


    def to_bytes(self):
        return struct.pack("!IB", self.payload_length, self.message_id)


    @classmethod
    def from_bytes(cls, raw_message: bytes):
        payload_length, message_id = struct.unpack("!IB", raw_message[:PEER_WIRE_MESSAGE_LENGTH])

        if message_id != NOT_INTERESTED_ID:
            raise Exception("Malformed Not Interested message")

        return NotInterested()


class Have(Message):
    PAYLOAD_LENGTH = 4

    def __init__(self, piece_index: int):
        super().__init__(PEER_WIRE_MESSAGE_LENGTH + self.PAYLOAD_LENGTH)
        self.payload_length = 1
        self.message_id = HAVE_ID
        self.piece_index = piece_index


    def to_bytes(self):
        message = struct.pack("!IB", self.payload_length, self.message_id)
        message += struct.pack("!I", self.piece_index)

        return message


    @classmethod
    def from_bytes(cls, raw_message: bytes):
        payload_length, message_id = struct.unpack("!IB", raw_message[:PEER_WIRE_MESSAGE_LENGTH])

        if message_id != HAVE_ID:
            raise Exception("Malformed Have message")

        piece_index = struct.unpack("!I", raw_message[PEER_WIRE_MESSAGE_LENGTH:PEER_WIRE_MESSAGE_LENGTH + cls.PAYLOAD_LENGTH])

        return Have(piece_index)


class Request(Message):
    PAYLOAD_LENGTH = 4*3

    def __init__(self, piece_index: int, block_offset: int, piece_length: int):
        super().__init__(PEER_WIRE_MESSAGE_LENGTH + self.PAYLOAD_LENGTH)
        self.payload_length = 1
        self.message_id = REQUEST_ID
        self.piece_index = piece_index
        self.block_offset = block_offset
        self.piece_length = piece_length


    def to_bytes(self):
        message = struct.pack("!IB", self.payload_length, self.message_id)
        message += struct.pack("!I", self.piece_index)
        message += struct.pack("!I", self.block_offset)
        message += struct.pack("!I", self.piece_length)

        return message


    @classmethod
    def from_bytes(cls, raw_message: bytes):
        payload_length, message_id = struct.unpack("!IB", raw_message[:PEER_WIRE_MESSAGE_LENGTH])

        if payload_length != 1:
            raise Exception("Malformed Request message")

        if message_id != REQUEST_ID:
            raise Exception("Malformed Request message")
        
        piece_index, block_offset, piece_length = struct.unpack("!III", raw_message[PEER_WIRE_MESSAGE_LENGTH:PEER_WIRE_MESSAGE_LENGTH + cls.PAYLOAD_LENGTH])

        return Request(piece_index, block_offset, piece_length)


class Piece(Message):
    PAYLOAD_LENGTH = None

    def __init__(self, block_length: int, piece_index: int, block_index: int, block_data: bytes):
        super().__init__(PEER_WIRE_MESSAGE_LENGTH)
        self.payload_length = 1
        self.message_id = PIECE_ID
        self.block_length = block_length
        self.piece_index = piece_index
        self.block_index = block_index
        self.block_data = block_data
        self.PAYLOAD_LENGTH = 4*3 + len(self.block_data)
        self.message_length = PEER_WIRE_MESSAGE_LENGTH + self.PAYLOAD_LENGTH


    def to_bytes(self):
        message = struct.pack("!IB", self.payload_length, self.message_id)
        message += struct.pack("!I", self.piece_index)
        message += struct.pack("!I", self.block_index)
        message += struct.pack("!{}s".format(self.block_length), self.block_data)

        return message


    @classmethod
    def from_bytes(cls, raw_message: bytes):
        payload_length, message_id = struct.unpack("!IB", raw_message[:PEER_WIRE_MESSAGE_LENGTH])

        if message_id != PIECE_ID:
            raise Exception("Malformed Piece message")
        
        block_length = len(raw_message) - 4*3 - 1
        piece_index, block_index = struct.unpack("!II", raw_message[PEER_WIRE_MESSAGE_LENGTH:PEER_WIRE_MESSAGE_LENGTH + 4*2])
        block_data = struct.unpack("!{}s".format(block_length), raw_message[PEER_WIRE_MESSAGE_LENGTH + 4*2:PEER_WIRE_MESSAGE_LENGTH + 4*2 + block_length])[0]

        return Piece(block_length, piece_index, block_index, block_data)




