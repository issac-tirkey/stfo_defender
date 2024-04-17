from keras.models import Sequential
from keras.layers import Conv1D, MaxPooling1D, Flatten, RepeatVector, LSTM, TimeDistributed, Dense


# # characteristics of the LRCN model
# input_shape = (5, 1)  # each window has 5 timesteps and 1 feature
# kernel_size_conv1 = 3  # based on the output shape change
# kernel_size_conv2 = 3  # based on the output shape change
# pool_size = 1

# model
def create_lrcn_model(input_shape, kernel_size_conv1, kernel_size_conv2, pool_size):
    model = Sequential()
    model.add(Conv1D(filters=64, kernel_size=kernel_size_conv1, activation='relu', input_shape=input_shape))
    model.add(Conv1D(filters=64, kernel_size=kernel_size_conv2, activation='relu'))
    model.add(MaxPooling1D(pool_size=pool_size))
    model.add(Flatten())
    model.add(RepeatVector(2))
    model.add(LSTM(200, return_sequences=True))
    model.add(TimeDistributed(Dense(100, activation='relu')))
    model.add(TimeDistributed(Dense(1)))
    model.compile(optimizer='adam', loss='mse')
    return model
