
import torch
import platform
import json, os
import socket

from logs import logger
from hash import get_ack_hash
from serialstuff import receive_json, send_json, receive_file, send_file


dirname = os.path.join( os.curdir,  '.raven')


def sys_info() -> dict[str]:
    """Returns all relevant hardware info for training."""
    
    ndevices = torch.cuda.device_count()
    
    machine_name = platform.node()
    
    info = {
        'machine' : machine_name,
        'devices' : [],
    }
    
    for each in range(ndevices):
        intname = f'cuda:{each}'
        name = torch.cuda.get_device_properties(each).name
        memory = torch.cuda.get_device_properties(each).total_memory
        
        info['devices'].append({
            'name' : name,
            'memory' : memory,
            'int_name' : intname
        })
    
    return info


def get_address():
    return socket.gethostbyname(socket.gethostname())


def verify_magic(sock : socket.socket) -> bool:
    magic_data = sock.recv(1024)
    if not magic_data:
        logger.error('Invalid magic data')
        return False
    magic_data = magic_data.decode()
    if magic_data != 'huginn?muninn?':
        logger.error('Invalid magic data')
        return False
    sock.sendall(b'<raven node>')
    return True







def process_command(command : str, sock : socket.socket):
    if not ((command[0] == '<') and (command[-1] == '>')):
        logger.error(f'Invalid command {command}')
        return
    
    command = command[1:-1]
    if command == 'push': return receive_file(sock, dirname)
    if command == 'json': return receive_json(sock, True)
    
    
    logger.error(f'Invalid command {command}')
    
    
        
device_data = sys_info()
    


def start_server():
    host = get_address()
    port = 4269
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    
    logger.success(f'Server started!')
    logger.debug(f'Running on raven://{host}:{port}')
    
    server.listen(1)
    
    while True:
        try:
            logger.info('Waiting for odin node...')
            client_socket, client_address = server.accept()
            clienthost, clientport = client_address
            logger.info(f"Connection established with odin://{clienthost}:{clientport}")
            
            if not verify_magic(client_socket):
                logger.critical('Magic verification FAILED')
                break
            
            send_json(device_data, client_socket)
            
            
            while True:
                command = client_socket.recv(1024)
                if not command : break
                command = command.decode()
                
                logger.debug(f'Command {command}')
                
                process_command(command, client_socket)

            logger.warning(f"Odin node {clienthost} disconnected.")
            client_socket.close()

        except KeyboardInterrupt:
            break
        # except Exception as e:
        #     logger.critical(e)

    logger.warning("Shutting down server.")
    server.close()



