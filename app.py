from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import pickle
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime
import secrets
import pytz

# Email and password reset imports
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer

# Database connection with timeout
def get_db_connection():
    conn = sqlite3.connect('users.db', timeout=10.0)
    return conn



app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = secrets.token_hex(32)
CORS(app)

# ==================== FLASK-MAIL CONFIGURATION ====================
# ==================== FLASK-MAIL CONFIGURATION ====================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'vipersid2904@gmail.com'  # gmail address for sending emails
app.config['MAIL_PASSWORD'] = 'uuya ofdm bthd gzqz'  # app password
app.config['MAIL_DEFAULT_SENDER'] = 'vipersid2904@gmail.com'  # Same as MAIL_USERNAME
mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)



# ==================== DATABASE SETUP ====================
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  full_name TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS predictions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  model_type TEXT,
                  input_data TEXT,
                  result TEXT,
                  confidence REAL,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()


init_db()


# ==================== LOAD ALL MODELS ====================
print("Loading all models...")
with open('models/MDPv2.pkl', 'rb') as f:
    disease_artifacts = pickle.load(f)
with open('models/readmission_risk_model.pkl', 'rb') as f:
    readmission_artifacts = pickle.load(f)
with open('models/cost_estimation_model.pkl', 'rb') as f:
    cost_artifacts = pickle.load(f)
with open('models/ktas_model.pkl', 'rb') as f:
    ktas_artifacts = pickle.load(f)
print("✓ All models loaded successfully!")


# ==================== AUTHENTICATION ROUTES ====================
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        
        password_hash = generate_password_hash(password)
        
        try:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute('INSERT INTO users (username, email, password_hash, full_name) VALUES (?, ?, ?, ?)',
                     (username, email, password_hash, full_name))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Account created successfully'})
        except sqlite3.IntegrityError:
            return jsonify({'success': False, 'error': 'Username or email already exists'}), 400
    
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT id, password_hash, full_name FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            session['full_name'] = user[2]
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ==================== FORGOT PASSWORD ROUTES ====================
@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Handle forgot password request and send reset email"""
    data = request.json
    email = data.get('email')
    
    # Check if user exists
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT id, username FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        # Don't reveal if email exists for security
        return jsonify({'success': True, 'message': 'If that email exists, a reset link has been sent.'})
    
    # Generate secure token
    token = serializer.dumps(email, salt='reset-password')
    reset_link = url_for('reset_password', token=token, _external=True)
    
    # Send email
    msg = Message("MESPRIT Password Reset Request", 
                  sender=app.config['MAIL_USERNAME'], 
                  recipients=[email])
    msg.body = f"""Hello,

You requested a password reset for your MESPRIT account.

Click the link below to reset your password:
{reset_link}

This link will expire in 1 hour.

If you didn't request this, please ignore this email.

Best regards,
MESPRIT Healthcare AI Team"""
    
    try:
        mail.send(msg)
        return jsonify({'success': True, 'message': 'If that email exists, a reset link has been sent.'})
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to send email. Please try again later.'}), 500


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token verification"""
    try:
        # Verify token (expires after 1 hour)
        email = serializer.loads(token, salt='reset-password', max_age=3600)
    except Exception:
        return "Invalid or expired reset link. Please request a new one from the <a href='/login' style='color: #3b82f6;'>login page</a>.", 400
    
    if request.method == 'POST':
        password = request.form['password']
        pw_hash = generate_password_hash(password)
        
        # Update password in database
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('UPDATE users SET password_hash = ? WHERE email = ?', (pw_hash, email))
        conn.commit()
        conn.close()
        
        return """
        <!DOCTYPE html>
        <html><head><title>Success</title></head>
        <body style='font-family: Arial; text-align: center; padding: 50px; background: linear-gradient(to bottom right, #0f172a, #1e3a8a);'>
            <div style='background: white; padding: 30px; border-radius: 10px; max-width: 400px; margin: auto;'>
                <h2 style='color: #10b981;'>✓ Password Reset Successful!</h2>
                <p>You can now log in with your new password.</p>
                <a href='/login' style='display: inline-block; margin-top: 20px; padding: 10px 20px; background: #3b82f6; color: white; text-decoration: none; border-radius: 5px;'>Go to Login</a>
            </div>
        </body></html>
        """
    
    return render_template('reset_password.html')


# ==================== DASHBOARD & MODEL PAGES ====================
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', 
                          username=session.get('username'),
                          full_name=session.get('full_name'))


@app.route('/models/disease')
def disease_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('disease.html')


@app.route('/models/readmission')
def readmission_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('readmission.html')


@app.route('/models/cost')
def cost_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('cost.html')


@app.route('/models/mortality')
def mortality_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('mortality.html')


@app.route('/models/ktas')
def ktas_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('ktas.html')


# ==================== USER HISTORY ====================
@app.route('/api/user/history')
def get_user_history():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''SELECT model_type, result, confidence, timestamp 
                 FROM predictions WHERE user_id = ? 
                 ORDER BY timestamp DESC LIMIT 10''', (session['user_id'],))
    history = c.fetchall()
    conn.close()
    
    return jsonify({'success': True, 'history': history})


def save_prediction(model_type, input_data, result, confidence=None):
    if 'user_id' in session:
        conn = sqlite3.connect('users.db', timeout=10.0)
        c = conn.cursor()
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')
        clean_input = "Patient assessment"
        c.execute('''INSERT INTO predictions (user_id, model_type, input_data, result, confidence, timestamp)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                 (session['user_id'], model_type, clean_input, result, confidence, current_time))
        conn.commit()
        conn.close()


# ==================== DISEASE PREDICTION ====================
@app.route('/api/disease/predict', methods=['POST'])
def predict_disease():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.json
        patient_data = {
            'Age': data['age'],
            'Gender': data['gender'],
            'Heart_Rate': data['heartrate'],
            'Body_Temperature': data['bodytemperature'],
            'Respiratory_Rate': data['respiratoryrate'],
            'Oxygen_Saturation': data['oxygensaturation'],
            'Systolic_BP': data['systolicbp'],
            'Diastolic_BP': data['diastolicbp'],
            'Smoking_Status': data['smokingstatus'],
            'Alcohol_Use': data['alcoholuse'],
            'Physical_Activity_Level': data['physicalactivitylevel'],
        }
        
        age = data['age']
        if age < 40:
            patient_data['Age_Group'] = "Young"
        elif age < 55:
            patient_data['Age_Group'] = "Middle"
        elif age < 70:
            patient_data['Age_Group'] = "Senior"
        else:
            patient_data['Age_Group'] = "Elderly"

        checked_symptoms = data.get('checkedsymptoms', [])
        for symptom in disease_artifacts['symptom_list']:
            key = f"Has_{symptom.replace(' ', '_')}"
            patient_data[key] = 1 if symptom in checked_symptoms else 0

        patient_df = pd.DataFrame([patient_data])

        for col in disease_artifacts['categorical_columns']:
            if col in patient_df.columns and col in disease_artifacts['label_encoders']:
                try:
                    patient_df[col] = disease_artifacts['label_encoders'][col].transform(patient_df[col].astype(str))
                except:
                    patient_df[col] = 0

        patient_df = patient_df[disease_artifacts['feature_columns']]
        prediction = disease_artifacts['model'].predict(patient_df)[0]
        probabilities = disease_artifacts['model'].predict_proba(patient_df)[0]
        pred_disease = disease_artifacts['disease_encoder'].inverse_transform([prediction])[0]
        confidence = float(probabilities[prediction])

        save_prediction('Disease Prediction', data, pred_disease, confidence)

        all_probs = {disease_artifacts['disease_encoder'].classes_[i]: float(probabilities[i]) for i in range(len(disease_artifacts['disease_encoder'].classes_))}
        sorted_probs = sorted(all_probs.items(), key=lambda x: x[1], reverse=True)

        return jsonify({
            'success': True,
            'predicted_disease': pred_disease,
            'confidence': confidence,
            'all_probabilities': dict(sorted_probs[:5])
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== READMISSION RISK ====================
@app.route('/api/readmission/predict', methods=['POST'])
def predict_readmission():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.json
        patient_data = {
            'Age': data['age'],
            'Gender': data['gender'],
            'Blood_Pressure': data['bloodpressure'],
            'Heart_Rate': data['heartrate'],
            'Body_Temperature': data['bodytemperature'],
            'Respiratory_Rate': data['respiratoryrate'],
            'Oxygen_Saturation': data['oxygensaturation'],
            'Smoking_Status': data['smokingstatus'],
            'Alcohol_Use': data['alcoholuse'],
            'Physical_Activity_Level': data['physicalactivitylevel'],
            'Family_History': data.get('familyhistory', 'No'),
            'Diagnosis': data['diagnosis'],
            'Previous_Admissions': data['previousadmissions'],
            'Length_of_Stay': data['lengthofstay'],
            'Medication_Adherence': data['medicationadherence'],
            'Number_of_Medications': data['numberofmedications'],
            'Support_System': data['supportsystem'],
            'Comorbidities': data['comorbidities'],
            'Risk_Score': data['riskscore']
        }

        patient_df = pd.DataFrame([patient_data])

        for col in readmission_artifacts['categorical_columns']:
            if col in patient_df.columns and col in readmission_artifacts['label_encoders']:
                try:
                    patient_df[col] = readmission_artifacts['label_encoders'][col].transform(patient_df[col].astype(str))
                except:
                    patient_df[col] = 0

        feature_columns = readmission_artifacts.get('feature_columns', list(readmission_artifacts.get('feature_names', [])))
        patient_df = patient_df[feature_columns]

        prediction = readmission_artifacts['model'].predict(patient_df)[0]
        probabilities = readmission_artifacts['model'].predict_proba(patient_df)[0]
        pred_risk = readmission_artifacts['target_encoder'].inverse_transform([prediction])[0]
        confidence = float(probabilities[prediction])

        save_prediction('Readmission Risk', data, pred_risk, confidence)

        all_probs = {readmission_artifacts['target_encoder'].classes_[i]: float(probabilities[i]) for i in range(len(readmission_artifacts['target_encoder'].classes_))}
        sorted_probs = sorted(all_probs.items(), key=lambda x: x[1], reverse=True)

        return jsonify({
            'success': True,
            'predicted_risk': pred_risk,
            'confidence': confidence,
            'all_probabilities': dict(sorted_probs)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== COST ESTIMATION ====================
@app.route('/api/cost/predict', methods=['POST'])
def predict_cost():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.json
        patient_data = {
            'Age': data['age'],
            'Gender': data['gender'],
            'Disease': data['disease'],
            'Hospital_Name': data['hospitalname'],
            'Room_Type': data['roomtype'],
            'Treatment_Type': data['treatmenttype'],
            'Length_of_Stay_(days)': data['lengthofstay'],
            'Severity_Level': data['severitylevel']
        }

        patient_df = pd.DataFrame([patient_data])

        for col in cost_artifacts['categorical_columns']:
            if col in patient_df.columns and col in cost_artifacts['label_encoders']:
                try:
                    patient_df[col] = cost_artifacts['label_encoders'][col].transform(patient_df[col].astype(str))
                except:
                    patient_df[col] = 0

        feature_columns = cost_artifacts.get('feature_columns', list(cost_artifacts.get('feature_names', [])))
        patient_df = patient_df[feature_columns]

        predicted_cost = float(cost_artifacts['model'].predict(patient_df)[0])
        
        min_cost = round(predicted_cost * 0.85, -2)
        max_cost = round(predicted_cost * 1.15, -2)
        predicted_cost = round(predicted_cost, -2)

        if predicted_cost >= 300000:
            category = "Very High Cost"
        elif predicted_cost >= 150000:
            category = "High Cost"
        elif predicted_cost >= 50000:
            category = "Medium Cost"
        else:
            category = "Low Cost"

        save_prediction('Cost Estimation', data, f"₹{predicted_cost:,.0f}", None)

        return jsonify({
            'success': True,
            'min_cost': min_cost,
            'predicted_cost': predicted_cost,
            'max_cost': max_cost,
            'category': category
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== MORTALITY RISK ====================
def calculate_mortality_score(age, gender, diagnosis, bodytemp, heartrate,
                             resprate, oxygensat, systolicbp, diastolicbp,
                             familyhistory="No", smoking="Never", alcohol="No"):
    score = 0
    breakdown = {}
    
    if age >= 85: score += 20; breakdown['age'] = 20
    elif age >= 75: score += 16; breakdown['age'] = 16
    elif age >= 65: score += 12; breakdown['age'] = 12
    elif age >= 55: score += 8; breakdown['age'] = 8
    elif age >= 45: score += 4; breakdown['age'] = 4
    else: breakdown['age'] = 0
    
    if oxygensat <= 75: score += 30; breakdown['oxygen'] = 30
    elif oxygensat <= 80: score += 28; breakdown['oxygen'] = 28
    elif oxygensat <= 85: score += 25; breakdown['oxygen'] = 25
    elif oxygensat <= 88: score += 22; breakdown['oxygen'] = 22
    elif oxygensat <= 90: score += 18; breakdown['oxygen'] = 18
    elif oxygensat <= 92: score += 14; breakdown['oxygen'] = 14
    elif oxygensat <= 94: score += 10; breakdown['oxygen'] = 10
    elif oxygensat <= 95: score += 6; breakdown['oxygen'] = 6
    elif oxygensat <= 96: score += 3; breakdown['oxygen'] = 3
    else: breakdown['oxygen'] = 0
    
    bp_score = 0
    if systolicbp <= 70: bp_score += 20
    elif systolicbp <= 80: bp_score += 18
    elif systolicbp <= 90: bp_score += 15
    elif systolicbp <= 100: bp_score += 10
    elif systolicbp >= 200: bp_score += 20
    elif systolicbp >= 180: bp_score += 15
    elif systolicbp >= 160: bp_score += 8
    elif systolicbp >= 140: bp_score += 4
    score += bp_score
    breakdown['blood_pressure'] = bp_score
    
    hr_score = 0
    if heartrate <= 40 or heartrate >= 150: hr_score = 15
    elif heartrate <= 50 or heartrate >= 140: hr_score = 12
    elif heartrate <= 55 or heartrate >= 130: hr_score = 9
    elif heartrate <= 60 or heartrate >= 120: hr_score = 7
    elif heartrate >= 110: hr_score = 5
    elif heartrate >= 100: hr_score = 3
    score += hr_score
    breakdown['heart_rate'] = hr_score
    
    rr_score = 0
    if resprate >= 40: rr_score = 10
    elif resprate >= 35: rr_score = 9
    elif resprate >= 30: rr_score = 7
    elif resprate >= 25: rr_score = 5
    elif resprate >= 22: rr_score = 3
    elif resprate >= 20: rr_score = 2
    elif resprate <= 8: rr_score = 10
    elif resprate <= 10: rr_score = 7
    score += rr_score
    breakdown['respiratory_rate'] = rr_score
    
    temp_score = 0
    if bodytemp >= 42 or bodytemp <= 35: temp_score = 10
    elif bodytemp >= 41 or bodytemp <= 35.5: temp_score = 8
    elif bodytemp >= 40 or bodytemp <= 36: temp_score = 6
    elif bodytemp >= 39.5: temp_score = 4
    elif bodytemp >= 39: temp_score = 3
    elif bodytemp >= 38.5: temp_score = 2
    score += temp_score
    breakdown['temperature'] = temp_score
    
    critical_diseases = ["Pneumonia", "COVID-19", "Tuberculosis", "Chronic Kidney Disease"]
    serious_diseases = ["Hepatitis", "Asthma", "Bronchitis", "Influenza", "Dengue", "Malaria"]
    chronic_diseases = ["Hypertension", "Diabetes Mellitus", "Diabetes"]
    
    diag_score = 0
    if diagnosis in critical_diseases: diag_score = 15
    elif diagnosis in serious_diseases: diag_score = 10
    elif diagnosis in chronic_diseases: diag_score = 5
    elif diagnosis == "Healthy": diag_score = 0
    else: diag_score = 7
    score += diag_score
    breakdown['diagnosis'] = diag_score
    
    risk_score = 0
    if smoking in ["Yes", "Former", "Current"]: risk_score += 2
    if familyhistory == "Yes": risk_score += 2
    if alcohol in ["Yes", "Regular"]: risk_score += 1
    score += risk_score
    breakdown['risk_factors'] = risk_score
    
    score = min(score, 100)
    
    if score >= 70:
        category = "High Risk"
        message = "CRITICAL - Immediate intervention required!"
        action = "ICU admission, close monitoring"
    elif score >= 40:
        category = "Medium Risk"
        message = "CAUTION - Close monitoring needed"
        action = "Hospital admission, monitor vitals"
    else:
        category = "Low Risk"
        message = "STABLE - Routine care appropriate"
        action = "Ward admission, routine care"
    
    return score, category, message, action, breakdown


@app.route('/api/mortality/calculate', methods=['POST'])
def calculate_mortality():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.json
        score, category, message, action, breakdown = calculate_mortality_score(
            age=data['age'],
            gender=data['gender'],
            diagnosis=data['diagnosis'],
            bodytemp=data['bodytemperature'],
            heartrate=data['heartrate'],
            resprate=data['respiratoryrate'],
            oxygensat=data['oxygensaturation'],
            systolicbp=data['systolicbp'],
            diastolicbp=data['diastolicbp'],
            familyhistory=data.get('familyhistory', 'No'),
            smoking=data.get('smokingstatus', 'Never'),
            alcohol=data.get('alcoholuse', 'No')
        )
        
        save_prediction('Mortality Risk', data, f"{category} (Score: {score})", None)
        
        return jsonify({
            'success': True,
            'score': score,
            'category': category,
            'message': message,
            'action': action,
            'breakdown': breakdown
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== KTAS TRIAGE ====================
@app.route('/api/ktas/predict', methods=['POST'])
def predict_ktas():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.json
        patient_data = {
            'Age': data['age'],
            'Gender': data['gender'],
            'Heart_Rate': data['heartrate'],
            'Body_Temperature': data['bodytemperature'],
            'Respiratory_Rate': data['respiratoryrate'],
            'Oxygen_Saturation': data['oxygensaturation'],
            'Family_History': data.get('familyhistory', 'No'),
            'Smoking_Status': data.get('smokingstatus', 'Never'),
            'Alcohol_Use': data.get('alcoholuse', 'No'),
            'Physical_Activity_Level': data.get('activitylevel', 'Moderate'),
            'Diagnosis': data['diagnosis'],
            'Systolic_BP': data['systolicbp'],
            'Diastolic_BP': data['diastolicbp']
        }

        patient_df = pd.DataFrame([patient_data])

        for col in ktas_artifacts['categorical_columns']:
            if col in patient_df.columns and col in ktas_artifacts['label_encoders']:
                try:
                    patient_df[col] = ktas_artifacts['label_encoders'][col].transform(patient_df[col].astype(str))
                except:
                    patient_df[col] = 0

        patient_scaled = ktas_artifacts['scaler'].transform(patient_df)

        prediction = ktas_artifacts['model'].predict(patient_scaled)[0]
        probabilities = ktas_artifacts['model'].predict_proba(patient_scaled)[0]
        predicted_ktas = ktas_artifacts['target_encoder'].inverse_transform([prediction])[0]
        confidence = float(probabilities[prediction])

        save_prediction('KTAS Triage', data, predicted_ktas, confidence)

        all_probs = {ktas_artifacts['target_encoder'].classes_[i]: float(probabilities[i]) for i in range(len(ktas_artifacts['target_encoder'].classes_))}
        sorted_probs = sorted(all_probs.items(), key=lambda x: x[1], reverse=True)

        return jsonify({
            'success': True,
            'predicted_level': predicted_ktas,
            'confidence': confidence,
            'all_probabilities': dict(sorted_probs)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== OTHER ROUTES ====================
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'models': {
            'disease_prediction': f"{disease_artifacts['accuracy']*100:.1f}%",
            'readmission_risk': f"{readmission_artifacts['accuracy']*100:.1f}%",
            'cost_estimation': f"{cost_artifacts['accuracy']:.1f}%",
            'ktas_triage': f"{ktas_artifacts['accuracy']*100:.1f}%"
        }
    })


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🏥 MESPRIT - AI Healthcare Assistant Suite with Authentication")
    print("="*70)
    print("Main URL: http://localhost:8000")
    print("="*70 + "\n")
    app.run(debug=True, port=8000, host='0.0.0.0')
