import io
import os
from flask_cors import CORS
from flask import Blueprint, request, jsonify, session, make_response, current_app
from sklearn.preprocessing import MinMaxScaler
from app.models import User
from app import db
from app.models import Image
from app.prediction import generate_prediction
from werkzeug.security import check_password_hash, generate_password_hash
import jwt
import datetime
import time
import yfinance as yf
from sklearn.linear_model import LinearRegression
import numpy as np
from app.trainingModel import train_model, predict_price
import tensorflow as tf

api_bp = Blueprint('api', __name__)
CORS(api_bp)


@api_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return make_response(jsonify({'message': 'Missing required fields'}), 400)

    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)).first()
    if existing_user:
        return make_response(jsonify({'message': 'Username or email already exists'}), 409)

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, email=email, password=hashed_password)
    db.session.add(new_user)

    max_retries = 3
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            db.session.commit()
            break
        except Exception as e:
            if attempt < max_retries - 1:
                db.session.rollback()
                time.sleep(retry_delay)
            else:
                raise e

    return make_response(jsonify({'message': 'User registered successfully'}), 201)


@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    print(data)
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return make_response(jsonify({'message': 'Missing required fields'}), 400)

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }, current_app.config['SECRET_KEY'])

        return jsonify({'token': token, 'user': {'email': user.email, 'username': user.username}}), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401


@api_bp.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'message': 'No image uploaded'})

    image_file = request.files['image']
    filename = image_file.filename

    # Read the image file and convert it to bytes
    image_bytes = image_file.read()

    # Create a new Image instance and save it to the database
    new_image = Image(filename=filename, data=image_bytes)
    db.session.add(new_image)
    db.session.commit()

    # Pass the image data to the prediction function
    prediction = generate_prediction(io.BytesIO(image_bytes))

    return jsonify({'prediction': prediction})


@api_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'User logged out successfully'})


@api_bp.route('/stocks', methods=['GET'])
def get_available_stocks():
    # Define a list of stock symbols
    stock_symbols = [
        # Greek stocks
        'MYTIL.AT', 'OPAP.AT', 'ETE.AT', 'ALPHA.AT', 'EUROB.AT', 'PPC.AT', 'EXAE.AT', 'LAMDA.AT', 'MOH.AT', 'ELPE.AT',

        # NASDAQ stocks
        'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'FB', 'TSLA', 'NVDA', 'NFLX', 'PYPL', 'INTC', 'CSCO', 'CMCSA', 'PEP', 'ADBE', 'COST',
        'AMGN', 'AVGO', 'TXN', 'CHTR', 'QCOM', 'GILD', 'MDLZ', 'FISV', 'BKNG', 'INTU', 'ADP', 'REGN', 'AMD', 'JD',
        'MU', 'AMAT', 'ILMN', 'LRCX', 'NTES', 'MELI', 'BIDU', 'WDAY', 'ADSK', 'BIIB', 'EBAY', 'NXPI', 'DOCU', 'KLAC', 'WBA',

        # S&P 500 stocks
        'AAPL', 'MSFT', 'AMZN', 'FB', 'BRK-B', 'GOOGL', 'GOOG', 'JNJ', 'JPM', 'V', 'PG', 'XOM', 'UNH', 'MA', 'INTC', 'VZ',
        'DIS', 'HD', 'MRK', 'PFE', 'KO', 'BAC', 'T', 'PEP', 'CMCSA', 'CSCO', 'NFLX', 'NVDA', 'ADBE', 'ABT', 'COST', 'WMT',
        'NKE', 'CRM', 'AMGN', 'MCD', 'MDT', 'ABBV', 'PYPL', 'NEE', 'BMY', 'UNP', 'AVGO', 'TXN', 'ACN', 'QCOM', 'HON', 'C'
    ]

    stocks = [{'code': symbol} for symbol in stock_symbols]
    return jsonify(stocks)


@api_bp.route('/stock/<string:code>', methods=['GET'])
def get_stock_name(code):
    try:
        stock_info = yf.Ticker(code).info
        return jsonify({'name': stock_info['longName']})
    except:
        return jsonify({'name': code})


@api_bp.route('/stocks/<symbol>', methods=['GET'])
def get_stock_data(symbol):
    # Fetch historical stock data using yfinance
    stock_data = yf.download(symbol, start='2022-01-01',
                             end=datetime.datetime.now().strftime('%Y-%m-%d'))

    # Extract the closing prices and dates
    closing_prices = stock_data['Close'].values
    dates = stock_data.index.strftime('%Y-%m-%d').tolist()

    # Prepare the response data
    data = {
        'symbol': symbol,
        'prices': closing_prices.tolist(),
        'labels': dates
    }

    return jsonify(data)


@api_bp.route('/stocks/<symbol>/predict', methods=['GET'])
def get_stock_prediction(symbol):
    # Fetch historical stock data using yfinance
    stock_data = yf.download(symbol, start='2022-01-01',
                             end=datetime.datetime.now().strftime('%Y-%m-%d'))

    # Extract the closing prices
    closing_prices = stock_data['Close'].values.reshape(-1, 1)

    # Create and train the linear regression model
    model = LinearRegression()
    model.fit(np.arange(len(closing_prices)).reshape(-1, 1), closing_prices)

    # Generate predictions for the next 30 days
    future_dates = np.arange(len(closing_prices), len(
        closing_prices) + 30).reshape(-1, 1)
    predicted_prices = model.predict(future_dates)

    # Prepare the response data
    data = {
        'symbol': symbol,
        'predicted_prices': predicted_prices.flatten().tolist()
    }

    return jsonify(data)


@api_bp.route('/predict/<string:code>', methods=['GET'])
def predict_stock_price(code):
    model_file = f"{code}_model.h5"
    if not os.path.exists(model_file):
        return jsonify({'error': f'Model for {code} not found. Please train the model first.'})

    try:
        model = tf.keras.models.load_model(model_file)
        stock_data = yf.download(
            code, start='2022-01-01', end=datetime.datetime.now().strftime('%Y-%m-%d'))
        stock_data = stock_data[['Close']]

        # Scale the data
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(stock_data)

        # Create features for prediction
        lookback = 60
        X = []
        for i in range(lookback, len(scaled_data)):
            X.append(scaled_data[i - lookback:i])
        X = np.array(X)

        # Reshape the input data to match the model's expected shape
        X = np.reshape(X, (X.shape[0], X.shape[1], 1))

        # Make predictions
        predicted_prices = model.predict(X)
        predicted_prices = scaler.inverse_transform(predicted_prices)

        return jsonify({'prices': predicted_prices.flatten().tolist()})
    except Exception as e:
        print(f"Error predicting stock prices for {code}: {str(e)}")
        return jsonify({'error': 'Failed to predict stock prices'})


@api_bp.route('/train/<string:code>', methods=['POST'])
def train_selected_model(code):
    try:
        model = train_model(code)
        model.save(f"{code}_model.h5")
        print(f"Training completed successfully for {code}")
        return jsonify({'message': f'Training completed successfully for {code}'})
    except Exception as e:
        print(f"Error training model for {code}: {str(e)}")
        return jsonify({'error': f'Failed to train model for {code}'})


CORS(api_bp, resources={r"/*": {"origins": "http://localhost:4200"}})
