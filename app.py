import os
import json
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Initialize FastAPI application
app = FastAPI(
    title="Loan Approval Prediction API",
    description="API to predict loan approval using an existing trained RandomForest model",
    version="1.0.0"
)

# Define the model path
MODEL_PATH = "loan_model.pkl"

# Check if model file exists
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file '{MODEL_PATH}' not found in the workspace.")

# Load the trained RandomForestClassifier model
try:
    model = joblib.load(MODEL_PATH)
except Exception as e:
    raise RuntimeError(f"Error loading the machine learning model: {e}")

# Define schema for input features
class LoanRequest(BaseModel):
    Gender: int = Field(..., description="Gender of applicant: 1 for Male, 0 for Female", ge=0, le=1)
    Married: int = Field(..., description="Marital status: 1 for Married, 0 for Unmarried/Single", ge=0, le=1)
    Education: int = Field(..., description="Education level: 1 for Graduate, 0 for Not Graduate", ge=0, le=1)
    ApplicantIncome: float = Field(..., description="Monthly income of the applicant", gt=0)
    LoanAmount: float = Field(..., description="Requested loan amount in thousands", gt=0)
    Credit_History: int = Field(..., description="Credit history meets guidelines: 1 for Yes, 0 for No", ge=0, le=1)

    model_config = {
        "json_schema_extra": {
            "example": {
                "Gender": 1,
                "Married": 1,
                "Education": 1,
                "ApplicantIncome": 5000.0,
                "LoanAmount": 150.0,
                "Credit_History": 1
            }
        }
    }

# Define schema for prediction response
class PredictionResponse(BaseModel):
    prediction: str = Field(..., description="Loan prediction result: 'Approved' or 'Rejected'")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Serves an inline SVG favicon to avoid 404 errors."""
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        '<rect width="32" height="32" rx="6" fill="#6c5ce7"/>'
        '<text x="16" y="24" font-size="22" font-family="Arial,sans-serif" '
        'fill="white" text-anchor="middle" font-weight="bold">$</text>'
        '</svg>'
    )
    return Response(content=svg, media_type="image/svg+xml")

@app.get("/")
def home():
    """
    Serves the frontend application if it exists, otherwise returns API status.
    """
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {
        "status": "healthy",
        "message": "Loan Approval Prediction API is online"
    }

@app.post("/predict", response_model=PredictionResponse)
def predict(request: LoanRequest):
    """
    Accepts applicant details, runs model inference, and returns 'Approved' or 'Rejected'.
    """
    try:
        # Convert request to pandas DataFrame in order to match the feature names
        # and order that the model was trained on
        input_df = pd.DataFrame([{
            "Gender": request.Gender,
            "Married": request.Married,
            "Education": request.Education,
            "ApplicantIncome": request.ApplicantIncome,
            "LoanAmount": request.LoanAmount,
            "Credit_History": request.Credit_History,
            "Loan_To_Income_Ratio": (request.LoanAmount * 1000) / request.ApplicantIncome
        }])

        # Perform the prediction
        # model.predict returns an array, we extract the first element
        prediction_value = model.predict(input_df)[0]

        # Map prediction (1 = Y / Approved, 0 = N / Rejected)
        result = "Approved" if prediction_value == 1 else "Rejected"

        return PredictionResponse(prediction=result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Inference error: {str(e)}"
        )

@app.get("/api/data")
def get_data():
    """
    Loads dataset/loan_data.csv and returns statistical aggregates.
    """
    csv_path = os.path.join("dataset", "loan_data.csv")
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Dataset file not found")
    
    try:
        df = pd.read_csv(csv_path)
        
        # Calculate summary statistics
        total_records = len(df)
        
        # Clean Loan_Status values (Y/N)
        approved_count = int((df["Loan_Status"].str.upper() == "Y").sum())
        rejected_count = int((df["Loan_Status"].str.upper() == "N").sum())
        
        # Avg income & avg loan amount
        avg_income = float(df["ApplicantIncome"].mean())
        avg_loan = float(df["LoanAmount"].mean())
        
        return {
            "stats": {
                "total_records": total_records,
                "approved_count": approved_count,
                "rejected_count": rejected_count,
                "avg_income": avg_income,
                "avg_loan": avg_loan
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading dataset: {str(e)}")

@app.get("/api/sample-input")
def get_sample_input():
    """
    Serves the sample_input.json raw content.
    """
    try:
        with open("sample_input.json", "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading sample input: {str(e)}")

@app.get("/api/sample-output")
def get_sample_output():
    """
    Serves the sample_output.json raw content.
    """
    try:
        with open("sample_output.json", "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading sample output: {str(e)}")

# Mount the static directory to serve HTML/CSS/JS assets
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
else:
    os.makedirs("static", exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Reload uvicorn server trigger comment (updated model reload)

