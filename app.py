from flask import Flask, request, jsonify, render_template
from json import loads
import syft as sy
import numpy as np
import torch
import hesystem.server as sv

# Organization information
my_address, private_key, endpoint_url = sv.retrieve_user_info()

# Server configuration
app = Flask(__name__)
conn = sv.set_database('DATABASE_URL')
enc = sv.MultiDimensionalArrayEncoder()
scheduler = sv.schedule_buyer_confirmation()
web3 = sv.set_web3(endpoint_url, my_address)
pub, pri = sy.keygen()

# Contract information
pending_confirmation = []
meta_link, test_link, test_result_link, data_link, result_link, num_rows, value, expiration_time, condition = sv.retrieve_contract_info()
contract_data = sv.ContractData(value, expiration_time, meta_link, test_link, test_result_link, data_link, result_link)
contract_deployed = contract_data.deploy_contract(web3, my_address, private_key)
#contract_deployed = contract_data.use_contract(web3, '0x157c7e9D93Bc09608f852836b3C82219de203c79')
print('Contract address: ' + contract_deployed.address)

# Restaurant Routes
@app.route('/restaurants/data/result', methods=['POST'])
def restaurantsdataresult():
    print('Decrypted result has been requested')
    global my_address
    global condition
    global private_key
    buyer = request.json.get('buyer')
    json_obj = request.json.get('obj')
    obj = loads(json_obj, object_hook=sv.hinted_tuple_hook)
    tensor = sv.deserialize_paillier(obj)
    tensor_decrypted = tensor.decrypt(protocol="paillier", private_key=pri)
    secure_result = sv.check_result(tensor_decrypted, num_rows, condition)
    print(secure_result)

    if secure_result:
        key = contract_deployed.functions.send_decrypted(buyer).buildTransaction({
            'nonce': web3.eth.getTransactionCount(my_address),
            'gas': 1728712,
            'gasPrice': web3.toWei('21','gwei')
        })
        signed_tx = web3.eth.account.signTransaction(key, private_key=private_key)
        hash_tx = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        receipt_tx = web3.eth.waitForTransactionReceipt(hash_tx)
        if receipt_tx.status:
            print(receipt_tx)
            print('Result sent to: ' + buyer)
            return tensor_decrypted.serialize()
        else:
            return jsonify({'message':'You already requested and received a result'})
    else:
        return jsonify({'message':'Your result dimensions should be less than the original dimensions divided by' + condition})
@app.route('/restaurants/test/result', methods=['POST'])
def restaurantstestresult():
    global pri
    print('Decrypted test result requested')
    json_obj = request.json.get('obj')
    obj = loads(json_obj, object_hook=sv.hinted_tuple_hook)
    tensor = sv.deserialize_paillier(obj)
    tensor_decrypted = tensor.decrypt(protocol="paillier", private_key=pri)
    global condition
    secure_result = sv.check_result(tensor_decrypted, num_rows, condition)
    if secure_result:
        return tensor_decrypted.serialize()
    else:
        return jsonify({'message':'There is a problem with your solution'})
@app.route('/restaurants/data', methods=['POST'])
def restaurantsdata():
    print('Real data has been requested')
    buyer = request.json.get('address')
    flag_pay = contract_deployed.functions.f_buyer_payed(buyer).call()
    if flag_pay:
        print('The buyer is: ' + buyer)
        cur = conn.cursor()
        command = "SELECT duracion, business_size, lat "
        command += "FROM RUCs r INNER JOIN businesscategory b on CAST(r.actividad_economica as INT )=b.id_actividad "
        command += "WHERE b.business_category = 'RESTAURANTE'"
        cur.execute(command)
        restaurants = cur.fetchall()
        cur.close()
        array = np.array(restaurants)
        tensor = torch.Tensor(array)
        tensor_encrypted = tensor.encrypt(protocol="paillier", public_key=pub)
        tensor_obj = sv.serialize_paillier(tensor_encrypted)
        global pending_confirmation
        pending_confirmation.append(buyer)

        return enc.encode(tensor_obj)
    else:
        return jsonify({'message':'There is no payment yet'})
@app.route('/restaurants/test', methods=['POST'])
def restaurantstest():
    print('Test data has been requested')
    global pub
    random_array = np.ones(num_rows)
    tensor = torch.Tensor(random_array)
    tensor_encrypted = tensor.encrypt(protocol="paillier", public_key=pub)
    tensor_obj = sv.serialize_paillier(tensor_encrypted)

    return enc.encode(tensor_obj)
@app.route('/restaurant/details', methods=['GET'])
def restaurantsdetails():
    print('Contract details have been requested')
    data = {
    'address': contract_data.address,
    'value': contract_data.value + contract_data.guarantee,
    'abi': contract_data.abi
    }
    return jsonify(data)

# Comparison Route
@app.route('/<string:string>/comparetensor', methods=['POST'])
def comparetensor(string):
    global pri
    print('Comparison requested')
    json_obj = request.json.get('obj')
    function = request.json.get('function')
    obj = loads(json_obj, object_hook=sv.hinted_tuple_hook)
    tensor = sv.deserialize_paillier(obj)
    tensor_decrypted = tensor.decrypt(protocol="paillier", private_key=pri)
    tensor_numpy = tensor_decrypted.numpy()
    if function == '>':
        result = sv.greather_than(tensor_numpy)
    elif function == '<':
        result = sv.less_than(tensor_numpy)
    elif function == '=':
        result = sv.equal_to(tensor_numpy)
    elif function == '>=':
        result = sv.equal_great(tensor_numpy)
    elif function == '<=':
        result = sv.equal_less(tensor_numpy)
    return torch.Tensor(result).serialize()

# Information Website Routes
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/data')
def data():
    return render_template('data.html')
@app.route('/buytutorial')
def buy():
    return render_template('buying.html')
@app.route('/connectiontutorial')
def connection():
    return render_template('connection.html')
@app.route('/librarytutorial')
def library():
    return render_template('library.html')
@app.route('/testtutorial')
def testing():
    return render_template('testing.html')
@app.route('/wallettutorial')
def wallet():
    return render_template('wallet.html')

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(port=5000, use_reloader=False)
