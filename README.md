# Loan Approval Prediction API

This project deploys an already trained Loan Approval Prediction model (RandomForestClassifier) as a FastAPI service, containerized using Docker. The API loads the pre-trained `loan_model.pkl` and makes loan approval predictions based on applicant characteristics.

## Project Structure

```text
Loan_Approval_API/
│
├── app.py                # FastAPI endpoints and prediction logic
├── loan_model.pkl        # Pre-trained machine learning model
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container configuration
├── README.md             # Project documentation and deployment instructions
├── sample_input.json     # Sample input request body
├── sample_output.json    # Sample response output body
└── dataset/
    └── loan_data.csv     # Reference dataset
```

## API Specifications

### 1. API Status Endpoint
* **Method:** `GET`
* **Path:** `/`
* **Response:**
  ```json
  {
    "status": "healthy",
    "message": "Loan Approval Prediction API is online"
  }
  ```

### 2. Predict Endpoint
* **Method:** `POST`
* **Path:** `/predict`
* **Request Body Schema (JSON):**
  * `Gender` (int): 1 for Male, 0 for Female.
  * `Married` (int): 1 for Yes, 0 for No.
  * `Education` (int): 1 for Graduate, 0 for Not Graduate.
  * `ApplicantIncome` (float): Monthly income of the applicant.
  * `LoanAmount` (float): Requested loan amount in thousands.
  * `Credit_History` (int): Credit history meets guidelines: 1 for Yes, 0 for No.
* **Response Body Schema (JSON):**
  * `prediction` (str): `"Approved"` or `"Rejected"`.

---

## Local Execution Instructions

### Step 1: Install Dependencies
Create a virtual environment (optional but recommended) and run:
```bash
pip install -r requirements.txt
```

### Step 2: Start FastAPI
Launch the server in auto-reload mode:
```bash
uvicorn app:app --reload
```

### Step 3: Open Swagger UI
Open your browser and navigate to the interactive API docs:
* http://127.0.0.1:8000/docs

---

## Docker Execution Instructions

### Step 1: Build Docker Image
Build the container image tagged as `loan-api`:
```bash
docker build -t loan-api .
```

### Step 2: Run Docker Container
Run the container on port `8000`:
```bash
docker run -p 8000:8000 loan-api
```
The API will be available at http://localhost:8000.

---

## Testing the API

### Curl Example
Run this command from your terminal or command prompt:
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d "{\"Gender\": 1, \"Married\": 1, \"Education\": 1, \"ApplicantIncome\": 5000, \"LoanAmount\": 150, \"Credit_History\": 1}"
```

### Expected Output
```json
{
  "prediction": "Approved"
}
```
