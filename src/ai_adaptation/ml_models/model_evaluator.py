import logging
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

class ModelEvaluator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def evaluate_model(self, model, X_test, y_test):
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')

        self.logger.info(f"Model Evaluation - Accuracy: {accuracy}, Precision: {precision}, Recall: {recall}, F1 Score: {f1}")

        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }

    def calculate_evaluation_metrics(self, y_true, y_pred):
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, average='weighted')
        recall = recall_score(y_true, y_pred, average='weighted')
        f1 = f1_score(y_true, y_pred, average='weighted')

        self.logger.info(f"Calculated Evaluation Metrics - Accuracy: {accuracy}, Precision: {precision}, Recall: {recall}, F1 Score: {f1}")

        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }

    def evaluate_model_real_time(self, model, X_stream, y_stream):
        """
        Evaluate the model in real-time using streaming data.
        
        Args:
            model: Trained model to evaluate
            X_stream: Streaming input features
            y_stream: Streaming true labels
            
        Returns:
            dict: Evaluation metrics
        """
        y_pred_stream = model.predict(X_stream)
        accuracy = accuracy_score(y_stream, y_pred_stream)
        precision = precision_score(y_stream, y_pred_stream, average='weighted')
        recall = recall_score(y_stream, y_pred_stream, average='weighted')
        f1 = f1_score(y_stream, y_pred_stream, average='weighted')

        self.logger.info(f"Real-Time Model Evaluation - Accuracy: {accuracy}, Precision: {precision}, Recall: {recall}, F1 Score: {f1}")

        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }
