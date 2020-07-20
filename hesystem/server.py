from apscheduler.schedulers.background import BackgroundScheduler
from atexit import register
from os import environ
from psycopg2 import connect
from urllib.parse import urlparse

from numpy import ndarray
from numpy import array

from hesystem.essentials import retrieve_user_info
from hesystem.essentials import MultiDimensionalArrayEncoder
from hesystem.essentials import hinted_tuple_hook
from hesystem.essentials import serialize_paillier
from hesystem.essentials import deserialize_paillier
from hesystem.essentials import to_paillier
from hesystem.essentials import set_web3

# Contract information container
class ContractData():
    def __init__(self, value, expiration_time, meta_link, test_link, test_result_link, data_link, result_link):
        self.value = value
        self.guarantee = int(value*0.1)
        self.expiration_time = expiration_time
        self.meta_link = meta_link
        self.test_link = test_link
        self.test_result_link = test_result_link
        self.data_link = data_link
        self.result_link = result_link

        abi_file = open('info/abi.txt','r')
        bytecode_file = open('info/bytecode.txt','r')
        self.abi = abi_file.read().rstrip()
        self.bytecode = bytecode_file.read().rstrip()
    def deploy_contract(self, web3, my_address, private_key):
        Contract = web3.eth.contract(abi=self.abi, bytecode=self.bytecode)
        construct_tx = Contract.constructor(
            self.value,
            self.guarantee,
            self.expiration_time,
            self.meta_link,
            self.test_link,
            self.test_result_link,
            self.data_link,
            self.result_link,
        ).buildTransaction({
            'nonce': web3.eth.getTransactionCount(my_address),
            'gas': 1728712,
            'gasPrice': web3.toWei('21','gwei')
        })
        signed_tx = web3.eth.account.signTransaction(construct_tx, private_key=private_key)
        tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
        contract_address = tx_receipt.contractAddress
        address = web3.toChecksumAddress(contract_address)
        contract_deployed = web3.eth.contract(address=address,abi=self.abi)
        self.address = contract_address
        return contract_deployed
    def use_contract(self, web3, contract_address):
        self.address = contract_address
        address = web3.toChecksumAddress(contract_address)
        contract_deployed = web3.eth.contract(address=address,abi=self.abi)
        return contract_deployed
def retrieve_contract_info(contract_path='info/contract_info.txt'):
    contract_file = open(contract_path, 'r')
    meta_link = contract_file.readline().lstrip('meta_link:').rstrip()
    test_link = contract_file.readline().lstrip('test_link:').rstrip()
    test_result_link = contract_file.readline().lstrip('test_result_link:').rstrip()
    data_link = contract_file.readline().lstrip('data_link:').rstrip()
    result_link = contract_file.readline().lstrip('result_link:').rstrip()
    num_rows = eval(contract_file.readline().lstrip('num_rows:').rstrip())
    value = eval(contract_file.readline().lstrip('value:').rstrip())
    expiration_time = eval(contract_file.readline().lstrip('expiration_time:').rstrip())
    condition = eval(contract_file.readline().lstrip('condition:').rstrip())
    contract_file.close()
    return meta_link, test_link, test_result_link, data_link, result_link, num_rows, value, expiration_time, condition

# Paillier comparison functions
def greather_than(tensor):
    if isinstance(tensor, ndarray):
        result = tensor
        for i,e in enumerate(tensor):
            result[i] = greather_than(tensor[i])
        return result
    else:
        if tensor > 0:
            return True
        else:
            return False
def less_than(tensor):
    if isinstance(tensor, ndarray):
        result = tensor
        for i,e in enumerate(tensor):
            result[i] = less_than(tensor[i])
        return result
    else:
        if tensor < 0:
            return True
        else:
            return False
def equal_to(tensor):
    if isinstance(tensor, ndarray):
        result = tensor
        for i,e in enumerate(tensor):
            result[i] = equal_to(tensor[i])
        return result
    else:
        if tensor == 0:
            return True
        else:
            return False
def equal_great(tensor):
    if isinstance(tensor, ndarray):
        result = tensor
        for i,e in enumerate(tensor):
            result[i] = equal_great(tensor[i])
        return result
    else:
        if tensor >= 0:
            return True
        else:
            return False
def equal_less(tensor):
    if isinstance(tensor, ndarray):
        result = tensor
        for i,e in enumerate(tensor):
            result[i] = equal_less(tensor[i])
        return result
    else:
        if tensor <= 0:
            return True
        else:
            return False

# Server setup functions
def set_database(env_variable):
    url = urlparse(environ[env_variable])
    conn = connect(
                dbname=url.path[1:],
                user=url.username,
                password=url.password,
                host=url.hostname,
                port=url.port
                )
    return conn
def schedule_buyer_confirmation():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_buyer_confirmation, trigger="interval", hours=3)
    scheduler.start()
    register(lambda: scheduler.shutdown())
    return scheduler
def check_result(tensor, dimensions, condition):
    tensor_size = tensor.shape
    flag = True
    for i, dim in enumerate(tensor_size):
        if dim > dimensions[i]/condition:
            flag = False
    return flag
def check_buyer_confirmation():
    global my_address
    global pending_confirmation
    print("Checking buyer receipt confirmation")
    for buyer in reversed(pending_confirmation):
        flag_pay = contract_deployed.functions.f_buyer_payed(buyer).call()
        if not flag_pay:
            flag_sent_decrypted = contract_deployed.functions.f_provider_sent_result(buyer).call()
            if flag_sent_decrypted:
                flag_received = contract_deployed.functions.f_buyer_received_result(buyer).call()
                if not flag_received:
                    key = contract_deployed.functions.reclaim_value(buyer).buildTransaction({
                        'nonce': web3.eth.getTransactionCount(my_address),
                        'gas': 1728712,
                        'gasPrice': web3.toWei('21','gwei')
                    })
                    signed_tx = web3.eth.account.signTransaction(key, private_key=private_key)
                    hash_tx = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
                    receipt_tx = web3.eth.waitForTransactionReceipt(hash_tx)
                    pending_confirmation.remove(buyer)
