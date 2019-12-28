# -*- coding: utf-8 -*-
"""parallel_ismail.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Dg2GGPN3OK9MauI2cNxvJnTPPf3M6eWd
"""

#@title Run Imports (double click to open) { form-width: "15%", display-mode: "form" }
from keras.models import Model
from keras.layers import Conv2D, MaxPool2D, Dense, Flatten, Dropout, Input, LSTM, Convolution2D, Embedding, Reshape, Concatenate
from keras.layers.merge import concatenate
from keras.utils import plot_model
import numpy as np

""""# CNN model""""

window_size = 5
num_channels = 128
mesh_rows = 20
mesh_columns = 22
cnn_activation ="tanh"
pool_size = (1,1)
number_conv2D_filters = 10
kernel_shape = (7)
model_activation="sigmoid"

def cnn_model():
  inputs = []
  models = []
  for i in range(window_size):  # Adding mesh inputs
    inp = Input(shape=(mesh_rows, mesh_columns, 1), name = "input"+str(i+1))
    inputs.append(inp)

  for i in range(window_size): # Connecting mesh inputs to CNNs
    conv = Conv2D(number_conv2D_filters, kernel_shape, activation=cnn_activation, \
                  input_shape=(mesh_rows, mesh_columns, 1))(inputs[i])# modify shape and kernel
    pool = MaxPool2D(pool_size=pool_size)(conv) # modify pool size
    x = Model(inputs=inputs[i], outputs=Flatten()(pool))
    models.append(x)
  merged = concatenate([model.output for model in models])

  output = Dense(1, activation=model_activation)(merged)

  cnn_model = Model(inputs=[model.input for model in models], outputs=output)
  return cnn_model,[model.input for model in models]

"""# LSTM model"""

lstm_activation="tanh"
number_lstm_cells = 10
number_nodes_hidden_layers_lstm = 8
number_nodes_lstm_output_layer = 50
number_nodes_hidden = 10


def lstm_model():
  models = []
  for i in range(5):
    input = Input(shape=(num_channels, 1))
    x = Dense(number_nodes_hidden_layers_lstm, activation=model_activation)(input)
    lstm = LSTM(number_lstm_cells,activation=lstm_activation)(x)
    x = Model(inputs=input, outputs=lstm)
    models.append(x)

  combined = concatenate([model.output for model in models])
  z = Dense(50, activation=model_activation)(combined)

  lstm_model = Model(inputs=[model.input for model in models], outputs=z)
  return lstm_model,[model.input for model in models]

"""# Parallel model"""

def parallel_model():
  lstm_network,lstm_inputs = lstm_model()
  cnn,cnn_inputs = cnn_model()

  combined = concatenate([lstm_network.output,cnn.output])
  final = Dense(1,activation=model_activation)(combined)
  inputs_parallel = []
  for i in range(len(lstm_inputs)):
    inputs_parallel.append(lstm_inputs[i])
  for i in range(len(cnn_inputs)):
    inputs_parallel.append(cnn_inputs[i])

  beast = Model(inputs = inputs_parallel,outputs=final)
  
  return beast

mod = parallel_model()
print(mod.summary())
plot_model(mod, show_shapes=True, dpi=50)