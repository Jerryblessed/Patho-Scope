# 🧠 Patho-Scope AI

An Intelligent Digital Workbench for Histopathology Analysis. Patho-Scope AI uses a locally trained TensorFlow model to classify histopathology images into five cancer types, then leverages Google Gemini for AI-generated medical explanations. It is built as a lightweight Flask web application with MongoDB storage.

---

## 📦 Installation Guide (Flask Version)

### 1. Clone the Repository

```bash
git clone https://github.com/Jerryblessed/Patho-Scope.git
cd Patho-Scope
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the root directory:

```env
MONGO_URI=your_mongodb_connection_string
GEMINI_API_KEY=your_google_gemini_api_key
```

### 5. Add the Trained Model

Ensure the model file `histo_densenet121_model.keras` is in the project root directory.

### 6. Run the Flask App

```bash
flask run
```

Visit the app at: [http://localhost:5000](http://localhost:5000)

---

You're now ready to use Patho-Scope AI for AI-assisted histopathology diagnosis.
