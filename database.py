from syft.frameworks.torch.tensors.interpreters.paillier import PaillierTensor
from phe.paillier import EncryptedNumber, PaillierPublicKey
from flask import Flask, request, jsonify
import json
import psycopg2
import torch
import syft as sy
import numpy as np
import tenseal as ts
conn = psycopg2.connect("dbname=basic-provider user=postgres password=postgres")
hook = sy.TorchHook(torch)
pub, pri = sy.keygen()

if __name__ == '__main__':
    cur = conn.cursor()
    command = "SELECT numero_ruc, duracion, business_size, lat, lon "
    command += "FROM RUCs r INNER JOIN businesscategory b on CAST(r.actividad_economica as INT )=b.id_actividad "
    command += "WHERE b.business_category = 'RESTAURANTE'"
    cur.execute(command)
    restaurants = cur.fetchall()

    cur.close()
    conn.close()
    array = np.array(restaurants)
    array = np.transpose(array)    

    random_array = np.random.randn(*array.shape)
    random_array = random_array.tolist()
    array = array.tolist()

    #random_array = np.random.randn(*array.shape)

    poly_mod_degree = 8192
    coeff_mod_bit_sizes = [40, 21, 21, 21, 21, 21, 21, 40]
    # create TenSEALContext
    ctx_training = ts.context(ts.SCHEME_TYPE.CKKS, poly_mod_degree, -1, coeff_mod_bit_sizes)
    ctx_training.global_scale = 2 ** 21
    ctx_training.generate_galois_keys()

    ckks_vec = [ts.ckks_vector(ctx_training, x) for x in array]
    #ckks_vec = ts.ckks_vector(ctx_training, array[0])

    '''
    tensor_encrypted = tensor.encrypt(protocol="paillier", public_key=pub)
    tensor_obj = serialize_paillier(tensor_encrypted)

    # Receiving end
    tensor_received = deserialize_paillier(tensor_obj)
    tensor_received_obj = serialize_paillier(tensor_received)

    # Sending end
    tensor_result_obj = deserialize_paillier(tensor_received_obj)
    tensor_result = tensor_result_obj.decrypt(protocol="paillier", private_key=pri)
    '''
