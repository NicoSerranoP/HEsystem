import torch
import tenseal as ts
import pandas as pd
import random
from time import time
# those are optional and are not necessary for training
import numpy as np
import matplotlib.pyplot as plt

torch.random.manual_seed(73)
random.seed(73)

def split_train_test(x, y, test_ratio=0.3):
    idxs = [i for i in range(len(x))]
    random.seed(73)
    random.shuffle(idxs)
    # delimiter between test and train data
    delim = int(len(x) * test_ratio)
    test_idxs, train_idxs = idxs[:delim], idxs[delim:]
    return x[train_idxs], y[train_idxs], x[test_idxs], y[test_idxs]

def heart_disease_data():
    data = pd.read_csv("framingham.csv")
    # drop rows with missing values
    data = data.dropna()
    # drop some features
    data = data.drop(columns=["education", "currentSmoker", "BPMeds", "diabetes", "diaBP", "BMI"])
    # balance data
    grouped = data.groupby('TenYearCHD')
    data = grouped.apply(lambda x: x.sample(grouped.size().min(), random_state=73).reset_index(drop=True))
    # extract labels
    y = torch.tensor(data["TenYearCHD"].values).float().unsqueeze(1)
    data = data.drop("TenYearCHD", 'columns')
    # standardize data
    data = (data - data.mean()) / data.std()
    x = torch.tensor(data.values).float()
    return split_train_test(x, y)

def random_data(m=1024, n=2):
    # data separable by the line `y = x`
    x_train = torch.randn(m, n)
    x_test = torch.randn(m // 2, n)
    y_train = (x_train[:, 0] >= x_train[:, 1]).float().unsqueeze(0).t()
    y_test = (x_test[:, 0] >= x_test[:, 1]).float().unsqueeze(0).t()
    return x_train, y_train, x_test, y_test

class LR(torch.nn.Module):

    def __init__(self, n_features):
        super(LR, self).__init__()
        self.lr = torch.nn.Linear(n_features, 1)

    def forward(self, x):
        out = torch.sigmoid(self.lr(x))
        return out

class EncryptedLR:
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

    def decrypt(self, context):
        self.weight = self.weight.decrypt()
        self.bias = self.bias.decrypt()

def train(model, optim, criterion, x, y, epochs=1):
    for e in range(1, epochs + 1):
        optim.zero_grad()
        out = model(x)
        loss = criterion(out, y)
        loss.backward()
        optim.step()
        print(f"Loss at epoch {e}: {loss.data}")
    return model

def enc_train(enc_model, ctx, enc_data_train, enc_target_train, epochs=1):
    enc_model.encrypt(ctx)
    for epoch in range(epochs):
        print(epoch)
        for enc_x, enc_y in zip(enc_data_train, enc_target_train):
            #print(enc_x.size())
            enc_out = enc_model.forward(enc_x)
            enc_model.backward(enc_x, enc_out, enc_y)
        enc_model.update_parameters()
    return enc_model


def accuracy(model, x, y):
    out = model(x)
    correct = torch.abs(y - out) < 0.5
    return correct.float().mean()

def encrypted_evaluation(model, enc_x_test, y_test):
    t_start = time()

    correct = 0
    for enc_x, y in zip(enc_x_test, y_test):
        # encrypted evaluation
        enc_out = model(enc_x)
        # plain comparaison
        out = enc_out.decrypt()
        out = torch.tensor(out)
        out = torch.sigmoid(out)
        if torch.abs(out - y) < 0.5:
            correct += 1

    t_end = time()
    print(f"Evaluated test_set of {len(x_test)} entries in {int(t_end - t_start)} seconds")
    print(f"Accuracy: {correct}/{len(x_test)} = {correct / len(x_test)}")
    return correct / len(x_test)

if __name__ == '__main__':
    data_train, target_train, data_test, target_test = heart_disease_data()

    n_features = data_train.shape[1]
    model = LR(n_features)
    # use gradient descent with a learning_rate=1
    optim = torch.optim.SGD(model.parameters(), lr=1)
    # use Binary Cross Entropy Loss
    criterion = torch.nn.BCELoss()

    model = train(model, optim, criterion, data_train, target_train)

    plain_accuracy = accuracy(model, data_test, target_test)
    print(f"Accuracy on plain test_set: {plain_accuracy}")

    eelr_evaluation = EncryptedLR(model)
    # parameters
    poly_mod_degree = 8192
    coeff_mod_bit_sizes = [40, 21, 21, 21, 21, 21, 21, 40]
    # create TenSEALContext
    ctx_training = ts.context(ts.SCHEME_TYPE.CKKS, poly_mod_degree, -1, coeff_mod_bit_sizes)
    # scale of ciphertext to use
    ctx_training.global_scale = 2 ** 21
    # this key is needed for doing dot-product operations
    ctx_training.generate_galois_keys()

    # Evaluation
    #enc_data_test = [ts.ckks_vector(ctx_training, x.tolist()) for x in data_test]

    #enc_out = eelr_evaluation(enc_data_test[0])
    #print("Single time result")

    # Training
    enc_data_train = [ts.ckks_vector(ctx_training, x.tolist()) for x in data_train]
    enc_target_train = [ts.ckks_vector(ctx_training, y.tolist()) for y in target_train]

    eelr_training = EncryptedLR(LR(n_features))
    eelr_training = enc_train(eelr_training, ctx_training, enc_data_train, enc_target_train)
