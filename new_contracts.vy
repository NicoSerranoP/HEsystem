#@version 0.1.0b17

# Seller details
value: public(uint256(wei)) # Data price
guarantee: public(uint256(wei)) # Guarantee deposit
expiration_time: public(uint256) # Number of blocks until expiration
seller: public(address) # Data owner

# Data details
meta_link: public(string[200])
test_link: public(string[200])
test_result_link: public(string[200])
data_link: public(string[200])
result_link: public(string[200])

# Buyer details
send_decrypted_time: map(address, uint256)

# Flags
f_buyer_payed: public(map(address, bool))
f_buyer_sent_result: map(address, bool)
f_provider_start_ligitation: map(address, bool)
f_provider_sent_result: public(map(address, bool))
f_buyer_received_result: public(map(address, bool))


@public
def __init__(_value: uint256, _guarantee: uint256, _expiration_time: uint256, _meta_link: string[200], _test_link: string[200], _test_result_link: string[200], _data_link: string[200], _result_link: string[200]):
    self.seller = msg.sender
    self.value = _value
    self.guarantee = _guarantee
    self.expiration_time = _expiration_time

    self.meta_link = _meta_link
    self.test_link = _test_link
    self.test_result_link = _test_result_link
    self.data_link = _data_link
    self.result_link = _result_link
    #col_data is missing


@public
@payable
def buy_data():
    assert(self.value + self.guarantee == msg.value)
    buyer: address = msg.sender
    assert(self.f_buyer_payed[buyer] == False)
    assert(self.f_buyer_sent_result[buyer] == False)
    assert(self.f_provider_start_ligitation[buyer] == False)
    assert(self.f_provider_sent_result[buyer] == False)

    self.f_buyer_payed[buyer] = True

    self.f_buyer_received_result[buyer] = False

@public
def send_result():
    buyer: address = msg.sender
    assert(self.f_buyer_payed[buyer] == True)
    assert(self.f_buyer_sent_result[buyer] == False)
    assert(self.f_provider_start_ligitation[buyer] == False)
    assert(self.f_provider_sent_result[buyer] == False)
    assert(self.f_buyer_received_result[buyer] == False)

    self.f_buyer_sent_result[buyer] = True

@public
def start_ligitation_buyer():
    buyer: address = msg.sender
    assert(self.f_buyer_payed[buyer] == True)
    assert(self.f_buyer_sent_result[buyer] == True)
    assert(self.f_provider_sent_result[buyer] == False)
    assert(self.f_buyer_received_result[buyer] == False)

    self.f_buyer_payed[buyer] = False
    self.f_buyer_sent_result[buyer] = False
    self.f_provider_start_ligitation[buyer] = False
    self.f_provider_sent_result[buyer] = False
    self.f_buyer_received_result[buyer] = True

    send(buyer, self.value + self.guarantee)


@public
def send_decrypted(_buyer: address):
    assert(self.seller == msg.sender)
    assert(self.f_buyer_payed[_buyer] == True)
    assert(self.f_buyer_sent_result[_buyer] == True)
    assert(self.f_provider_start_ligitation[_buyer] == False)
    assert(self.f_provider_sent_result[_buyer] == False)
    assert(self.f_buyer_received_result[_buyer] == False)

    self.f_provider_sent_result[_buyer] = True
    self.send_decrypted_time[_buyer] = block.number

@public
def confirm_result():
    buyer: address = msg.sender
    assert(self.f_buyer_payed[buyer] == True)
    assert(self.f_buyer_sent_result[buyer] == True)
    assert(self.f_provider_start_ligitation[buyer] == False)
    assert(self.f_provider_sent_result[buyer] == True)
    assert(self.f_buyer_received_result[buyer] == False)

    self.f_buyer_payed[buyer] = False
    self.f_buyer_sent_result[buyer] = False
    self.f_provider_start_ligitation[buyer] = False
    self.f_provider_sent_result[buyer] = False
    self.f_buyer_received_result[buyer] = True

    send(self.seller, self.value - self.guarantee)
    send(buyer, self.guarantee)

@public
def reclaim_value(_buyer: address):
    assert(self.seller == msg.sender)
    assert(self.f_buyer_payed[_buyer] == True)
    assert(self.f_buyer_sent_result[_buyer] == True)
    assert(self.f_provider_start_ligitation[_buyer] == False)
    assert(self.f_provider_sent_result[_buyer] == True)
    assert(self.f_buyer_received_result[_buyer] == False)
    assert (block.number > self.send_decrypted_time[_buyer] + self.expiration_time)

    self.f_buyer_payed[_buyer] = False
    self.f_buyer_sent_result[_buyer] = False
    self.f_provider_start_ligitation[_buyer] = False
    self.f_provider_sent_result[_buyer] = False
    self.f_buyer_received_result[_buyer] = True
    send(self.seller, self.value)
