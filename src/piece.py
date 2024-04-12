from block import Block, BlockState, BLOCK_SIZE
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
        self.data = None
        self.blocks = []


    @staticmethod
    def create_pieces(piece_hashes: bytes, raw_data: bytes, piece_length: int) -> list['Piece']:
        piece_count = len(piece_hashes) / PIECE_HASH_LENGTH
        pieces = []
        hash_offset = 0
        data_offset = 0
        index = 0
        piece_count = 6

        while index < piece_count:
            piece_hash = piece_hashes[hash_offset:hash_offset + PIECE_HASH_LENGTH]
            raw_piece_contents = raw_data[data_offset:data_offset + piece_length]

            piece = Piece(index, piece_hash)
            piece.try_init_contents(raw_piece_contents)
            pieces.append(piece)

            hash_offset += PIECE_HASH_LENGTH
            data_offset += piece_length
            index += 1

        return pieces


    @staticmethod
    def get_hash_count(piece_hashes: bytes):
        return math.ceil(len(piece_hashes) / PIECE_HASH_LENGTH)


    def add_block(self, block: Block, block_index: int):
        #if 0 <= block.index <= len(self.blocks) - 1:
        self.blocks.insert(block_index, block)
        print(f"piece {self.index} is now {len(self.blocks)} long")


    def try_update_contents(self):
        if len(self.blocks) == 0:
            return False
        
        first_block: Block = self.blocks[0]
        block_length = len(first_block.data)
        expected_block_count = math.ceil(self.length/block_length)

        #print("actual vs expected:", len(self.blocks), expected_block_count)

        if len(self.blocks) == expected_block_count:
            data = b''
            for i in range(self.block_count):
                block: Block = self.blocks[i]
                data += block.data
            self.data = data

            #print(self.data.decode('utf-8'))

            return True
        return False


    def try_init_contents(self, data: bytes):
        if self.data:
            return False

        #if self.valid(data):
        self.data = data
        self.length = len(data)
        self.block_count = math.ceil(self.length / BLOCK_SIZE)

        block_offset = 0
        for i in range(self.block_count):
            block = Block(i, BlockState.FULL, data=self.data[block_offset:block_offset + BLOCK_SIZE])
            self.blocks.append(block)
            block_offset += BLOCK_SIZE

        # Adjust the size of the last block to match the size of the actual contents
        last_block: Block = self.blocks[self.block_count - 1]
        last_block.block_size = len(last_block.data)

        return True


    def valid(self, raw_data: bytes = None):
        if raw_data is None:
            raw_data = self.data
        return hashlib.sha1(raw_data).digest() == self.expected_hash

