import pandas as pd
import matplotlib.pylab as plt

data = pd.read_csv("data.csv", delimiter=",")

# print(data)

# plt.plot(data[["y","z"]])
plt.plot(data["a1"])
plt.plot(data["a2"])
plt.plot(data["a3"])
plt.show()