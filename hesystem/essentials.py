from syft.frameworks.torch.tensors.interpreters.paillier import PaillierTensor
from syft.serde.serde import deserialize
from phe.paillier import EncryptedNumber
from phe.paillier import PaillierPublicKey
from json import JSONEncoder
from numpy import ndarray
from numpy import array
from numpy import random
from web3 import Web3

from syft import TorchHook
import torch
hook = TorchHook(torch)

# User manipulation functions
def retrieve_user_info(user_path = 'info/user_info.txt'):
    user_file = open(user_path, 'r')
    address = user_file.readline().lstrip('address:').rstrip()
    private_key = user_file.readline().lstrip('private_key:').rstrip()
    endpoint_url = user_file.readline().lstrip('endpoint_url:').rstrip()
    user_file.close()
    return address, private_key, endpoint_url

# Paillier tensor manipulation functions
class MultiDimensionalArrayEncoder(JSONEncoder):
    def encode(self, obj):
        def hint_tuples(item):
            if isinstance(item, tuple):
                return {'__tuple__': True, 'items': item}
            if isinstance(item, list):
                return [hint_tuples(e) for e in item]
            if isinstance(item, dict):
                return {key: hint_tuples(value) for key, value in item.items()}
            else:
                return item
        return super(MultiDimensionalArrayEncoder, self).encode(hint_tuples(obj))
def hinted_tuple_hook(obj):
    if '__tuple__' in obj:
        return tuple(obj['items'])
    else:
        return obj
def serialize_paillier(element):
  # Case 1: tensor recursion
  if isinstance(element, torch.Tensor):
    paillier = element.child
    if isinstance(paillier, PaillierTensor):
      child = [serialize_paillier(subchild) for subchild in paillier.child]
      return {'n': paillier.pubkey.n, 'values': child} # in PaillierPublicKey g = n + 1
    else:
      raise TypeError(type(paillier))

  # Case 2: ndarray recursion
  elif isinstance(element, ndarray):
    return [serialize_paillier(subelement) for subelement in element]

  # Case 3: EncryptedNumber serialization
  elif isinstance(element, EncryptedNumber):
    return (str(element.ciphertext()), str(element.exponent))

  # Case 4: Unknown type
  else:
    raise TypeError(type(element))
def deserialize_paillier(struct, pub=None):
  # Case 1: dict recursion
  if isinstance(struct, dict):
    pub = PaillierPublicKey(n=int(struct['n']))
    child = [deserialize_paillier(substruct, pub) for substruct in struct['values']]
    # Building Paillier Tensor
    tensor = PaillierTensor()
    tensor.child = array(child)
    tensor.pubkey = pub
    return tensor.wrap()

  # Case 2: list recursion
  elif isinstance(struct, list):
    return [deserialize_paillier(substruct, pub) for substruct in struct]

  # Case 3: Tuple deserialization
  elif isinstance(struct, tuple):
    return EncryptedNumber(pub, int(struct[0]), int(struct[1]))

  # Case 4: Unknown type
  else:
    raise TypeError(type(struct))
def to_paillier(element, public_key):
    if isinstance(element, torch.Tensor) and isinstance(element.child, PaillierTensor):
        element.child.pubkey = public_key
        child = element.child.child
        if isinstance(child, ndarray):
          return element
        elif isinstance(child, EncryptedNumber):
          element.child.child = array([child])
          return element
        else:
          raise Exception("The tensor does not have an EncryptedNumber or a np.ndarray as child")
    elif isinstance(element, PaillierTensor):
        element.pubkey = public_key
        return element.wrap()
    elif isinstance(element, ndarray):
        tensor = PaillierTensor()
        tensor.child = element
        tensor.pubkey = public_key
        return tensor.wrap()
    elif isinstance(element, list):
        tensor = PaillierTensor()
        tensor.child = array(element)
        tensor.pubkey = public_key
        return tensor.wrap()
    elif isinstance(element, EncryptedNumber):
        tensor = PaillierTensor()
        tensor.child = array([element])
        tensor.pubkey = public_key
        return tensor.wrap()
    else:
        raise TypeError(type(element))

# Configuration functions
def set_web3(infura_url, my_address):
    web3 = Web3(Web3.HTTPProvider(infura_url))
    web3.eth.defaultAccount = my_address
    return web3
