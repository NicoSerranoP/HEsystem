# http://127.0.0.1:5000/restaurants/details
import hesystem as cl
import numpy as np
import tenseal as ts
import pandas as pd
import random
import torch

class LR(torch.nn.Module):
    def __init__(self, n_features):
        super(LR, self).__init__()
        self.lr = torch.nn.Linear(n_features, 1)
    def forward(self, x):
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
        enc_out = EncryptedLR_training.sigmoid(enc_out)
        return enc_out

    def backward(self, enc_x, enc_out, enc_y):
        out_minus_y = (enc_out - enc_y)
        self._delta_w += enc_x * out_minus_y
        self._delta_b += out_minus_y
        self._count += 1

    def update_parameters(self):
        if self._count == 0:
            raise RuntimeError("You should at least run one foward iteration")
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

def train(model, optim, criterion, data, target, epochs=1):
    for e in range(epochs):
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
    data = data.drop(columns=["education", "currentSmoker", "BPMeds", "diabetes", "diaBP", "BMI"])

    grouped = data.groupby(target_column)
    data = grouped.apply(lambda x: x.sample(grouped.size().min(), random_state=73).reset_index(drop=True))

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
    User = cl.initialize(file_path="info/user_info.txt")
    data, col, ctx = cl.request_data(User, details_url="http://127.0.0.1:5000/restaurants/details", index=9)

    # Encrypted training
    n_features = len(data[0])
    eelr_training = EncryptedLR_training(LR(n_features))
    eelr_training = enc_train(eelr_training, ctx, data, col)
    # Requesting decrypted result (weights and bias)
    result = [eelr_training.weight, eelr_training.bias]
    final_result = cl.request_result(User, result, ctx)
    # Build a new model with the decrypted result
    eelr_model = LR(n_features)
    eelr_model.lr.weight.data[0] = torch.tensor(final_result[0])
    eelr_model.lr.bias.data = torch.tensor(final_result[1])

    # Create a usual model for testing (Copied from evaluation script)
    tx_data, tx_target, ts_data, ts_target = load_data('framingham.csv', "TenYearCHD", 0.3)
    model = LR(n_features)
    optim = torch.optim.SGD(model.parameters(), lr=1)
    criterion = torch.nn.BCELoss()
    model = train(model, optim, criterion, tx_data, tx_target)

    # To test the evaluation of the usual model and the encrypted model
    data_out = model(ts_data)
    enc_data_out = eelr_model(ts_data)
    correct_threshold = 0.5
    correct_plain = (torch.abs(ts_target - data_out) < correct_threshold).float().mean()
    correct_encrypted = (torch.abs(ts_target - enc_data_out) < correct_threshold).float().mean()
    print(f'Difference between accuracies: {torch.abs(correct_plain - correct_encrypted)}')
