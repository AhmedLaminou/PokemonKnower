# data_preprocessing.py
# Handles loading, preprocessing, augmentation
import os
import numpy as np
import cv2 as cv
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from config import IMG_SIZE, CHANNELS, VALIDATION_SPLIT
import pandas as pd

def load_dataset(dataset_path):
    """
    Loads images and labels from dataset folder.
    Assumes dataset structure: dataset_path/Pokemon_Name/*.jpg
    """
    images, labels = [], []
    types_list = []  # For multi-label type prediction
    stats_list = []  # For regression (HP, Attack, etc.)

    # Correct path to metadata CSV inside Kaggle dataset
    metadata_path = os.path.join(os.path.dirname(dataset_path), 'pokemon_metadata.csv')
    metadata = pd.read_csv(metadata_path)

    for idx, row in metadata.iterrows():
        img_path = os.path.join(dataset_path, row['Image'])
        img = cv.imread(img_path)
        if img is None:
            continue
        img = cv.resize(img, IMG_SIZE)
        images.append(img)
        labels.append(row['Name'])
        types_list.append([row['Type1'], row.get('Type2', '')])  # some Pokémon have 2 types
        stats_list.append([row['HP'], row['Attack'], row['Defense'], row['Sp. Atk'], row['Sp. Def'], row['Speed']])

    images = np.array(images, dtype='float32') / 255.0
    labels = np.array(labels)
    stats_list = np.array(stats_list, dtype='float32')

    # Encode Pokémon names
    label_encoder = LabelEncoder()
    labels_encoded = label_encoder.fit_transform(labels)
    labels_encoded = to_categorical(labels_encoded)

    return images, labels_encoded, types_list, stats_list, label_encoder

def create_datagen(x_train, y_train):
    datagen = ImageDataGenerator(
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        horizontal_flip=True,
        validation_split=VALIDATION_SPLIT
    )
    train_gen = datagen.flow(x_train, y_train, batch_size=32, subset='training')
    val_gen = datagen.flow(x_train, y_train, batch_size=32, subset='validation')
    return train_gen, val_gen
