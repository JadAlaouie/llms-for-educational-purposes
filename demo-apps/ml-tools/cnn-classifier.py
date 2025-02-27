import streamlit as st
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
from tensorflow.keras.utils import to_categorical
from PIL import Image
import os

# --------------------------
# Helper Functions
# --------------------------
def load_and_preprocess_image(file, img_size):
    """
    Open an image file, convert to RGB, resize, and normalize the pixel values.
    """
    img = Image.open(file).convert("RGB")
    img = img.resize(img_size)
    img_array = np.array(img) / 255.0  # Normalize pixels to [0,1]
    return img_array

# --------------------------
# App Config and Styling
# --------------------------
st.set_page_config(page_title="Simple CNN Classifier", layout="wide")
st.markdown(
    """
    <style>
    .big-font { font-size:2rem !important; }
    .center { display: flex; justify-content: center; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Simple CNN Classifier Trainer")
st.markdown("This app lets you **train a simple CNN** on multiple classes of images and then use it to classify a new image. Use the tabs below to switch between training and prediction.")

# Define a common image size for training and prediction
IMG_SIZE = (64, 64)  # (width, height)

# --------------------------
# Create Tabs for Better Organization
# --------------------------
tab_train, tab_predict = st.tabs(["Train Model", "Classify Image"])

# ==========================
# TRAINING TAB
# ==========================
with tab_train:
    st.header("Training")
    st.markdown("First, set the **number of classes** (minimum 2). For each class, provide a name and upload images.")

    # Choose the number of classes
    num_classes = st.number_input("Number of Classes", min_value=2, value=2, step=1, key="num_classes")
    
    # Create an expander for each class for neat organization
    class_data = []  # Will store tuples of (class_name, list_of_files)
    for i in range(int(num_classes)):
        with st.expander(f"Class {i+1} Settings", expanded=True):
            class_name = st.text_input(f"Name for Class {i+1}", value=f"Class {i+1}", key=f"class_name_{i}")
            files = st.file_uploader(
                f"Upload images for {class_name}",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=True,
                key=f"class_files_{i}"
            )
            if files:
                st.image(
                    [Image.open(file) for file in files],
                    width=120,
                    caption=[class_name for _ in files],
                )
            class_data.append((class_name, files))
    
    # Check if every class has at least one image uploaded
    all_uploaded = all(len(files) > 0 for _, files in class_data)
    
    if all_uploaded:
        st.markdown("### Preparing Training Data...")
        data = []
        labels = []
        class_names = []
        
        for idx, (class_name, files) in enumerate(class_data):
            class_names.append(class_name)
            for file in files:
                img_array = load_and_preprocess_image(file, IMG_SIZE)
                data.append(img_array)
                labels.append(idx)  # Use index as label
        
        data = np.array(data)
        labels = np.array(labels)
        
        # Convert labels to one-hot encoding
        labels_cat = to_categorical(labels, num_classes=int(num_classes))
        
        st.success(f"Total Training Samples: {len(data)}")
        
        # Shuffle the training data
        indices = np.arange(len(data))
        np.random.shuffle(indices)
        data = data[indices]
        labels_cat = labels_cat[indices]
        
        if st.button("Train Model"):
            with st.spinner("Training the model... Please wait."):
                # Define a simple CNN model
                model = Sequential([
                    Conv2D(32, (3, 3), activation='relu', input_shape=(IMG_SIZE[1], IMG_SIZE[0], 3)),
                    MaxPooling2D((2, 2)),
                    Conv2D(64, (3, 3), activation='relu'),
                    MaxPooling2D((2, 2)),
                    Flatten(),
                    Dense(64, activation='relu'),
                    Dense(int(num_classes), activation='softmax')
                ])
                model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
                
                # Train the model (adjust epochs/batch_size as needed)
                history = model.fit(data, labels_cat, epochs=5, batch_size=8, verbose=0)
                
                final_loss = history.history['loss'][-1]
                final_acc = history.history['accuracy'][-1]
                
            st.success("**Training complete!**")
            st.markdown(f"**Final Loss:** {final_loss:.4f}  |  **Final Accuracy:** {final_acc:.4f}")
            
            # Save the trained model in the 'models' directory
            os.makedirs("models", exist_ok=True)
            model_path = os.path.join("models", "my_model.h5")
            model.save(model_path)
            
            # Store the trained model and class names in session_state for later use
            st.session_state['model'] = model
            st.session_state['class_names'] = class_names

            # Provide a download button for the saved model
            with open(model_path, "rb") as f:
                st.download_button(
                    label="Download Model",
                    data=f.read(),
                    file_name="my_model.h5",
                    mime="application/octet-stream"
                )
    else:
        st.info("Please upload images for **every class** to begin training.")

# ==========================
# PREDICTION TAB
# ==========================
with tab_predict:
    st.header("Image Classification")
    st.markdown("Upload an image below and click to see the model's prediction for each class.")
    
    uploaded_file = st.file_uploader(
        "Upload an image to classify",
        type=["png", "jpg", "jpeg"],
        key="predict"
    )
    
    if uploaded_file:
        # Display the uploaded image
        img = Image.open(uploaded_file).convert("RGB")
        st.image(img, caption="Uploaded Image", width=200)
        
        # Preprocess the image for prediction
        img = img.resize(IMG_SIZE)
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
        
        if 'model' in st.session_state:
            model = st.session_state['model']
            predictions = model.predict(img_array)[0]
            
            # Get class names; if not available, default to Class 1, Class 2, etc.
            class_names = st.session_state.get('class_names', [f"Class {i+1}" for i in range(len(predictions))])
            
            st.markdown("### Prediction Results:")
            # Display predictions as a list
            for idx, prob in enumerate(predictions):
                st.markdown(f"**{class_names[idx]}:** {prob*100:.2f}%")
                st.progress(int(prob*100))
        else:
            st.warning("The model hasn't been trained yet. Please switch to the **Train Model** tab and train the model first.")
