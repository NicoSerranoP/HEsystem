# http://127.0.0.1:5000/restaurants/details
import hesystem as cl
import time

if __name__ == '__main__':
    User = cl.initialize()

    # Real Data
    data, col, ctx = cl.request_data(User, 'rotation')
    start_time = time.time()
    result = sum(col)
    print("Encrypted Sum: %s seconds" % (time.time() - start_time))
    print('Encrypted result:')
    print(result)
    final_result = cl.request_result(User, 'rotation', result, ctx)
    print(f'Sum: {final_result}')
    print(f'Average:{final_result/len(col)}')

    # Get time for sum with unencrypted data
    a = [e for e in range(len(data))]
    start_time = time.time()
    result_check = sum(a)
    print("Normal Sum: %s seconds" % (time.time() - start_time))


    # Testing functions
    #data, public_key = cl.request_test(User, 'rotation')
    #final_result = cl.retrieve_test_result(User, 'rotation', result, public_key)
