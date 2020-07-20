# http://127.0.0.1:5000/restaurant/details
import hesystem.client as cl

if __name__ == '__main__':
    User = cl.initialize()

    # Real Data
    data, public_key = cl.request_data(User)
    result = data.transpose().mean(1)[0]
    final_result = cl.request_result(User, result, public_key)

    # Test Data
    #test_data, test_public_key = cl.request_test(User)
    #test_result = test_data.transpose().mean(1)[0]
    #test_final_result = cl.retrieve_test_result(User, test_result, test_public_key)
