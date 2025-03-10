
import json, os
import socket
import inspect

from logs import logger
from hash import get_ack_hash
from serialstuff import send_file, serialize, send_json, receive_json
from nodes import DeviceData, NodeData


dirname = os.path.join( os.curdir , '.odin')
config_file = os.path.join(dirname, 'nodes.json')

def cache_node_config(config : dict, node_name : str):
    os.makedirs(dirname, exist_ok=True)
    if os.path.exists(config_file):
        with open(config_file, 'r') as file:
            original = json.load(file)
    else:
        original = dict()
    original[node_name] = config
    with open(config_file, 'w') as file:
        json.dump(original, file, indent='\t')


def verify_magic(sock : socket.socket) -> bool:
    magic_data = b'huginn?muninn?'
    sock.sendall(magic_data)
    rdata = sock.recv(1024).decode()
    return rdata == '<raven node>'



def connect_raven(host, port) -> socket.socket | None:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    logger.info(f'Connecting to raven://{host}:{port}')
    
    try:
        client.connect((host, port))
        if verify_magic(client):
            node_data = receive_json(client)
            cache_node_config(node_data, host)
            
            logger.success(f'Connected to [{node_data["machine"]}] raven://{host}:{port}')
            
            return client
    except ConnectionRefusedError as e:
        logger.error(f"Couldn't connect to raven://{host}:{port}")

    return None
    


def push_file(filename : str, sock : socket.socket, target_filename : str = None):
    sock.sendall(b'<push>')
    return send_file(filename, sock, target_filename)



def load_nodes_json(configfile : str = None) -> list[NodeData]:
    if configfile is None:
        configfile = config_file
    
    with open(configfile, 'r') as file:
        data = json.load(file)
    
    nodes = []
    for host in data:
        ds = []
        for device in data[host]['devices']:
            ds.append(DeviceData(
                memory = device['memory'],
                name = device['name'],
                int_name = device['int_name'],
            ))
        nodes.append(NodeData(
            machine = data[host]['machine'],
            host=host,
            devices=ds
        ))

    return nodes



header = '''

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision as tv

import numpy as np
import matplotlib.pyplot as plt

import talos


'''

class Raven:
    
    def __init__(self, node_data : NodeData):
        self.nd = node_data
        self.sock : socket.socket = None
    
    
    def connect(self):
        if not self.active:
            self.sock = connect_raven(self.nd.host, 4269)
    
    @property
    def active(self) -> bool:
        return self.sock is not None
    
    def push_file(self, filename : str, target_filename : str = None):
        if not self.active:
            logger.warning(f'Raven node [{self.nd["machine"]}] not active; use .connect()!')
            return
        
        return push_file(filename, self.sock, target_filename)
    
    def push_model(self, module, weights_file : str):
        if not self.active:
            logger.warning(f'Raven node [{self.nd["machine"]}] not active; use .connect()!')
            return
        
        mname = f'{module.__name__}.py'
        temploc = os.path.join(dirname, mname)
        
        with open(temploc, 'w') as file:
            file.write(header + inspect.getsource(module))
        
        
        target_weights_file = os.path.basename(weights_file)
        self.push_file(temploc, mname)
        self.push_file(weights_file, target_weights_file)
    
    
    def exec_script(self, script_path : str, *args, **kwargs):
        self.sock.sendall(b'<exec>')
        
        logger.info(f'Trying to execute `{script_path}`...')
        
        send_json({
            'script' : script_path,
            'args' : args,
            'kwargs' : kwargs,
        }, self.sock)
        
        res = receive_json(self.sock, True)
        if res['status'] == 'OK':
            logger.success(f'Execution complete `{script_path}`!')
            return res
        else:
            logger.error(f'Execution FAILED `{script_path}`!')
            logger.error(res['error'])
            return res
        
        
        
        
        
        

















