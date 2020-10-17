# http://127.0.0.1:5000/restaurants/details
import hesystem as cl
import numpy as np
import torch
import tenseal as ts

class LR(torch.nn.Module):
    def __init__(self, n_features):
        super(LR, self).__init__()
        self.lr = torch.nn.Linear(n_features, 1)
    def foward(self, x):
        return torch.sigmoid(self.lr(x))

class EncryptedLR_training:
    def __init__(self, torch_lr_model):
        # TenSEAL processes lists and not torch tensors
        # so we take out parameters from the PyTorch model
        self.weight = torch_lr_model.lr.weight.data.tolist()[0]
        self.bias = torch_lr_model.lr.bias.data.tolist()

        # accumulate gradients and count iterations
        self._delta_w = 0
        self._delta_b = 0
        self._count = 0

    def forward(self, enc_x):
        enc_out = enc_x.dot(self.weight) + self.bias
        # if training, you need a sigmoid function
        enc_out = self.sigmoid(enc_out)
        return enc_out

    def backward(self, enc_x, enc_out, enc_y):
        out_minus_y = (enc_out - enc_y)
        self._delta_w += enc_x * out_minus_y
        self._delta_b += out_minus_y
        self._count += 1

    def update_parameters(self):
        if self._count == 0:
            raise Exception("You should at least run one foward iteration")
        self.weight -= self._delta_w*(1/self._count)+self.weight*0.05 #0.05 is to keep layer in range of sigmoid approximation
        self.bias -= self._delta_b*(1/self._count)

        self._delta_w = 0
        self._delta_b = 0
        self._count = 0

    @staticmethod
    def sigmoid(enc_x):
        # use an approximation function for sigmoid
        return enc_x.polyval([0.5,0.197,0,-0.004])

    def __call__(self, *args, **kwargs):
        return self.forward(*args, **kwargs)

    def encrypt(self, context):
        self.weight = ts.ckks_vector(context, self.weight)
        self.bias = ts.ckks_vector(context, self.bias)

def enc_train(enc_model, ctx, enc_data_train, enc_target_train, epochs=1):
    enc_model.encrypt(ctx)
    for epoch in range(epochs):
        for enc_x, enc_y in zip(enc_data_train, enc_target_train):
            enc_out = enc_model.forward(enc_x)
            enc_model.backward(enc_x, enc_out, enc_y)
        enc_model.update_parameters()
    return enc_model

if __name__ == '__main__':
    # Requesting encrypted data
    User = cl.initialize()
    data, col, ctx = cl.request_data(User)

    # Model specifications
    n_features = len(data[0])
    model = LR(n_features)
    optim = torch.optim.SGD(model.parameters(), lr=1)
    criterion = torch.nn.BCELoss()

    # Encrypted training
    eelr_training = EncryptedLR_training(model)
    eelr_training = enc_train(eelr_training, ctx, data, col)

    # Requesting decrypted result (weights and bias)
    result = [eelr_training.weight, eelr_training.bias]
    final_result = cl.request_result(User, result, ctx)
