  # Defines the multi-output CNN model# model_architecture.py
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, Flatten, Dense, Dropout

def build_multi_task_cnn(img_size, channels, num_pokemon, num_types, num_stats):
    """
    Builds a CNN with multi-task outputs:
      - Classification (Pokémon name)
      - Type prediction (multi-label)
      - Stats regression
    """
    inp = Input(shape=(img_size[0], img_size[1], channels))

    x = Conv2D(32, (3,3), activation='relu', padding='same')(inp)
    x = Conv2D(64, (3,3), activation='relu', padding='same')(x)
    x = MaxPooling2D((2,2))(x)
    x = Conv2D(128, (3,3), activation='relu', padding='same')(x)
    x = MaxPooling2D((2,2))(x)
    x = Flatten()(x)
    x = Dense(256, activation='relu')(x)
    x = Dropout(0.5)(x)

    # Pokémon classification
    class_output = Dense(num_pokemon, activation='softmax', name='class_output')(x)

    # Type prediction (multi-label)
    type_output = Dense(num_types, activation='sigmoid', name='type_output')(x)

    # Stats regression
    stat_output = Dense(num_stats, activation='linear', name='stat_output')(x)

    model = Model(inputs=inp, outputs=[class_output, type_output, stat_output])
    return model
