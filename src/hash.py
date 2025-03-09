
from hashlib import sha256

def get_ack_hash(data):
    if type(data) == str:
        data = data.encode()
    if type(data) == list:
        data = bytes(data)
    
    return sha256(data, usedforsecurity=False).hexdigest()[:16]


