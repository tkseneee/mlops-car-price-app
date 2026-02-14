"""
Exercise 5B: Azure Functions Backend
-------------------------------------
Deployed via GitHub Actions on every push to backend/ folder.

Endpoints:
  POST /api/predict  -> JSON prediction
  GET  /api/health   -> Health check
"""

import azure.functions as func
import json
import logging
import pandas as pd
from joblib import load
from custom_transformers import YearToAgeTransformer  # needed for unpickling

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Load pipeline once
pipeline = load("car_price_pipeline.pkl")
logging.info("Pipeline loaded successfully!")


@app.route(route="predict", methods=["POST"])
def predict(req: func.HttpRequest) -> func.HttpResponse:
    """Prediction endpoint. Accepts JSON, returns JSON."""
    try:
        data = req.get_json()

        input_df = pd.DataFrame([{
            "Year": int(data["Year"]),
            "Present_Price": float(data["Present_Price"]),
            "Kms_Driven": int(data["Kms_Driven"]),
            "Fuel_Type": data["Fuel_Type"],
            "Seller_Type": data["Seller_Type"],
            "Transmission": data["Transmission"],
            "Owner": int(data["Owner"]),
        }])

        raw_pred = pipeline.predict(input_df)[0]

        present_price = float(data["Present_Price"])
        lower_bound = 0.4 * present_price
        upper_bound = present_price
        suggested_price = max(lower_bound, min(raw_pred, upper_bound))

        result = {
            "success": True,
            "raw_prediction": round(float(raw_pred), 2),
            "suggested_price": round(float(suggested_price), 2),
            "lower_bound": round(float(lower_bound), 2),
            "upper_bound": round(float(upper_bound), 2),
        }

        return func.HttpResponse(
            json.dumps(result),
            mimetype="application/json",
            status_code=200,
        )

    except Exception as e:
        logging.error(f"Prediction error: {e}")
        return func.HttpResponse(
            json.dumps({"success": False, "error": str(e)}),
            mimetype="application/json",
            status_code=400,
        )


@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint."""
    return func.HttpResponse(
        json.dumps({"status": "healthy", "model": "car_price_pipeline"}),
        mimetype="application/json",
        status_code=200,
    )
