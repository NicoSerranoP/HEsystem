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

    # Load data
    tx_data, tx_target, ts_data, ts_target = load_data('framingham.csv', "TenYearCHD", 0.3)

    # Model specifications
    n_features = len(tx_data[0])
    model = LR(n_features)
    optim = torch.optim.SGD(model.parameters(), lr=1)
    criterion = torch.nn.BCELoss()

    # Training
    model = train(model, optim, criterion, tx_data, tx_target)

    # Encrypted evaluation
    eelr = EncryptedLR_evaluation(model)
    data, col, ctx = cl.request_data(User, details_url="http://127.0.0.1:5000/restaurants/details", index=9)
    #eelr.encrypt(ctx)
    enc_out = eelr(data[3])
    enc_result = cl.request_result(User, enc_out, ctx)
    result_sigmoid = torch.sigmoid(torch.Tensor(enc_result).astype(dtype='float32'))
    print(f"Encrypted evaluation result: {result_sigmoid}")

    # Checking the evaluation without encrypted data
    data_check, col_check, ctx_check = cl.request_data(User, details_url="http://127.0.0.1:5000/restaurants/details", index=9)
    enc_out_check = data_check[3]
    enc_result_check = cl.request_result(User, enc_out_check, ctx_check)
    model_check = model(torch.Tensor(enc_result_check))
    print(f"Decrypted evaluation result: {model_check}")
