from ultralyticsplus import YOLO, render_result
import cv2
import numpy as np
import yfinance as yf
from sklearn.linear_model import LinearRegression
import datetime


def generate_prediction(image_data):
    # Load the pretrained model from HuggingFace
    model = YOLO('foduucom/stockmarket-future-prediction')

    # Set model parameters
    model.overrides['conf'] = 0.25  # NMS confidence threshold
    model.overrides['iou'] = 0.45  # NMS IoU threshold
    model.overrides['agnostic_nms'] = False  # NMS class-agnostic
    model.overrides['max_det'] = 1000  # maximum number of detections per image

    # Read the image data from bytes
    image_np = np.frombuffer(image_data.read(), np.uint8)
    image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

    # Perform inference
    results = model.predict(image)

    # Observe results
    print(results[0].boxes)
    render = render_result(model=model, image=image, result=results[0])
    render.show()

    # Return the prediction result
    prediction = results[0].boxes.cls[0].item()
    return prediction


def predict_stock_prices(symbol):
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

    return predicted_prices.flatten().tolist()
