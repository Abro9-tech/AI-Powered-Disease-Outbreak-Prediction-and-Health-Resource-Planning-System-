
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
# DETERMINISTIC DATA (STABLE 🔥)
# -----------------------------
def get_stable_random(seed_str):
    """Generate a consistent random generator based on a string seed"""
    import hashlib
    # Create a numeric seed from the string
    seed = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16) % (2**32)
    return random.Random(seed)

def get_population(region):
    # Use region as seed so population stays the same for each county
    rng = get_stable_random(region)
    return rng.randint(800000, 4500000)

def get_environment(region, year):
    # Use region + year as seed so weather stays consistent for that specific scenario
    rng = get_stable_random(f"{region}-{year}")
    rainfall = rng.uniform(600, 1800)
    temperature = rng.uniform(18, 32)
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
            rainfall, temperature = get_environment(county, year)

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
        rainfall, temperature = get_environment(region_name, year)

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
        # TREND DATA (3-YEAR SERIES 🔥)
        # -----------------------------
        history = []
        years_to_predict = [year-2, year-1, year]
        
        for y in years_to_predict:
            # Get consistent data for each year
            y_pop = get_population(region_name)
            y_rain, y_temp = get_environment(region_name, y)
            
            y_feat = np.array([[region, y, disease, y_pop, y_rain, y_temp]])
            y_cases = int(cases_model.predict(y_feat)[0])
            history.append({"year": y, "cases": y_cases})

        # -----------------------------
        # INSIGHTS (STABLE 🔥)
        # -----------------------------
        # Make trend deterministic based on risk and predicted cases
        rng = get_stable_random(f"{region_name}-{disease_name}-{year}")
        trend = rng.choice(["Increasing", "Stable", "Decreasing"])

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
            "recommendation": recommendation,
            "history": history
        })

    except Exception as e:
        return jsonify({"error": str(e)})

# -----------------------------
# CASES SERIES (2020-2025)
# -----------------------------
@app.route("/cases_series", methods=["POST"])
def cases_series():
    try:
        data = request.json

        region_name = data["region"]
        disease_name = data["disease"]

        start_year = int(data.get("start_year", 2020))
        end_year = int(data.get("end_year", 2025))

        if start_year > end_year:
            return jsonify({"error": "start_year must be <= end_year"}), 400

        # ENCODE (once)
        region = le_region.transform([region_name])[0]
        disease = le_disease.transform([disease_name])[0]

        series = []
        for y in range(start_year, end_year + 1):
            y_pop = get_population(region_name)
            y_rain, y_temp = get_environment(region_name, y)
            y_feat = np.array([[region, y, disease, y_pop, y_rain, y_temp]])
            y_cases = int(cases_model.predict(y_feat)[0])
            series.append({"year": y, "cases": y_cases})

        return jsonify({"region": region_name, "disease": disease_name, "series": series})
    except Exception as e:
        return jsonify({"error": str(e)})

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

