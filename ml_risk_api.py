from flask import Flask, request, jsonify
import xgboost as xgb
import numpy as np
import pickle
import os

app = Flask(__name__)

# Загружаем модель при старте
MODEL_PATH = os.path.join(os.path.dirname(__file__), "risk_model.pkl")
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "model_loaded": True})

@app.route("/score", methods=["POST"])
def score():
    data = request.json
    # Ожидаем: amount, tx_count, is_blacklisted
    try:
        features = np.array([[data["amount"], data["tx_count"], data["is_blacklisted"]]])
    except Exception as e:
        return jsonify({"error": f"Некорректные данные: {e}"}), 400
    # Получаем вероятность мошенничества
    risk_score = float(model.predict_proba(features)[0][1])
    return jsonify({"risk_score": risk_score})

if __name__ == "__main__":
    # Запуск на localhost:5001
    app.run(host="0.0.0.0", port=5001) 