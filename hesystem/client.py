from requests import post
from requests import get

from hesystem.essentials import array
from hesystem.essentials import random
from hesystem.essentials import retrieve_user_info
from hesystem.essentials import set_web3

from tenseal import _ts_cpp
from tenseal import ckks_vector_from
from tenseal import context_from
from base64 import b64encode, b64decode

# User information container
class UserData():
    def __init__(self, address, private_key, endpoint_url):
        self.address = address
        self.private_key = private_key
        self.endpoint_url = endpoint_url
        self.web3 = set_web3(endpoint_url, address)
        print('User information ready!')
        print('===========================')

# Client-Server interaction functions
def retrieve_contract_web(web3, url):
    response = get(url)
    data = response.json()
    contract_address = data['address']
    contract_value = data['value']
    contract_abi = data['abi']
    address = web3.toChecksumAddress(contract_address)
    contract = web3.eth.contract(address=address,abi=contract_abi)
    return contract, contract_value
def buy_data(User, index, value):
    contract = User.contract
    web3 = User.web3
    key = contract.functions.buy_data().buildTransaction({
        'nonce': web3.eth.getTransactionCount(User.address),
        'value': value,
        'gas': 1728712,
        'gasPrice': web3.toWei('21', 'gwei')
    })
    signed_tx = web3.eth.account.signTransaction(key, private_key=User.private_key)
    hash_tx = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    receipt_tx = web3.eth.waitForTransactionReceipt(hash_tx)
    if receipt_tx.status:
        url = contract.functions.data_link().call()
        return retrieve_data(User.address, index, url)
    else:
        buy_confirmation = contract.functions.f_buyer_payed(User.address).call()
        if buy_confirmation:
            url = contract.functions.data_link().call()
            return retrieve_data(User.address, index, url)
        else:
            raise Exception('The buy_data function was not executed correctly')

# Client visible functions
def initialize(file_path=None):
    print('Setting up user information')
    print('===========================')
    if file_path:
        address, private_key, endpoint_url = retrieve_user_info(file_path)
        return UserData(address, private_key, endpoint_url)
    else:
        load = input('Do you want to load payment info from file? (Y/N) ')
        if load == 'Y' or load == 'y':
            user_path = input('Enter your information file path: ')
            address, private_key, endpoint_url = retrieve_user_info(user_path)
            return UserData(address, private_key, endpoint_url)
        else:
            address = input('Enter your address (0x514AEa42dA89B7856C81bdAA4A20BD7D64EbA8E4): ')
            private_key = input('Enter your private_key (5D232502101181CADEF51F19294A981E22D2DCA38AB031E9BA6EE12F512263BA): ')
            endpoint_url = input('Enter your endpoint_url (https://ropsten.infura.io/v3/52c1338c6a2220d4a18dfef32ba53c2a): ')
            save = input('Do you want to save this info in a file? (Y/N) ')
            if save == 'Y' or save == 'y':
                user_path = input('Enter your information file path: ')
                user_file = open(user_path, 'w')
                user_file.write('address:'+address+'\n')
                user_file.write('private_key:'+private_key+'\n')
                user_file.write('endpoint_url:'+endpoint_url+'\n')
                user_file.close()
            return UserData(address, private_key, endpoint_url)
def request_data(User, details_url=None, index=None):
    if not details_url:
        details_url = input('Enter the data details url: ')
    if not index:
        index = input('Enter the column index you need separated: ')
    contract, value = retrieve_contract_web(User.web3, details_url)
    User.contract = contract
    data, col, ctx = buy_data(User, index, value)
    print('Data has been received!')
    print('===========================')
    return data, col, ctx
def request_test(User):
    details_url = input('Enter the data details url: ')
    index = input('Enter the column index you need separated: ')
    contract, value = retrieve_contract_web(User.web3, details_url)
    test_url = contract.functions.test_link().call()
    User.contract = contract
    data, col, ctx = retrieve_data(User.address, index, test_url)
    print('Test data has been received!')
    print('===========================')
    return data, col, ctx
def request_result(User, result, ctx):
    print('Real result has been requested!')
    print('===========================')
    contract = User.contract
    web3 = User.web3
    key = contract.functions.send_result().buildTransaction({
        'nonce': web3.eth.getTransactionCount(User.address),
        'gas': 1728712,
        'gasPrice': web3.toWei('21','gwei')
    })
    signed_tx = web3.eth.account.signTransaction(key, private_key=User.private_key)
    hash_tx = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    receipt_tx = web3.eth.waitForTransactionReceipt(hash_tx)
    if receipt_tx.status:
        decrypted_result = retrieve_result(User, result, ctx)
        if not isinstance(decrypted_result, (dict, str)):
            key = contract.functions.confirm_result().buildTransaction({
                'nonce': web3.eth.getTransactionCount(User.address),
                'gas': 1728712,
                'gasPrice': web3.toWei('21','gwei')
            })
            signed_tx = web3.eth.account.signTransaction(key, private_key=User.private_key)
            hash_tx = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
            receipt_tx = web3.eth.waitForTransactionReceipt(hash_tx)
        else:
            print('The result is not in proper format. Consult with the web server.')
            litigation(User)
        return decrypted_result
    else:
        raise Exception('The send_result blockchain function was not executed correctly. Did you already request and receive a result?')
def litigation(User, details_url=None):
    if hasattr(User,'contract'):
        contract = User.contract
    else:
        contract, value = retrieve_contract_web(User.web3, details_url)
    key = contract.functions.start_ligitation_buyer().buildTransaction({
        'nonce': User.web3.eth.getTransactionCount(User.address),
        'gas': 1728712,
        'gasPrice': User.web3.toWei('21','gwei')
    })
    signed_tx = User.web3.eth.account.signTransaction(key, private_key=User.private_key)
    hash_tx = User.web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    receipt_tx = User.web3.eth.waitForTransactionReceipt(hash_tx)
    if receipt_tx.status:
        print("The data purchase has been reverted")
    return receipt_tx
# Data handling useful functions
def retrieve_data(my_address, index, url):
    response = post(url, json={'address': my_address, 'index': index})
    json_obj = response.json()
    try:
        ctx_string = json_obj['ctx']
        ctx = context_from(b64decode(ctx_string))
        data_string = json_obj['ckks']
        data = client_deserialize(ctx, data_string)

        column_string = json_obj['col']
        column = client_deserialize(ctx, column_string)

        set_additional_methods(_ts_cpp.CKKSVector)
        return data, column, ctx
    except:
        return json_obj, json_obj, json_obj
def retrieve_result(User, result, ctx):
    random_data = random.randint(100)
    result = array(result, dtype=object) + random_data
    result = client_serialize(result)

    data = {'buyer': User.address, 'obj': result}
    result_url = User.contract.functions.result_link().call()
    response = post(result_url, json=data)
    result = response.json()
    print('Result has been received!')
    print('===========================')
    try:
        decrypted_result = array(result, dtype=object) - random_data
    except:
        decrypted_result = result
    return decrypted_result
def retrieve_test_result(User, result, ctx):
    random_data = random.randint(100)
    result = array(result, dtype=object) + random_data
    result = client_serialize(result)

    data = {'buyer': User.address, 'obj': result}
    result_url = User.contract.functions.test_result_link().call()
    response = post(result_url, json=data)
    result = response.json()
    print('Result has been received!')
    print('===========================')
    try:
        decrypted_result = array(result, dtype=object) - random_data
    except:
        decrypted_result = result
    return decrypted_result

def client_serialize(result):
    if (isinstance(result, _ts_cpp.CKKSVector)):
        return b64encode(result.serialize()).decode()
    else:
        return [client_serialize(e) for e in result]
def client_deserialize(ctx, result):
    if (not isinstance(result, list)):
        return ckks_vector_from(ctx, b64decode(result))
    else:
        return [client_deserialize(ctx, e) for e in result]

def set_additional_methods(ModifiedClass):
    '''def client_suscript(self, item):
        vector = np.zeros(self.size()).tolist()
        vector[item] = 1
        return self.dot(vector)
    ModifiedClass.__getitem__ = client_suscript
    def client_iter(self):
        self.n = 0
        return self
    ModifiedClass.__iter__ = client_iter
    def client_next(self):
        if self.n <= self.size():
            result = self[self.n]
            self.n += 1
            return result
    ModifiedClass.__next__ = client_next'''
    def client_len(self):
        return self.size()
    ModifiedClass.__len__ = client_len
    def client_mean(self):
        return (self.dot([1]*self.size()))*(1/self.size())
    ModifiedClass.mean = client_mean
