import hashlib

class IDhasher:
    @staticmethod
    def to_md5(int_id:int) -> str:
        return hashlib.md5(str(int_id).encode()).hexdigest()
    
    @staticmethod 
    def from_md5(md5_hash: str) -> int:
        try: 
            return int(md5_hash)
        except ValueError:
            raise ValueError("MD5 issue")
class IDmapper:
    def __init__(self):
        self.hash_to_id = {}
        self.id_to_hash = {}

    def get_hash(self, int_id: int) -> str:
        if int_id not in self.id_to_hash:
            hash_val = hashlib.md5(str(int_id).encode()).hexdigest()
            self.id_to_hash[int_id] = hash_val
            self.hash_to_id[hash_val] = int_id
        return self.id_to_hash[int_id]
    
    def get_id(self, hash_val: str) -> int:
        return self.hash_to_id.get(hash_val)