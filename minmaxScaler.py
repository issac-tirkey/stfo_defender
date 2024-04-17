from sklearn.preprocessing import MinMaxScaler
import numpy as np


class NormalizedModel:
    def __init__(self, window_size):
        self.window_size = window_size
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.data = None  # Placeholder for the window data

    def fit(self, data):
        self.data = np.array(data).reshape(-1, 1)
        self.scaler.fit(self.data)

    def transform(self):
        if self.data is None:
            raise ValueError("The model has not been fitted with data.")

        # Check if the current window size matches the initialized window size
        if len(self.data) != self.window_size:
            raise ValueError(f"The data must have a window size of {self.window_size}.")

        # Transforming the data
        return self.scaler.transform(self.data)

    def inverse_transform(self, data):
        transformed_data = np.array(data).reshape(-1, 1)
        return self.scaler.inverse_transform(transformed_data)


# window size of 5
normalized_model = NormalizedModel(window_size=5)

# Example data
example_data = [100, 200, 300, 400, 500]
normalized_model.fit(example_data)


normalized_data = normalized_model.transform()

original_scale_data = normalized_model.inverse_transform(normalized_data)

print("Normalised data:{} \n Orginal data: {}".format(normalized_data, original_scale_data))
