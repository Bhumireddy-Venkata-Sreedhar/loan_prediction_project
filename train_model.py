"""
train_model.py — Trains a RandomForestClassifier on a realistic synthetic loan dataset.

Key approval factors:
  1. Credit History (strongest factor)
  2. Loan-to-Income ratio (high loan relative to income → rejection)
  3. Education level
  4. Marital status & gender (minor factors)

Target accuracy: ≥ 80% on a held-out test split.
"""

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report

# Reproducibility
np.random.seed(42)

# ──────────────────────────────────────────────
# 1. Generate a large, realistic synthetic dataset
# ──────────────────────────────────────────────
N = 2000  # number of samples

gender = np.random.choice([0, 1], size=N, p=[0.4, 0.6])           # 0=Female, 1=Male
married = np.random.choice([0, 1], size=N, p=[0.35, 0.65])        # 0=Single, 1=Married
education = np.random.choice([0, 1], size=N, p=[0.3, 0.7])        # 0=Not Grad, 1=Grad
credit_history = np.random.choice([0, 1], size=N, p=[0.25, 0.75]) # 0=Bad, 1=Good

# Income: uniform distribution to cover all ranges ($500 to $50,000)
applicant_income = np.random.uniform(500, 50000, size=N).astype(int)

# Loan amount: uniform distribution to cover all ranges ($10k to $1,000k)
loan_amount = np.random.uniform(10, 1000, size=N).astype(int)

# ──────────────────────────────────────────────
# 2. Define realistic approval logic
# ──────────────────────────────────────────────
# The key ratio: loan_amount (in $1000s) vs monthly income
# If someone earning $5000/mo requests a $500k loan, that's very risky.
loan_to_income_ratio = (loan_amount * 1000) / applicant_income

approval_score = np.zeros(N, dtype=float)

# Credit history is the #1 factor (worth ~40 points)
approval_score += credit_history * 40

# Low loan-to-income ratio is good (worth up to ~30 points)
# Ratio < 30 → good, Ratio > 80 → very bad
approval_score += np.clip(30 - (loan_to_income_ratio - 20) * 0.5, -20, 30)

# Education helps (~10 points)
approval_score += education * 10

# Being married slightly helps (~5 points)
approval_score += married * 5

# Higher income generally helps (~10 points)
income_factor = np.clip((applicant_income - 2000) / 8000, 0, 1) * 10
approval_score += income_factor

# Add some noise for realism
approval_score += np.random.normal(0, 8, size=N)

# Threshold: score ≥ 50 → Approved (1), else Rejected (0)
loan_status = (approval_score >= 50).astype(int)

print(f"Generated {N} samples")
print(f"Approved: {loan_status.sum()} ({loan_status.mean()*100:.1f}%)")
print(f"Rejected: {N - loan_status.sum()} ({(1-loan_status.mean())*100:.1f}%)")

# ──────────────────────────────────────────────
# 3. Build DataFrame
# ──────────────────────────────────────────────
df = pd.DataFrame({
    "Gender": gender,
    "Married": married,
    "Education": education,
    "ApplicantIncome": applicant_income,
    "LoanAmount": loan_amount,
    "Credit_History": credit_history,
    "Loan_To_Income_Ratio": (loan_amount * 1000) / applicant_income,
    "Loan_Status": loan_status
})

# Also save a readable CSV for reference
df_readable = df.copy()
df_readable["Gender"] = df_readable["Gender"].map({0: "Female", 1: "Male"})
df_readable["Married"] = df_readable["Married"].map({0: "No", 1: "Yes"})
df_readable["Education"] = df_readable["Education"].map({0: "Not Graduate", 1: "Graduate"})
df_readable["Loan_Status"] = df_readable["Loan_Status"].map({0: "N", 1: "Y"})
df_readable.to_csv("dataset/loan_data.csv", index=False)
print("\nSaved updated dataset/loan_data.csv")

# ──────────────────────────────────────────────
# 4. Train / Test Split
# ──────────────────────────────────────────────
X = df[["Gender", "Married", "Education", "ApplicantIncome", "LoanAmount", "Credit_History", "Loan_To_Income_Ratio"]]
y = df["Loan_Status"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

print(f"\nTrain size: {len(X_train)}, Test size: {len(X_test)}")

# ──────────────────────────────────────────────
# 5. Train RandomForestClassifier with tuned hyperparameters
# ──────────────────────────────────────────────
model = GradientBoostingClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.1,
    min_samples_split=10,
    min_samples_leaf=5,
    subsample=0.8,
    random_state=42
)

model.fit(X_train, y_train)

# ──────────────────────────────────────────────
# 6. Evaluate
# ──────────────────────────────────────────────
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"\n{'='*50}")
print(f"  Test Accuracy: {accuracy*100:.2f}%")
print(f"{'='*50}")
print(f"\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=["Rejected", "Approved"]))

# Cross-validation for robustness check
cv_scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")
print(f"5-Fold Cross-Validation Accuracy: {cv_scores.mean()*100:.2f}% (±{cv_scores.std()*100:.2f}%)")

# ──────────────────────────────────────────────
# 7. Feature importance analysis
# ──────────────────────────────────────────────
feature_names = X.columns.tolist()
importances = model.feature_importances_
print(f"\nFeature Importances:")
for name, imp in sorted(zip(feature_names, importances), key=lambda x: -x[1]):
    print(f"  {name:20s}: {imp:.4f}")

# ──────────────────────────────────────────────
# 8. Sanity checks — high loan amounts should be rejected
# ──────────────────────────────────────────────
print(f"\n{'='*50}")
print("Sanity Checks:")
print(f"{'='*50}")

test_cases = [
    {"desc": "Low income, HIGH loan, bad credit",   "data": [1, 1, 1, 3000, 500, 0]},
    {"desc": "Low income, HIGH loan, good credit",   "data": [1, 1, 1, 3000, 500, 1]},
    {"desc": "High income, low loan, good credit",   "data": [1, 1, 1, 15000, 100, 1]},
    {"desc": "High income, HIGH loan, good credit",  "data": [1, 1, 1, 15000, 600, 1]},
    {"desc": "Low income, low loan, good credit",    "data": [0, 0, 1, 5000, 80, 1]},
    {"desc": "Med income, med loan, bad credit",     "data": [1, 0, 0, 5000, 150, 0]},
]

for tc in test_cases:
    # tc["data"] is [Gender, Married, Education, ApplicantIncome, LoanAmount, Credit_History]
    # We need to append the ratio: (LoanAmount * 1000) / ApplicantIncome
    row_data = list(tc["data"])
    income = row_data[3]
    loan = row_data[4]
    ratio = (loan * 1000) / income
    row_data.append(ratio)
    
    test_df = pd.DataFrame([row_data], columns=feature_names)
    pred = model.predict(test_df)[0]
    result = "Approved" if pred == 1 else "Rejected"
    print(f"  {tc['desc']:45s} -> {result}")

# ──────────────────────────────────────────────
# 9. Save the model
# ──────────────────────────────────────────────
joblib.dump(model, "loan_model.pkl")
print(f"\n[OK] Model saved to loan_model.pkl")
print(f"[OK] Accuracy: {accuracy*100:.2f}% (target was >=60%)")
