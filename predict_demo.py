# predict_demo.py
# Example prediction on a single image
import cv2 as cv
import numpy as np
from tensorflow.keras.models import load_model
from utils import plot_image, display_predictions
from config import IMG_SIZE, CHANNELS
from data_preprocessing import load_dataset

# Load model
model = load_model('pokemon_multi_task_model.h5', compile=False)

# Load label encoder
_, _, _, _, label_encoder = load_dataset('../input/pokemon-generation-one-22k/')

# Load test image
img_path = '../input/pokemon-generation-one-22k/images/pikachu.png'
img = cv.imread(img_path)
img_resized = cv.resize(img, IMG_SIZE)
img_input = np.expand_dims(img_resized, axis=0) / 255.0

# Predict
pred_class, pred_type, pred_stats = model.predict(img_input)
pred_class_idx = np.argmax(pred_class[0])

display_predictions(img, pred_class_idx, pred_type[0], pred_stats[0], label_encoder)
