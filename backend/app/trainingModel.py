import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
import yfinance as yf
import datetime


def create_dataset(data, look_back=60):
    X, Y = [], []
    for i in range(len(data) - look_back):
        X.append(data[i:(i + look_back), :])
        Y.append(data[i + look_back, :])
    return np.array(X), np.array(Y)


def train_model(stock_codes):
    # Fetch historical data for multiple stocks
    data = []
    for code in stock_codes:
        stock_data = yf.download(
            code, start='2022-01-01', end=datetime.datetime.now().strftime('%Y-%m-%d'))
        stock_data['Stock'] = code
        data.append(stock_data)

    # Combine the data from multiple stocks
    combined_data = pd.concat(data)

    # Preprocess the data
    combined_data = combined_data[['Close', 'Stock']]
    combined_data = combined_data.pivot_table(
        index=combined_data.index, columns='Stock', values='Close')
    combined_data.fillna(0, inplace=True)

    # Scale the data
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(combined_data)

    # Create features and labels
    lookback = 60
    X, y = create_dataset(scaled_data, lookback)

    # Create and train the model
    model = tf.keras.models.Sequential()
    model.add(tf.keras.layers.LSTM(units=50, return_sequences=True,
              input_shape=(X.shape[1], X.shape[2])))
    model.add(tf.keras.layers.LSTM(units=50))
    model.add(tf.keras.layers.Dense(units=X.shape[2]))
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X, y, epochs=10, batch_size=32)

    return model


def prepare_data(data, look_back=60):
    close_prices = data['Close'].values.reshape(-1, 1)
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(close_prices)
    return scaled_data


def predict_price(stock_symbol, look_back=60, num_predictions=30):
    model = tf.keras.models.load_model(f'{stock_symbol}_model.h5')

    # Fetch the latest stock data
    stock_data = yf.download(stock_symbol, period='1d', interval='1m')

    # Prepare the data for prediction
    scaled_data = prepare_data(stock_data, look_back)
    X_test, _ = create_dataset(scaled_data, look_back)

    # Make predictions for the next num_predictions steps
    predicted_prices = []
    current_data = X_test[-1]
    for _ in range(num_predictions):
        predicted_price = model.predict(np.array([current_data]))
        predicted_prices.append(predicted_price[0, 0])
        current_data = np.append(current_data[1:], predicted_price, axis=0)

    return np.array(predicted_prices)
