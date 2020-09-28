# http://127.0.0.1:5000/restaurants/details
import hesystem as cl

import numpy as np

if __name__ == '__main__':
    User = cl.initialize()

    # Real Data
    data, ctx = cl.request_data(User)
    result = data[0].mean()
    final_result = cl.request_result(User, result, ctx)

    # Test Data
    test_data, test_ctx = cl.request_test(User)
    test_result = test_data[0].mean()
    test_final_result = cl.retrieve_test_result(User, test_result, test_ctx)
