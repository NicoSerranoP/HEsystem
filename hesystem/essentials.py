from numpy import ndarray
from numpy import array
from numpy import random
from web3 import Web3

# User manipulation functions
def retrieve_user_info(user_path = 'info/user_info.txt'):
    user_file = open(user_path, 'r')
    address = user_file.readline().lstrip('address:').rstrip()
    private_key = user_file.readline().lstrip('private_key:').rstrip()
    endpoint_url = user_file.readline().lstrip('endpoint_url:').rstrip()
    user_file.close()
    return address, private_key, endpoint_url

# Configuration functions
def set_web3(infura_url, my_address):
    web3 = Web3(Web3.HTTPProvider(infura_url))
    web3.eth.defaultAccount = my_address
    return web3
