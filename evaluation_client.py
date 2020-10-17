# http://127.0.0.1:5000/restaurants/details
import hesystem as cl
import numpy as np
import pandas as pd
import torch
import random
import tenseal as ts

class LR(torch.nn.Module):
    def __init__(self, n_features):
        super(LR, self).__init__()
        self.lr = torch.nn.Linear(n_features, 1)
    def forward(self, x):
        return torch.sigmoid(self.lr(x))

class EncryptedLR_evaluation:
    def __init__(self, torch_lr_model):
        self.weight = torch_lr_model.lr.weight.data.tolist()[0]
        self.bias = torch_lr_model.lr.bias.data.tolist()
    def forward(self, enc_x):
        return enc_x.dot(self.weight) + self.bias
    def __call__(self, *args, **kwargs):
        return self.forward(*args, **kwargs)
    def encrypt(self, context):
        self.weight = ts.ckks_vector(context, self.weight)
        self.bias = ts.ckks_vector(context, self.bias)

def train(model, optim, criterion, data, target, epochs=5):
    for e in range(1, epochs + 1):
        optim.zero_grad()
        out = model(data)
        loss = criterion(out, target)
        loss.backward()
        optim.step()
    return model

def load_data(url, target_column, ratio):
    # load data
    data = pd.read_csv(url)
    data = data.dropna()

    # separate target column from data
    target = torch.tensor(data[target_column].values).float().unsqueeze(1)
    data = data.drop(target_column, "columns")

    # standarize data
    data = (data - data.mean()) / data.std()
    data = torch.tensor(data.values).float()

    # split datasets
    idxs = [i for i in range(len(data))]
    random.shuffle(idxs)
    delim = int(len(data)*ratio)
    train_idxs, test_idxs = idxs[delim:], idxs[:delim]
    return data[train_idxs], target[train_idxs], data[test_idxs], target[test_idxs]


if __name__ == '__main__':
    # Requesting encrypted data
    User = cl.initialize()
    data, col, ctx = cl.request_data(User)

    # Model specifications
    n_features = len(data[0])
    model = LR(n_features)
    optim = torch.optim.SGD(model.parameters(), lr=1)
    criterion = torch.nn.BCELoss()

    # Load data and train model
    tx_data, tx_target, ts_data, ts_target = load_data('local_training_businesses.csv', "duracion", 0.3)
    model = train(model, optim, criterion, tx_data, tx_target)

    # Encrypted evaluation
    eelr = EncryptedLR_evaluation(model)
    enc_out = eelr(data[0])
    final_result = cl.request_result(User, enc_out, ctx)
