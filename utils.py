# utils.py
# Helper functions for visualization, splitting, etc.
import matplotlib.pyplot as plt
import numpy as np

def plot_image(img, title=''):
    plt.imshow(img)
    plt.title(title)
    plt.axis('off')
    plt.show()

def display_predictions(img, pred_class, pred_type, pred_stats, label_encoder):
    print("Predicted Pokémon:", label_encoder.inverse_transform([pred_class])[0])
    print("Predicted Type(s):", pred_type)
    print("Predicted Stats:", pred_stats)
    plot_image(img)
