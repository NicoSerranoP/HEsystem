# HESystem server application
from flask import Flask, request, jsonify, render_template
from tenseal import context
from tenseal import SCHEME_TYPE
import hesystem.server as sv
import numpy as np

# parameters
#poly_mod_degree = 2**13 # value: 8192
#coeff_mod_bit_sizes = [40, 21, 21, 21, 21, 21, 21, 40]
#ctx_training = context(SCHEME_TYPE.CKKS, poly_mod_degree, -1, coeff_mod_bit_sizes)
#ctx_training.global_scale = 2 ** 21

#ctx_training.generate_galois_keys()
#secret_key = ctx_training.secret_key()
#ctx_training.make_context_public()

ctx_train = context(SCHEME_TYPE.CKKS, 2**13, -1, [40, 21, 21, 21, 21, 21, 21, 40])
ctx_train.global_scale = 2 ** 21
ctx_train.generate_galois_keys()
secret_key_train = ctx_train.secret_key()
ctx_train.make_context_public()
ctx_rotation = context(SCHEME_TYPE.CKKS, 2**13, -1, [60, 30, 60])
ctx_rotation.global_scale = 2 ** 30
ctx_rotation.generate_galois_keys()
secret_key_rotation = ctx_rotation.secret_key()
ctx_rotation.make_context_public()
ctx_eval = context(SCHEME_TYPE.CKKS, 2**12, -1, [40, 20, 40])
ctx_eval.global_scale = 2 ** 20
ctx_eval.generate_galois_keys()
secret_key_eval = ctx_eval.secret_key()
ctx_eval.make_context_public()

# Organization information
my_address, private_key, endpoint_url = sv.retrieve_user_info()

# Server configuration
app = Flask(__name__)
conn = sv.set_database('DATABASE_URL')
scheduler = sv.schedule_buyer_confirmation()
web3 = sv.set_web3(endpoint_url, my_address)

# Contract information
pending_confirmation = []
meta_link, test_link, test_result_link, data_link, result_link, num_rows, value, expiration_time, condition = sv.retrieve_contract_info()
contract_data = sv.ContractData(value, expiration_time, meta_link, test_link, test_result_link, data_link, result_link)
#contract_deployed = contract_data.deploy_contract(web3, my_address, private_key)
contract_deployed = contract_data.use_contract(web3, '0x8694A9ed96179d39DFDBD81d8eE3536e8fDaDA71')
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
    params = request.json.get('params')
    global ctx_train
    global secret_key_train
    global ctx_eval
    global secret_key_eval
    global ctx_rotation
    global secret_key_rotation
    if params == 'train':
        ctx_final = ctx_train
        secret_key = secret_key_train
    elif params == 'eval':
        ctx_final = ctx_eval
        secret_key = secret_key_eval
    elif params == 'rotation':
        ctx_final = ctx_rotation
        secret_key = secret_key_rotation
    else:
        ctx_final = ctx_rotation
        secret_key = secret_key_rotation
    result = np.array(sv.deserialize_decrypt(ctx_final, json_obj, secret_key))

    global num_rows
    global condition
    secure_result = sv.check_result(result, num_rows, condition)
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
            print('Result sent to: ' + buyer)
            return jsonify(result.tolist())
        else:
            return jsonify({'message':'You already requested and received a result'})
    else:
        return jsonify({'message':'Your result dimensions should be less than the original dimensions divided by' + condition})
@app.route('/restaurants/test/result', methods=['POST'])
def restaurantstestresult():
    print('Decrypted test result requested')
    json_obj = request.json.get('obj')
    params = request.json.get('params')
    global ctx_train
    global secret_key_train
    global ctx_eval
    global secret_key_eval
    global ctx_rotation
    global secret_key_rotation
    if params == 'train':
        ctx_final = ctx_train
        secret_key = secret_key_train
    elif params == 'eval':
        ctx_final = ctx_eval
        secret_key = secret_key_eval
    elif params == 'mean':
        ctx_final = ctx_rotation
        secret_key = secret_key_rotation
    else:
        ctx_final = ctx_rotation
        secret_key = secret_key_rotation
    result = np.array(sv.deserialize_decrypt(ctx_final, json_obj, secret_key))

    global num_rows
    global condition
    secure_result = sv.check_result(result, num_rows, condition)
    if secure_result:
        return jsonify(result.tolist())
    else:
        return jsonify({'message':'Your result dimensions should be less than the original dimensions divided by' + condition})
@app.route('/restaurants/data', methods=['POST'])
def restaurantsdata():
    print('Real data has been requested')
    buyer = request.json.get('address')
    index = int(request.json.get('index'))
    flag_pay = contract_deployed.functions.f_buyer_payed(buyer).call()
    if flag_pay:
        print('The buyer is: ' + buyer)
        cur = conn.cursor()
        #command = "SELECT lat, lon, duracion, business_size, categoria_CALZADO, categoria_CAFETERIA, categoria_PANADERIA, categoria_FARMACIA, categoria_RESTAURANTE, categoria_TIENDA "
        #command += "FROM RUCs r INNER JOIN businesscategory b on CAST(r.actividad_economica as INT )=b.id_actividad "
        #command += "WHERE b.business_category = 'RESTAURANTE'"
        command = "SELECT male, age, cigsPerDay, prevalentStroke, prevalentHyp, totchol, sysbp, heartRate, glucose, TenYearCHD FROM framingham LIMIT 1000"

        cur.execute(command)
        restaurants = cur.fetchall()
        cur.close()

        array = np.array(restaurants)
        array = (array - array.mean()) / array.std()
        new_array = array[:,index]
        print('standarized selected array element:')
        print('[ ' + str(new_array[0]) + ', ... ]')
        print(f'Sum: {sum(new_array)}')
        new_array = [[e] for e in new_array]
        array = np.delete(array, index, 1)
        array = array.tolist()

        params = request.json.get('params')
        global ctx_train
        global ctx_eval
        global ctx_rotation
        if params == 'train':
            ctx_final = ctx_train
        elif params == 'eval':
            ctx_final = ctx_eval
        elif params == 'mean':

            ctx_final = ctx_rotation
        else:
            ctx_final = ctx_rotation

        ckks_serialized = sv.encrypt_serialize(ctx_final, array)
        col_serialized = sv.encrypt_serialize(ctx_final, new_array)
        ctx_serialized = sv.b64encode(ctx_final.serialize()).decode()

        global pending_confirmation
        pending_confirmation.append(buyer)

        return jsonify({
        'ckks': ckks_serialized,
        'col': col_serialized,
        'ctx': ctx_serialized,
        'params': params,
        })
    else:
        return jsonify({'message':'There is no payment yet'})
@app.route('/restaurants/test', methods=['POST'])
def restaurantstest():
    print('Test data has been requested')
    index = int(request.json.get('index'))
    array = np.ones(num_rows)
    new_array = array[:,index]
    new_array = [[e] for e in new_array]
    array = np.delete(array, index, 1)
    array = array.tolist()

    params = request.json.get('params')
    global ctx_train
    global ctx_eval
    global ctx_rotation
    if params == 'train':
        ctx_final = ctx_train
    elif params == 'eval':
        ctx_final = ctx_eval
    elif params == 'mean':
        ctx_final = ctx_rotation
    else:
        ctx_final = ctx_rotation

    ckks_serialized = sv.encrypt_serialize(ctx_final, array)
    col_serialized = sv.encrypt_serialize(ctx_final, new_array)
    ctx_serialized = sv.b64encode(ctx_final.serialize()).decode()

    return jsonify({
    'ckks': ckks_serialized,
    'col': col_serialized,
    'ctx': ctx_serialized
    })
@app.route('/restaurants/details', methods=['GET'])
def restaurantsdetails():
    print('Contract details have been requested')
    data = {
    'address': contract_data.address,
    'value': contract_data.value + contract_data.guarantee,
    'abi': contract_data.abi
    }
    return jsonify(data)

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
