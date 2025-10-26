# train.py
from data_preprocessing import load_dataset, create_datagen
from model_architecture import build_multi_task_cnn
from config import IMG_SIZE, CHANNELS, BATCH_SIZE, EPOCHS
from tensorflow.keras.optimizers import Adam
import numpy as np

# Correct dataset path for Kaggle
DATASET_PATH = '/kaggle/input/pokemon-generation-one-22k/images/'

# Load dataset
images, labels_encoded, types_list, stats_list, label_encoder = load_dataset(DATASET_PATH)

num_pokemon = labels_encoded.shape[1]
num_types = 18  # Example: number of Pokémon types
num_stats = 6   # HP, Attack, Defense, Sp. Atk, Sp. Def, Speed

# Build model
model = build_multi_task_cnn(IMG_SIZE, CHANNELS, num_pokemon, num_types, num_stats)

# Compile model with multiple losses
model.compile(
    optimizer=Adam(learning_rate=0.001),
    loss={
        'class_output': 'categorical_crossentropy',
        'type_output': 'binary_crossentropy',
        'stat_output': 'mse'
    },
    metrics={'class_output': 'accuracy'}
)

# Train model
model.fit(
    images, 
    {'class_output': labels_encoded, 'type_output': np.random.rand(len(images), num_types), 'stat_output': stats_list},  # Replace type_output with proper encoding
    batch_size=BATCH_SIZE,
    epochs=EPOCHS,
    validation_split=0.2
)

# Save model
model.save('pokemon_multi_task_model.h5')
