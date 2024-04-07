from enum import Enum

BLOCK_SIZE = 2 ** 12


class BlockState(Enum):
    EMPTY = 0
    FULL = 1


class Block:
    def __init__(self, block_index: int, state: BlockState = BlockState.EMPTY, block_size: int = BLOCK_SIZE, data: bytes = b''):
        self.index = block_index
        self.state = state
        self.block_size = block_size
        self.data = data

