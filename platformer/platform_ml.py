import numpy as np
from sklearn.linear_model import LinearRegression

class PlatformRegressor:
    def __init__(self):
        self.model = LinearRegression()
        self.data_X = []
        self.data_Y = []


    def record_jump(self, gap, features):
        self.data_X.append(features)
        self.data_Y.append(gap)


    def train(self):
        if len(self.data_X) > 1:
            X = np.array(self.data_X)
            Y = np.array(self.data_Y)
            print(X, Y)
            self.model.fit(X,Y)

    def predict_gap(self, features):
        return int(self.model.predict(np.array(features).reshape(1,-1))[0])
    