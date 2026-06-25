// JavaScript Dashboard Controller for LoanLENS

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const themeToggleBtn = document.getElementById("theme-toggle");
    const bodyEl = document.body;
    
    // Sliders
    const incomeInput = document.getElementById("input-income");
    const incomeDisplay = document.getElementById("income-val");
    const loanInput = document.getElementById("input-loan");
    const loanDisplay = document.getElementById("loan-val");
    
    // Form and Buttons
    const predictionForm = document.getElementById("prediction-form");
    const btnPredict = document.getElementById("btn-predict");
    const btnLoadSample = document.getElementById("btn-load-sample");
    
    // Results & Debugger
    const resultCard = document.getElementById("prediction-result-card");
    const jsonRequestCode = document.getElementById("json-request-code");
    const jsonResponseCode = document.getElementById("json-response-code");
    
    // JSON files inspector
    const jsonFileInput = document.getElementById("json-file-input");
    const jsonFileOutput = document.getElementById("json-file-output");

    // --- Theme Management ---
    // Read theme from localStorage or default to dark
    const currentTheme = localStorage.getItem("theme") || "dark";
    if (currentTheme === "light") {
        bodyEl.classList.remove("dark-theme");
        bodyEl.classList.add("light-theme");
    }

    themeToggleBtn.addEventListener("click", () => {
        if (bodyEl.classList.contains("dark-theme")) {
            bodyEl.classList.remove("dark-theme");
            bodyEl.classList.add("light-theme");
            localStorage.setItem("theme", "light");
        } else {
            bodyEl.classList.remove("light-theme");
            bodyEl.classList.add("dark-theme");
            localStorage.setItem("theme", "dark");
        }
    });

    // --- Slider Displays ---
    const updateIncomeDisplay = (val) => {
        incomeDisplay.textContent = new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
            maximumFractionDigits: 0
        }).format(val);
    };

    const updateLoanDisplay = (val) => {
        const fullVal = val * 1000;
        const formattedFull = new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
            maximumFractionDigits: 0
        }).format(fullVal);
        loanDisplay.textContent = `$${val}k (${formattedFull})`;
    };

    incomeInput.addEventListener("input", (e) => updateIncomeDisplay(e.target.value));
    loanInput.addEventListener("input", (e) => updateLoanDisplay(e.target.value));

    // Initialize display values
    updateIncomeDisplay(incomeInput.value);
    updateLoanDisplay(loanInput.value);


    // --- Debugger Tab Switcher ---
    const tabButtons = document.querySelectorAll(".debugger-tab");
    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tabButtons.forEach(t => t.classList.remove("active"));
            btn.classList.add("active");
            
            const targetPaneId = btn.getAttribute("data-tab");
            document.querySelectorAll(".tab-pane").forEach(pane => {
                pane.classList.remove("active");
            });
            document.getElementById(targetPaneId).classList.add("active");
        });
    });


    // --- Load Sample Files ---
    const loadSampleJSONFiles = async () => {
        try {
            // Load Sample Input
            const inputRes = await fetch("/api/sample-input");
            if (inputRes.ok) {
                const inputData = await inputRes.json();
                jsonFileInput.textContent = JSON.stringify(inputData, null, 2);
            } else {
                jsonFileInput.textContent = "Error loading sample_input.json";
            }

            // Load Sample Output
            const outputRes = await fetch("/api/sample-output");
            if (outputRes.ok) {
                const outputData = await outputRes.json();
                jsonFileOutput.textContent = JSON.stringify(outputData, null, 2);
            } else {
                jsonFileOutput.textContent = "Error loading sample_output.json";
            }
        } catch (err) {
            console.error("Error loading sample files:", err);
            jsonFileInput.textContent = "Error connecting to server";
            jsonFileOutput.textContent = "Error connecting to server";
        }
    };
    loadSampleJSONFiles();

    // --- Load Stats from API ---
    const loadStats = async () => {
        try {
            const res = await fetch("/api/data");
            if (!res.ok) throw new Error("Could not fetch dataset analytics");
            
            const data = await res.json();
            
            // Populate stats dashboard
            document.getElementById("stat-total-records").textContent = data.stats.total_records;
            
            const appRate = ((data.stats.approved_count / data.stats.total_records) * 100).toFixed(0);
            document.getElementById("stat-approval-rate").textContent = `${appRate}%`;
            
            document.getElementById("stat-avg-income").textContent = new Intl.NumberFormat("en-US", {
                style: "currency",
                currency: "USD",
                maximumFractionDigits: 0
            }).format(data.stats.avg_income);
            
            document.getElementById("stat-avg-loan").textContent = `$${data.stats.avg_loan.toFixed(0)}k`;

        } catch (err) {
            console.error("Error fetching stats:", err);
        }
    };


    // --- Load Sample to Form ---
    btnLoadSample.addEventListener("click", async () => {
        try {
            btnLoadSample.disabled = true;
            const res = await fetch("/api/sample-input");
            if (!res.ok) throw new Error("Could not fetch sample input");
            
            const sample = await res.json();
            
            // Populate form elements
            document.getElementById("input-gender").value = sample.Gender;
            document.getElementById("input-married").value = sample.Married;
            document.getElementById("input-education").value = sample.Education;
            document.getElementById("input-credit").value = sample.Credit_History;
            
            incomeInput.value = sample.ApplicantIncome;
            updateIncomeDisplay(sample.ApplicantIncome);
            
            loanInput.value = sample.LoanAmount;
            updateLoanDisplay(sample.LoanAmount);
            
            // Flash form indicator
            const predictorPanel = document.getElementById("predictor-section");
            predictorPanel.style.borderColor = "var(--color-primary)";
            setTimeout(() => {
                predictorPanel.style.borderColor = "";
            }, 500);

        } catch (err) {
            alert("Error loading sample data: " + err.message);
        } finally {
            btnLoadSample.disabled = false;
        }
    });


    // --- Submit Prediction Form ---
    predictionForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        // Prepare request schema
        const payload = {
            Gender: parseInt(document.getElementById("input-gender").value),
            Married: parseInt(document.getElementById("input-married").value),
            Education: parseInt(document.getElementById("input-education").value),
            ApplicantIncome: parseFloat(incomeInput.value),
            LoanAmount: parseFloat(loanInput.value),
            Credit_History: parseInt(document.getElementById("input-credit").value)
        };

        // Render request payload in JSON debugger
        jsonRequestCode.textContent = JSON.stringify(payload, null, 2);
        
        // Visual state updates
        btnPredict.disabled = true;
        document.querySelector(".state-idle").classList.add("hidden");
        document.querySelector(".state-success").classList.add("hidden");
        document.querySelector(".state-rejected").classList.add("hidden");
        
        // Show loading spinner
        const spinner = document.createElement("div");
        spinner.className = "pulse-ring";
        spinner.id = "inference-spinner";
        resultCard.appendChild(spinner);

        try {
            const response = await fetch("/predict", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            
            // Render response payload in JSON debugger
            jsonResponseCode.textContent = JSON.stringify(data, null, 2);
            
            // Remove spinner
            const activeSpinner = document.getElementById("inference-spinner");
            if (activeSpinner) activeSpinner.remove();

            if (!response.ok) {
                throw new Error(data.detail || "Prediction inference failed");
            }

            // Display approved/rejected badge
            if (data.prediction === "Approved") {
                document.querySelector(".state-success").classList.remove("hidden");
            } else {
                document.querySelector(".state-rejected").classList.remove("hidden");
            }

            // Auto switch debugger tab to Response to see result json
            const responseTab = document.querySelector('[data-tab="tab-response"]');
            if (responseTab) responseTab.click();

        } catch (err) {
            console.error(err);
            const activeSpinner = document.getElementById("inference-spinner");
            if (activeSpinner) activeSpinner.remove();
            
            document.querySelector(".state-idle").classList.remove("hidden");
            jsonResponseCode.textContent = JSON.stringify({ error: err.message }, null, 2);
            alert("Error running prediction: " + err.message);
        } finally {
            btnPredict.disabled = false;
        }
    });


    // --- Clipboard Copy Helper ---
    document.querySelectorAll(".btn-copy").forEach(btn => {
        btn.addEventListener("click", () => {
            const targetId = btn.getAttribute("data-target");
            const codeContent = document.getElementById(targetId).textContent;
            
            navigator.clipboard.writeText(codeContent).then(() => {
                const originalText = btn.textContent;
                btn.textContent = "Copied!";
                btn.classList.add("btn-primary");
                btn.classList.remove("btn-secondary");
                
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.classList.remove("btn-primary");
                    btn.classList.add("btn-secondary");
                }, 1500);
            }).catch(err => {
                console.error("Failed to copy code: ", err);
            });
        });
    });


    // Start execution — load stats
    loadStats();
});
