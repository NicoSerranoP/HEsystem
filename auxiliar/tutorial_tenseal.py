import torch
import tenseal as ts
import pandas as pd
import random
from time import time

# those are optional and are not necessary for training
import numpy as np

torch.random.manual_seed(73)
random.seed(73)


def split_train_test(x, y, test_ratio=0.3):
    idxs = [i for i in range(len(x))]
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

class LR(torch.nn.Module):
    def __init__(self, n_features):
        super(LR, self).__init__()
        self.lr = torch.nn.Linear(n_features, 1)

    def forward(self, x):
        out = torch.sigmoid(self.lr(x))
        return out

class EncryptedLR:
    def __init__(self, torch_lr):
        # TenSEAL processes lists and not torch tensors
        # so we take out parameters from the PyTorch model
        self.weight = torch_lr.lr.weight.data.tolist()[0]
        self.bias = torch_lr.lr.bias.data.tolist()

    def forward(self, enc_x):
        # We don't need to perform sigmoid as this model
        # will only be used for evaluation, and the label
        # can be deduced without applying sigmoid
        enc_out = enc_x.dot(self.weight) + self.bias
        return enc_out

    def __call__(self, *args, **kwargs):
        return self.forward(*args, **kwargs)

    ################################################
    ## You can use the functions below to perform ##
    ## the evaluation with an encrypted model     ##
    ################################################

    def encrypt(self, context):
        self.weight = ts.ckks_vector(context, self.weight)
        self.bias = ts.ckks_vector(context, self.bias)

    def decrypt(self, context):
        self.weight = self.weight.decrypt()
        self.bias = self.bias.decrypt()

def train(model, optim, criterion, x, y, epochs=5):
    for e in range(1, epochs + 1):
        optim.zero_grad()
        out = model(x)
        loss = criterion(out, y)
        loss.backward()
        optim.step()
        print(f"Loss at epoch {e}: {loss.data}")
    return model


def accuracy(model, x, y):
    out = model(x)
    correct = torch.abs(y - out) < 0.5
    print(f"Accuracy: {correct.float().sum()}/{len(x)} = {correct.float().mean()}")
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
    print(f"Encrypted Accuracy: {correct}/{len(x_test)} = {correct / len(x_test)}")
    return correct / len(x_test)

if __name__ == '__main__':
    x_train, y_train, x_test, y_test = heart_disease_data()
    n_features = x_train.shape[1]
    model = LR(n_features)
    # use gradient descent with a learning_rate=1
    optim = torch.optim.SGD(model.parameters(), lr=1)
    # use Binary Cross Entropy Loss
    criterion = torch.nn.BCELoss()

    model = train(model, optim, criterion, x_train, y_train)
    plain_accuracy = accuracy(model, x_test, y_test)

    eelr = EncryptedLR(model)

    # parameters
    poly_mod_degree = 4096
    coeff_mod_bit_sizes = [40, 20, 40]
    # create TenSEALContext
    ctx_eval = ts.context(ts.SCHEME_TYPE.CKKS, poly_mod_degree, -1, coeff_mod_bit_sizes)
    # scale of ciphertext to use
    ctx_eval.global_scale = 2 ** 20
    # this key is needed for doing dot-product operations
    ctx_eval.generate_galois_keys()

    enc_x_test = [ts.ckks_vector(ctx_eval, x.tolist()) for x in x_test]
    encrypted_accuracy = encrypted_evaluation(eelr, enc_x_test, y_test)
    diff_accuracy = plain_accuracy - encrypted_accuracy
    print(f"Difference between plain and encrypted accuracies: {diff_accuracy}")

    #eelr.encrypt(ctx_eval)
    for i in range(100):
        enc_out = eelr(enc_x_test[i])
        print(f'Encrypted result: {enc_out.decrypt()}')
        print(f'Sigmoid applied: {torch.sigmoid(torch.tensor(enc_out.decrypt()))}')
        print(f'Plain result: {model(x_test[i])}')
        print(f'Target result: {y_test[i]}')
