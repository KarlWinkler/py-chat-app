from enum import Enum

BLOCK_SIZE = 2 ** 14


class BlockState(Enum):
    EMPTY = 0
    PARTIAL = 1
    FULL = 2


class Block:
    def __init__(self, state: BlockState = BlockState.EMPTY, block_size: int = BLOCK_SIZE, data: bytes = b'', last_seen: float = 0):
        self.state: BlockState.EMPTY = state
        self.block_size: int = block_size
        self.data: bytes = data
        self.last_seen: float = last_seen

