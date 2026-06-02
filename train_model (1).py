# ============================================
# PLASTIC CLASSIFICATION MODEL
# ACCORDING TO YOUR FOLDER STRUCTURE
# ============================================

# pip install tensorflow matplotlib pillow

# ============================================
# IMPORT LIBRARIES
# ============================================

import tensorflow as tf
from tensorflow.keras import layers, models
import matplotlib.pyplot as plt
import numpy as np
from tensorflow.keras.preprocessing import image

# ============================================
# DATASET PATH
# ============================================

import os
dataset_path = os.path.join(os.path.dirname(__file__), "camera plastic")

# ============================================
# LOAD TRAINING DATASET
# ============================================

train_ds = tf.keras.preprocessing.image_dataset_from_directory(
    dataset_path,
    validation_split=0.2,
    subset="training",
    seed=123,
    image_size=(224,224),
    batch_size=32,

    # YOUR FOLDER ORDER
    class_names=['Others', 'PC', 'PE', 'PET', 'PP', 'PS']
)

# ============================================
# LOAD VALIDATION DATASET
# ============================================

val_ds = tf.keras.preprocessing.image_dataset_from_directory(
    dataset_path,
    validation_split=0.2,
    subset="validation",
    seed=123,
    image_size=(224,224),
    batch_size=32,

    # SAME ORDER
    class_names=['Others', 'PC', 'PE', 'PET', 'PP', 'PS']
)

# ============================================
# SHOW CLASS NAMES
# ============================================

class_names = train_ds.class_names

print("\nDetected Classes:")
print(class_names)

# ============================================
# OPTIMIZE DATASET
# ============================================

AUTOTUNE = tf.data.AUTOTUNE

train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)

val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

# ============================================
# SHOW SAMPLE IMAGES
# ============================================

plt.figure(figsize=(10,10))

for images, labels in train_ds.take(1):

    for i in range(9):

        ax = plt.subplot(3,3,i+1)

        plt.imshow(images[i].numpy().astype("uint8"))

        plt.title(class_names[labels[i]])

        plt.axis("off")

# plt.show()

# ============================================
# BUILD CNN MODEL
# ============================================

model = models.Sequential([

    # Normalize
    layers.Rescaling(1./255, input_shape=(224,224,3)),

    # CNN Layer 1
    layers.Conv2D(32, (3,3), activation='relu'),
    layers.MaxPooling2D(),

    # CNN Layer 2
    layers.Conv2D(64, (3,3), activation='relu'),
    layers.MaxPooling2D(),

    # CNN Layer 3
    layers.Conv2D(128, (3,3), activation='relu'),
    layers.MaxPooling2D(),

    # Flatten
    layers.Flatten(),

    # Dense Layer
    layers.Dense(128, activation='relu'),

    # Output Layer
    layers.Dense(len(class_names), activation='softmax')
])

# ============================================
# MODEL SUMMARY
# ============================================

model.summary()

# ============================================
# COMPILE MODEL
# ============================================

model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

# ============================================
# TRAIN MODEL
# ============================================

history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=10
)

# ============================================
# SAVE MODEL
# ============================================

model.save("plastic_classifier.h5")

print("\nModel Saved Successfully!")

# ============================================
# ACCURACY GRAPH
# ============================================

plt.figure(figsize=(12,5))

# Accuracy Graph
plt.subplot(1,2,1)

plt.plot(history.history['accuracy'])

plt.plot(history.history['val_accuracy'])

plt.title("Accuracy")

plt.xlabel("Epoch")

plt.ylabel("Accuracy")

plt.legend(['Train','Validation'])

# Loss Graph
plt.subplot(1,2,2)

plt.plot(history.history['loss'])

plt.plot(history.history['val_loss'])

plt.title("Loss")

plt.xlabel("Epoch")

plt.ylabel("Loss")

plt.legend(['Train','Validation'])

# plt.show()

# ============================================
# TEST IMAGE PREDICTION
# ============================================

# Put test image path here
test_image_path = os.path.join(dataset_path, "test.jpg")

# Load Image
img = image.load_img(test_image_path, target_size=(224,224))

# Convert to array
img_array = image.img_to_array(img)

# Expand dimensions
img_array = np.expand_dims(img_array, axis=0)

# Predict
prediction = model.predict(img_array)

# Predicted Class
predicted_class = class_names[np.argmax(prediction)]

# Confidence
confidence = np.max(prediction) * 100

print("\nPrediction:", predicted_class)

print("Confidence:", round(confidence,2), "%")

# Show Image
plt.imshow(img)

plt.title(f"Prediction: {predicted_class}")

plt.axis("off")

# plt.show()