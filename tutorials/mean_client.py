# http://127.0.0.1:5000/restaurants/details
import hesystem as cl

if __name__ == '__main__':
    User = cl.initialize()

    # Real Data
    data, col, ctx = cl.request_data(User)
    result = sum(col)
    print('Encrypted result:')
    print(result)
    final_result = cl.request_result(User, result, ctx)
    print(f'Sum: {final_result}')
    print(f'Average:{final_result/len(col)}')
