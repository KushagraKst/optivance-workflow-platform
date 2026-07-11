from sklearn.linear_model import LinearRegression
import numpy as np

def predict(values):
    X = np.arange(len(values)).reshape(-1, 1)
    y = np.array(values)

    model = LinearRegression()
    model.fit(X, y)

    return model.predict([[len(values)]])[0]