import os
import json
import base64
from flask import Flask, request, render_template, jsonify, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import google.generativeai as genai
from PIL import Image
import numpy as np
from tensorflow.keras.models import load_model
from datetime import datetime

# --- 1. CONFIGURATION ---
# Hardcoded keys as requested
MONGO_URI = "mongodb+srv://teslasacademicgroup:oDELC6JXdmB8w84Q@cluster0.gvzgh2h.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = 'PathoScopeDB'
COLLECTION_NAME = 'analyses'

# Google Gemini AI Configuration
# !!! IMPORTANT: You MUST replace this with your own valid Google API key. !!!
GOOGLE_API_KEY = "AIzaSyBU_3NNernMnnKXgASt2rurUbnH8wfZsP0"
MODEL_NAME = "gemini-1.5-flash-latest"

# --- 2. INITIALIZATION ---
app = Flask(__name__)

# Database Connection
try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    print("MongoDB connection successful.")
except Exception as e:
    print(f"MongoDB connection failed: {e}")

# Gemini AI Model Initialization
ai_model = None
try:
    if not GOOGLE_API_KEY or "PASTE_YOUR_REAL" in GOOGLE_API_KEY:
        raise ValueError("Google API Key is a placeholder. Please replace it.")
    genai.configure(api_key=GOOGLE_API_KEY)
    ai_model = genai.GenerativeModel(MODEL_NAME)
    print("Gemini AI Core Initialized.")
except Exception as e:
    print(f"CRITICAL: Gemini AI Core failed to initialize: {e}")

# Histopathology Model Initialization
try:
    histo_model = load_model('histo_densenet121_model.keras')
    
    CLASSES = [
    'Colon Adenocarcinoma',     # colon_aca
    'Colon Benign',             # colon_n
    'Lung Adenocarcinoma',      # lung_aca
    'Lung Benign',              # lung_n
    'Lung Squamous Cell Carcinoma'  # lung_scc
]

    print("Histopathology model loaded successfully.")
except Exception as e:
    histo_model = None
    print(f"CRITICAL: Failed to load .keras model: {e}")

# --- 3. HELPER FUNCTIONS ---
def preprocess_image(image_stream):
    """Resizes and normalizes the image for the model."""
    img = Image.open(image_stream).convert('RGB').resize((224, 224))
    return np.expand_dims(np.array(img) / 255.0, axis=0)

def image_to_base64(image_stream):
    """Converts an image stream to a Base64 string for embedding in HTML."""
    image_stream.seek(0)
    return base64.b64encode(image_stream.read()).decode('utf-8')

# --- 4. BACKEND API & ROUTES ---

@app.route('/')
def index():
    """Renders the main workbench, loading all previous analyses from MongoDB."""
    history = list(collection.find().sort('timestamp', -1))
    # Convert ObjectId to string for Jinja2
    for item in history:
        item['_id'] = str(item['_id'])
    return render_template('index.html', history=history)

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyzes an uploaded image, gets AI insights, and saves to the database."""
    if 'file' not in request.files or not histo_model:
        return jsonify({'error': 'No file or model not loaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        # 1. Preprocess and Classify
        preprocessed_img = preprocess_image(file.stream)
        preds = histo_model.predict(preprocessed_img)[0]
        idx = np.argmax(preds)
        prediction = CLASSES[idx]
        confidence = round(float(preds[idx]) * 100, 2)
        
        # 2. Get AI Explanation
        ai_explanation = "AI Assistant is offline."
        if ai_model:
            prompt = f"""
            You are a helpful AI assistant for a histopathology analysis tool.
            A lung tissue scan has been classified by a model as: **{prediction}** with a confidence of **{confidence}%**.

            Provide a brief, easy-to-understand explanation for a non-expert. Describe what this classification generally means, its typical cell characteristics (in simple terms), and what the general next steps might be (e.g., "Consultation with a specialist is recommended for a definitive diagnosis and treatment plan.").
            Keep the tone professional, calm, and informative. Do not provide a medical diagnosis. Start directly with the explanation.
            """
            response = ai_model.generate_content(prompt)
            ai_explanation = response.text

        # 3. Save to Database
        image_b64 = image_to_base64(file.stream)
        analysis_record = {
            'prediction': prediction,
            'confidence': confidence,
            'image_b64': image_b64,
            'ai_explanation': ai_explanation,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        result = collection.insert_one(analysis_record)
        
        # 4. Prepare and return JSON response
        # Convert ObjectId to string for JSON serialization
        analysis_record['_id'] = str(result.inserted_id)
        return jsonify(analysis_record)

    except Exception as e:
        print(f"Error during analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_analysis/<id>')
def get_analysis(id):
    """Fetches a single analysis record from the database by its ID."""
    try:
        record = collection.find_one({'_id': ObjectId(id)})
        if not record:
            return jsonify({'error': 'Analysis not found'}), 404
        record['_id'] = str(record['_id'])
        return jsonify(record)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete_analysis/<id>')
def delete_analysis(id):
    """Deletes an analysis record from the database."""
    try:
        collection.delete_one({'_id': ObjectId(id)})
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)