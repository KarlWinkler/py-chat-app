import bencode
import util
import hashlib
import urllib.parse

class Torrent():
    def __init__(self):
        self.data = None
        self.tracker_list = {}
        self.created_by = None
        self.creation_date = None
        self.encoding = None
        self.piece_length = 0
        self.pieces = None
        self.piece_count = 0
        self.name = None
        self.file_list = {}
        self.info_hash = None
        self.total_length = 0

    
    def load_from_file(self, file_path: str) -> 'Torrent':
        # Read as binary file
        with open(file_path, "rb") as file:
            self.data: dict = bencode.decode(file.read())

        # List of tracker urls
        if "announce-list" in self.data:
            self.tracker_list = Torrent.create_tracker_list(util.flatten(self.data["announce-list"]))
        # Single tracker url
        elif "announce" in self.data:
            self.tracker_list = Torrent.create_tracker_list([self.data["announce"]])

        info = self.data["info"]
        
        # List of files
        if "files" in info:
            self.file_list = info["files"]
            self.total_length = sum(file["length"] for file in self.file_list)
        # Single file
        else:
            self.file_list = {"length": info["length"], "path": info["name"]}
            self.total_length = info["length"]

        self.name = info["name"]
        self.piece_length = info["piece length"]
        self.pieces = info["pieces"]
        self.piece_count = self.total_length // self.piece_length
        self.info_hash = hashlib.sha1(urllib.parse.urlencode(info).encode()).digest()

        # Optional info included in some torrents
        self.created_by = self.data.get("created by")
        self.creation_date = self.data.get("creation date")
        self.encoding = self.data.get("encoding")

        return self


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


