
from math import ceil
import json, os
import socket
import time


from logs import logger
from hash import get_ack_hash


def serialize(data) -> bytes:
    
    if type(data) == str:
        return data.encode()
    
    if type(data) == list:
        return bytes(data)
    
    if type(data) == dict:
        data = json.dumps(data)
        data = data.encode()
        return data


def receive_json(sock : socket.socket, display : bool = False) -> dict:
    # logger.info(f'Receiving JSON data...')
    
    data = []
    
    while True:
        databuff = sock.recv(1024 * 4)
        if not databuff: break
        data += list(databuff)
        if len(databuff) < (1024 * 4): break
    
    # print()
    obj = json.loads(bytes(data).decode())
    
    sock.sendall(get_ack_hash(data).encode())

    if display:print(json.dumps(obj, indent='\t'))

    return obj



def send_json(obj : dict, sock : socket.socket):
    # logger.info(f'Sending JSON data...')
    
    # print(json.dumps(obj, indent='\t'))
    
    jr = serialize(obj)
    
    sock.sendall(jr)
    rdata_hash = sock.recv(1024).decode()
    
    if rdata_hash != get_ack_hash(jr):
        logger.critical('Data hash mismatch!')
        return
    
    return rdata_hash






def receive_file(sock : socket.socket, dirname : str) -> str:
    filename = ''
    data = []
    
    while True:
        filenamebuff = sock.recv(1024)
        if not filenamebuff: break
        filename += filenamebuff.decode()
        if len(filenamebuff) < 1024: break
    
    
    logger.info(f'Receiving file `{filename}`...')
    
    sock.sendall(get_ack_hash(filename).encode())
    
    disk_location = os.path.join(dirname, filename)
    os.makedirs(os.path.dirname(disk_location), exist_ok=True)
    
    with open(disk_location, 'wb') as file:
        file.write(bytes([]))
    
    with open(disk_location, 'ab') as file:
        while True:
            databuff = sock.recv(1024 * 4)
            if not databuff: break
            
            file.write(databuff)
            
            if len(databuff) < (1024 * 4): break
    
    
    # with open(disk_location, 'rb') as file:
    #     ack = file.read()
    # ack = get_ack_hash(ack)
    # sock.sendall(ack.encode())
    sock.sendall(b'OK')
    
    logger.success(f'Received file `{filename}`!')
    
    return filename


def format_seconds(seconds):
    return time.strftime("%M:%S", time.gmtime(seconds))


def send_data_with_progress(data : bytes, sock : socket.socket, chunk_size : int = 1024 * 4) -> bool:
    nbytes = len(data)
    nchunks = ceil(nbytes / chunk_size)
    
    K = 30
    
    prevtime = time.time()
    original = time.time()
    
    for each in range(nchunks):
        chunk = data[each * chunk_size : (each + 1) * chunk_size]
        ok = sock.send(chunk)
        
        if ok == 0: return False
        
        currtime = time.time()
        dt = currtime - prevtime
        tdt = currtime - original
        eta = format_seconds(dt * (nchunks - each))
        elpased = format_seconds(tdt)
        prevtime = currtime
        
        per = each / nchunks
        p = ('=' * int(K * per)) + (' ' * int(K * (1 - per)))
        p = p[:K]
        
        print(f'\rSending data [{p}] {per*100:2.2f}% ETA {eta} Elapsed {elpased}', end='')
    
    print()
    return True
    
    


def send_file(filename : str, sock : socket.socket, target_filename : str = None):
    logger.info(f'Pushing `{filename}`...')
    
    with open(filename, 'rb') as file:
        data = file.read()
    
    if target_filename is None: target_filename = filename
    
    # sock.sendall(b'<push>')
    sock.sendall(target_filename.encode())
    rfilename_hash = sock.recv(1024).decode()
    
    
    # ok = sock.sendall(data)
    ok = send_data_with_progress(data, sock)
    if not ok:
        logger.critical('File transfer FAILED')
        return
    
    ack_ok = sock.recv(1024).decode()
    
    if ack_ok != 'OK':
        logger.critical('File transfer failed!')
        return
    # if rdata_hash != get_ack_hash(data):
    #     logger.critical('Data hash mismatch!')
    #     return
    
    logger.success(f'Sent `{filename}`!')
    return rfilename_hash #, rdata_hash


