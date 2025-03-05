import logging
import pandas as pd
from sklearn.base import BaseEstimator

class OnlineLearner:
    def __init__(self, model: BaseEstimator):
        self.logger = logging.getLogger(__name__)
        self.model = model
        self.data = pd.DataFrame()

    def update_model(self, X_new, y_new):
        if self.data.empty:
            self.data = pd.DataFrame(X_new)
            self.data['target'] = y_new
        else:
            new_data = pd.DataFrame(X_new)
            new_data['target'] = y_new
            self.data = pd.concat([self.data, new_data], ignore_index=True)

        X = self.data.drop('target', axis=1)
        y = self.data['target']
        self.model.partial_fit(X, y)
        self.logger.info("Model updated with new data")

    def predict(self, X):
        return self.model.predict(X)

    def evaluate_model(self, X_test, y_test):
        y_pred = self.predict(X_test)
        accuracy = (y_pred == y_test).mean()
        self.logger.info(f"Model evaluation - Accuracy: {accuracy}")
        return accuracy
