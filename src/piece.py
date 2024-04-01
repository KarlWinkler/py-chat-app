import hashlib
import math

PIECE_HASH_LENGTH = 20

class Piece:
    def __init__(self, index: int, expected_hash: bytes):
        self.index = index
        self.expected_hash = expected_hash
        self.verified = False
        self.downloaded = False
        self.length = None
        self._contents = None


    # read raw hash data in chunks of 20 bytes
    # read raw data in chunks of piece_length, set try updating piece.contents with try_set_contents
    @staticmethod
    def create_pieces(piece_hashes: bytes, raw_data: bytes, piece_length: int) -> list['Piece']:
        hashes_length = len(piece_hashes)
        pieces = []
        offset = 0
        index = 0

        while offset < hashes_length:
            piece_hash = piece_hashes[offset:offset + PIECE_HASH_LENGTH]
            piece = Piece(index, piece_hash)
            #piece.try_set_contents()
            pieces.append(piece)
            offset += PIECE_HASH_LENGTH
            index += 1

        return pieces


    @staticmethod
    def get_hash_count(piece_hashes: bytes):
        return math.ceil(len(piece_hashes) / PIECE_HASH_LENGTH)


    def try_set_contents(self, raw_data: bytes):
        if self._contents:
            return False

        if self.valid(raw_data):
            self.contents = raw_data
            self.length = len(raw_data)
            return True

        return False


    def valid(self, raw_data: bytes):
        return hashlib.sha1(raw_data) == self.expected_hash


    def is_full(self):
        return self._contents

