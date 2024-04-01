from bitstring import BitArray
from piece import Piece
from pathlib import Path
import sparse_file
import bencode
import util
import hashlib
import urllib.parse
import math
import os

class Torrent():
    def __init__(self):
        self.data = {}
        self.tracker_list = {}
        self.created_by = None
        self.creation_date = None
        self.encoding = None
        self.piece_length = 0
        self.piece_hashes = None
        self.piece_count = 0
        self.name = None
        self.file_info = {}
        self.file_count = 0
        self.info_hash = None
        self.total_length = 0
        self.bitfield: BitArray = None
        self.pieces: list[Piece] = []
        self.sparse_files = []

    
    @staticmethod
    def load_metainfo_from_file(file_path: str) -> 'Torrent':
        torrent = Torrent()

        # Read as binary file
        with open(file_path, "rb") as file:
            torrent.data = bencode.decode(file.read())

        if not isinstance(torrent.data, dict):
            raise Exception("Decoded torrent file is not a dictionary")

        # List of tracker urls
        if "announce-list" in torrent.data:
            torrent.tracker_list = Torrent.create_tracker_list(util.flatten(torrent.data["announce-list"]))
        # Single tracker url
        elif "announce" in torrent.data:
            torrent.tracker_list = Torrent.create_tracker_list([torrent.data["announce"]])

        info = torrent.data["info"]
        
        # List of files
        if "files" in info:
            torrent.file_info = info["files"]
            torrent.total_length = sum(file["length"] for file in torrent.file_info)
        # Single file
        else:
            torrent.file_info = [{"length": info["length"], "path": info["name"]}]
            torrent.total_length = info["length"]

        torrent.file_count = len(torrent.file_info)

        # Ensure each file only has a single path
        for i in range(torrent.file_count):
            path = torrent.file_info[i]["path"]
            if isinstance(path, list):
                torrent.file_info[i]["path"] = path[0]

        torrent.name = info["name"]
        torrent.piece_length = info["piece length"]
        torrent.piece_hashes = info["pieces"]
        torrent.piece_count = math.ceil(torrent.total_length / torrent.piece_length)
        torrent.bitfield = BitArray([0]*torrent.piece_count)
        torrent.info_hash = hashlib.sha1(urllib.parse.urlencode(info).encode()).digest()

        if torrent.piece_count != Piece.get_hash_count(torrent.piece_hashes):
            raise Exception("Total length of file does not match number of piece hashes")

        # Optional info included in some torrents
        torrent.created_by = torrent.data.get("created by")
        torrent.creation_date = torrent.data.get("creation date")
        torrent.encoding = torrent.data.get("encoding")

        return torrent


    """Build list of HTTP and UDP tracker urls"""
    @staticmethod
    def create_tracker_list(tracker_urls: list[str]) -> tuple[str, str, int]:
        tracker_list = {"udp": [], "http": []}

        for url in tracker_urls:
            # Remove the info hash from the url (will be calculated manually)
            trimmed_url = '/'.join(url.split('/')[:3])
            url = url.lower()

            if url.startswith("http"):
                tracker_list["http"].append(trimmed_url)
            elif url.startswith("udp"):
                tracker_list["udp"].append(trimmed_url)

        return tracker_list


    # load pieces which have already been downloaded from disk
    def load_pieces(self, save_path: str):
        # Create parent directories if they don't exist
        Path(save_path).mkdir(parents=True, exist_ok=True)

        for f_info in self.file_info:
            file_path = os.path.join(save_path, f_info["path"])
            self.sparse_files.append(sparse_file.open_sparse(file_path, "wb+"))

        # TODO: retrieve length of sparse file (in place of 0)
        self.pieces = Piece.create_pieces(self.piece_hashes, 0, self.piece_length)

        for piece in self.pieces:
            if piece.is_full():
                self.bitfield.set(value=1, pos=piece.index)

        #print(self)

        # with open(file_path, "w+") as file:
        #     pass
        #     #self.sparse_file = sparse_file.open_sparse(file_path, "wb+")


    # when client downloads a new piece, we need to update the list
    def write_piece(self, piece: Piece):
        self.bitfield.set(value=1, pos=piece.index)
        self.pieces[piece.index] = piece

        # update sparse file


    def __str__(self):
        return ''.join('1' if bit else '0' for bit in self.bitfield)
