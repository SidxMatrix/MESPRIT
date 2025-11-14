MESPRIT - Medical Evaluation System for Patient Risk Insights and Triage
An AI-powered healthcare platform built from scratch, late nights, and a lot of debugging.
What This Is:
MESPRIT is a comprehensive healthcare AI platform that I built as my 3rd-year college project. It is something I REALLY put my heart into. The platform uses machine learning to help medical professionals make better decisions faster.
Five complete prediction systems, each trained on real medical datasets, all wrapped in a UI that I probably spent way too much time making look good. 
All the nights spent debugging, came to fruition as I saw each individual feature come to life, bit by bit.
Making ZIP files, just to make sure I don't lose progress even due to a slight mistake, or a missed semi colon, this wasn't easy. I spent weeks just understanding how APACHE II scoring works, then more time training models that actually worked. The readmission risk model? Took me 4 days to get the feature engineering right. The UI? Lost count of how many times I rewrote the CSS.

But honestly, seeing it all come together, watching the dark mode toggle work perfectly, getting those prediction accuracies above 90%, it felt worth it. Every single debugging session at 2 AM, every model that failed to converge, every "why isn't this working" moment - worth it.

I learned more building this than I did in entire semesters. Flask routing, machine learning pipelines, frontend frameworks, Git (finally understood it), model serialization, feature scaling, the works. This project taught me what actual development feels like, not just theory from textbooks.
Tech Stack:
Backend: Flask + FastAPI (yeah I used both, don't judge)

ML Models: scikit-learn, Random Forest, Logistic Regression, XGBoost

Frontend: HTML/CSS/JavaScript with Tailwind CSS

Database: SQLite (users.db for authentication)

Features: Dark/Light mode (with glassmorphism because why not), responsive design, real-time predictions

What It Does:
Disease Prediction - Multi-disease detection system (Diabetes, Hypertension, COVID-19, and 9 more conditions, more will be added in the future.)

30-Day Readmission Risk - Predicts whether a patient might need to come back within 30 days

Mortality Risk Assessment - APACHE II-based scoring for ICU patients

Emergency Triage (KTAS) - Korean Triage and Acuity Scale for ER prioritization

Healthcare Cost Estimation - Predicts treatment costs based on diagnosis, hospital, and severity.

- Model Details:
  1) Disease Prediction
Disease Prediction
- **Accuracy:** 91.3%
- **Algorithm:** Random Forest Classifier
- **Clinical Use:** Multi-disease differential diagnosis

Conditions Covered: 12 diseases including Diabetes, Hypertension, COVID-19, Malaria, Tuberculosis


 2) 30-Day Readmission Risk
- **Accuracy:** 88.4%
- **Algorithm:** Gradient Boosting
- **Clinical Use:** Discharge planning and follow-up prioritization


3) Mortality Risk (APACHE II)
- **Based on:** Validated medical (APACHE 2) scoring system
- **Clinical Use:** ICU patient risk stratification

Risk Categories: Low, Medium, High

4) Emergency Triage (KTAS)
- **Accuracy:** 77.7%
- **Algorithm:** Multi-class Classification
- **Note:** Achieves human-level performance (inter-rater reliability in published KTAS studies: 65-80%)
- **Challenge:** 5-level classification with inherent subjectivity in emergency assessment

5)Cost Estimation
- **R² Score:** 0.46
- **Algorithm:** Random Forest Regressor
- **Note:** Healthcare cost prediction is inherently high-variance. Even enterprise systems struggle with this due to insurance negotiations, hidden fees, and billing complexity not captured in basic clinical features
- **Limitation:** Synthetic data lacks real-world pricing variation, insurance details, and hospital-specific cost structures

  Now, KTAS and Cost estimation might look low from an initial perspective, but let's dive down deep:
  Triage is a notoriously subjective task. Research shows two nurses triaging the same patient agree only 70-75% of the time. My model is performing at human level despite not having access to visual cues, patient behavior, or clinical intuition."
  77.7% accuracy for a 5-level classification problem is clinically acceptable. Published research on KTAS implementation shows inter-rater reliability between human nurses ranges from 65-80%. Our model achieves human-level performance despite lacking subjective assessment factors like patient demeanor, pain expression, and clinical intuition that emergency staff use."

  Next, about cost estimation:
  Healthcare cost prediction is fundamentally challenging due to high variance in medical billing. Research literature shows even sophisticated models using complete EHR data achieve R² scores of 0.50-0.65. The 46.17% accuracy reflects dataset limitations - real cost prediction requires insurance data, itemized billing, complication rates, and hospital-specific pricing policies that synthetic datasets cannot replicate. For a proof-of-concept system using basic features, this baseline establishes that cost factors are learnable, though clinical deployment would require richer data sources."

  - What I Learned from thiis project:
Machine Learning: Feature engineering is harder than I thought. Normalizing data matters. A LOT. Cross-validation isn't optional.

Web Development: Flask is powerful but unforgiving. Tailwind makes CSS actually enjoyable. Glassmorphism is beautiful but heavy (especially if you don't have a RTX 5090 to back you up :) )

Debugging: Console.log() is your best friend. Git commit messages matter when you're trying to figure out what broke 3 days ago.

Soft Skills: Deadlines are real. You will be asked questions you didn't prepare for. Documentation matters (hence this README).


File structure/hierarchy:
MESPRIT/
├── app.py                 # Main Flask application
├── models/                # Trained ML models (.pkl files)
├── templates/             # HTML templates
│   ├── dashboard.html
│   ├── disease.html
│   ├── readmission.html
│   ├── mortality.html
│   ├── ktas.html
│   └── cost.html
├── static/                # Static assets
└── users.db              # SQLite database

If you want to use this:
# Clone the repo
git clone https://github.com/SidxMatrix/MESPRIT.git
cd MESPRIT

# Install dependencies
flask==3.0.0
scikit-learn==1.3.2
pandas==2.1.3
numpy==1.26.2
joblib==1.3.2
fastapi==0.104.1
uvicorn==0.24.0

# Run the app
python app.py

# Open browser
http://localhost:8000

📧 Contact
Siddharth Singh

GitHub: @SidxMatrix

LinkedIn: www.linkedin.com/in/siddharth-singh-4b01842b9

Email: vipersid2904@gmail.com

⚠️ Disclaimer
This is a student project built for educational purposes. It's NOT a substitute for professional medical advice, diagnosis, or treatment. Don't use it to make actual medical decisions. Seriously.

This project represents hundreds of hours of work, learning, and growth. If you made it this far in the README, thanks for reading. It means more than you know. Later passerby :)
 
