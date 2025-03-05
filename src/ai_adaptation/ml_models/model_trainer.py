import logging
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

class ModelTrainer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model = RandomForestClassifier()
        self.training_data = None
        self.training_parameters = {}

    def load_training_data(self, filepath):
        self.training_data = pd.read_csv(filepath)
        self.logger.info(f"Loaded training data from {filepath}")

    def set_training_parameters(self, **params):
        self.training_parameters = params
        self.logger.info(f"Set training parameters: {params}")

    def train_model(self):
        if self.training_data is None:
            self.logger.error("Training data not loaded.")
            return

        try:
            X = self.training_data.drop('target', axis=1)
            y = self.training_data['target']
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            self.model.set_params(**self.training_parameters)
            self.model.fit(X_train, y_train)
            self.logger.info("Model training completed")

            accuracy = self.model.score(X_test, y_test)
            self.logger.info(f"Model accuracy: {accuracy}")
        except Exception as e:
            self.logger.error(f"Error during model training: {e}")

    def save_model(self, filepath):
        import joblib
        joblib.dump(self.model, filepath)
        self.logger.info(f"Saved model to {filepath}")
