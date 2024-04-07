from block import Block, BlockState
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
        self.raw_contents = None
        self.blocks = list[Block]


    # read raw hash data in chunks of 20 bytes
    # read raw data in chunks of piece_length, set try updating piece.contents with try_set_contents
    @staticmethod
    def create_pieces(piece_hashes: bytes, raw_data: bytes, piece_length: int) -> list['Piece']:
        piece_count = len(piece_hashes) / PIECE_HASH_LENGTH
        pieces = []
        hash_offset = 0
        data_offset = 0
        index = 0

        while index < piece_count:
            piece_hash = piece_hashes[hash_offset:hash_offset + PIECE_HASH_LENGTH]
            raw_piece_contents = raw_data[data_offset:data_offset + piece_length]

            piece = Piece(index, piece_hash)
            if piece.try_set_contents(raw_piece_contents):
                pieces.append(piece)

            hash_offset += PIECE_HASH_LENGTH
            data_offset += piece_length
            index += 1

        return pieces


    @staticmethod
    def get_hash_count(piece_hashes: bytes):
        return math.ceil(len(piece_hashes) / PIECE_HASH_LENGTH)


    def try_set_contents(self, raw_data: bytes):
        if self.raw_contents:
            return False

        if self.valid(raw_data):
            self.contents = raw_data
            self.length = len(raw_data)

            #block_count = self.length / block.BLOCK
            #block = Block(BlockState.FULL, data=b'')
            #self.blocks[]

            return True

        return False


    def valid(self, raw_data: bytes):
        return hashlib.sha1(raw_data).digest() == self.expected_hash

