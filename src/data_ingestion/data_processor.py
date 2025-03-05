import pandas as pd
import numpy as np
import logging

class DataProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def clean_data(self, data):
        self.logger.info("Cleaning data")
        data = data.dropna()
        data = data.drop_duplicates()
        data = data.reset_index(drop=True)
        return data

    def transform_data(self, data):
        self.logger.info("Transforming data")
        data['log_return'] = np.log(data['price'] / data['price'].shift(1))
        data = data.dropna()
        return data

    def process_data(self, data):
        self.logger.info("Processing data")
        data = self.clean_data(data)
        data = self.transform_data(data)
        return data
