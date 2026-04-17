
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import joblib
import random

app = Flask(__name__)
CORS(app)

# -----------------------------
# LOAD MODELS
# -----------------------------
cases_model = joblib.load("models/cases_model.pkl")
risk_model = joblib.load("models/risk_model.pkl")

le_region = joblib.load("models/le_region.pkl")
le_disease = joblib.load("models/le_disease.pkl")
le_risk = joblib.load("models/le_risk.pkl")

# -----------------------------
# SIMULATED DATA (AUTO)
# -----------------------------
def get_population(region):
    return random.randint(500000, 5000000)

def get_environment():
    rainfall = random.uniform(500, 2000)
    temperature = random.uniform(15, 35)
    return rainfall, temperature

import os
import json

# User data storage
USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

# -----------------------------
# HOME ROUTE
# -----------------------------
@app.route("/")
def home():
    return "AI Health Intelligence System Running 🚀"

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    users = load_users()
    if username in users:
        return jsonify({"error": "User already exists"}), 400

    users[username] = {"email": email, "password": password}
    save_users(users)
    return jsonify({"message": "Registration successful"})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    users = load_users()
    if username not in users or users[username]["password"] != password:
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"message": "Login successful", "username": username})

# -----------------------------
# MAIN PREDICTION
# -----------------------------
@app.route("/predict_all", methods=["POST"])
def predict_all():
    try:
        data = request.json
        disease_name = data.get("disease")
        year = int(data.get("year"))

        # Load all counties from LabelEncoder
        counties = le_region.classes_
        
        results = {}

        for county in counties:
            # AUTO DATA
            population = get_population(county)
            rainfall, temperature = get_environment()

            # ENCODE
            region = le_region.transform([county])[0]
            disease = le_disease.transform([disease_name])[0]

            # -----------------------------
            # MODEL 1 → CASES
            # -----------------------------
            features_cases = np.array([[
                region, year, disease, population, rainfall, temperature
            ]])
            predicted_cases = cases_model.predict(features_cases)[0]

            # -----------------------------
            # MODEL 2 → RISK
            # -----------------------------
            features_risk = np.array([[
                region, year, disease, population, rainfall, temperature, predicted_cases
            ]])
            risk_encoded = risk_model.predict(features_risk)[0]
            risk = le_risk.inverse_transform([risk_encoded])[0]

            results[county] = {
                "cases": int(predicted_cases),
                "risk": risk
            }

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.json

        region_name = data["region"]
        disease_name = data["disease"]
        year = int(data["year"])

        # AUTO DATA
        population = get_population(region_name)
        rainfall, temperature = get_environment()

        # ENCODE
        region = le_region.transform([region_name])[0]
        disease = le_disease.transform([disease_name])[0]

        # -----------------------------
        # MODEL 1 → CASES
        # -----------------------------
        features_cases = np.array([[
            region, year, disease, population, rainfall, temperature
        ]])

        predicted_cases = cases_model.predict(features_cases)[0]

        # -----------------------------
        # MODEL 2 → RISK
        # -----------------------------
        features_risk = np.array([[
            region, year, disease, population, rainfall, temperature, predicted_cases
        ]])

        risk_encoded = risk_model.predict(features_risk)[0]
        risk = le_risk.inverse_transform([risk_encoded])[0]

        # -----------------------------
        # INSIGHTS (UPGRADE 🔥)
        # -----------------------------
        trend = random.choice(["Increasing", "Stable", "Decreasing"])

        beds = int(predicted_cases * 0.1)
        staff = int(beds / 2)

        # ALERT
        alert = ""
        if risk == "High":
            alert = "⚠️ High outbreak risk detected!"

        # RECOMMENDATION
        if disease_name == "Malaria" and risk == "High":
            recommendation = "Urgently distribute mosquito nets and fumigate."
        elif disease_name == "Cholera" and risk == "High":
            recommendation = "Improve water sanitation immediately."
        elif disease_name == "Tuberculosis" and risk == "High":
            recommendation = "Increase TB screening and treatment programs."
        else:
            recommendation = "Maintain monitoring and preventive measures."

        return jsonify({
            "cases": int(predicted_cases),
            "risk": risk,
            "trend": trend,
            "beds": beds,
            "staff": staff,
            "alert": alert,
            "recommendation": recommendation
        })

    except Exception as e:
        return jsonify({"error": str(e)})

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)

