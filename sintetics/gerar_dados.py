import pandas as pd
import numpy as np

np.random.seed(6)

n_obs = 1000
n_vars = 7

X = np.random.uniform(low=0.1, high=10.0, size=(n_obs, n_vars))
cols_base = [f"x{i}" for i in range(n_vars)]
df = pd.DataFrame(X, columns=cols_base)


df["log_x0"] = np.log(df["x0"])
df["log_x1"] = np.log(df["x1"])

df["quadratico_x1"] = df["x1"] ** 2
df["quadratico_x2"] = df["x2"] ** 2

df["cubico_x2"] = df["x2"] ** 3
df["cubico_x3"] = df["x3"] ** 3

df["exp_x3"] = np.exp(df["x3"])
df["exp_x4"] = np.exp(df["x4"])

df["soma_x0_x1_x2"] = df["x0"] + df["x1"] + df["x2"]
df["razao_x3_x4"] = df["x3"] / df["x4"]

df["exp_soma_x4_x5"] = np.exp(df["x4"] + df["x5"])
df["log_soma_x0_x3"] = np.log(df["x0"] + df["x3"])
df["x5_maior_0.2"] = df["x5"] > .2

df.to_csv("sintetics/dados_sinteticos.csv", index=False)