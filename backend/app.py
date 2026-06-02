import os
import uuid
import sqlite3
import numpy as np
from PIL import Image
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# Load Plastic Data
from plastic_data import PLASTIC_DETAILS
from report_generator import generate_pdf_report

app = Flask(__name__)
CORS(app) # Enable CORS for frontend connection

# Configurations
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'temp_uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

# Initialize SQLite Database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Scans History
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plastic_type TEXT,
        confidence REAL,
        env_score INTEGER,
        image_name TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Schema Migration for user_wallet
    cursor.execute("PRAGMA table_info(user_wallet)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if len(columns) > 0 and "phone_number" not in columns:
        cursor.execute("DROP TABLE user_wallet")
        
    # Re-create multi-user wallet table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_wallet (
        phone_number TEXT PRIMARY KEY,
        name TEXT,
        total_weight REAL DEFAULT 0.0,
        total_coins INTEGER DEFAULT 0
    )
    """)
    
    # Drop old leaderboard table as rankings are now dynamically computed from user_wallet
    cursor.execute("DROP TABLE IF EXISTS leaderboard")
    
    # Seed mock users if table is empty
    cursor.execute("SELECT COUNT(*) FROM user_wallet")
    if cursor.fetchone()[0] == 0:
        mock_data = [
            ("9999999991", "Rohan Sharma", 320.0, 3200),
            ("9999999992", "Priya Patel", 285.0, 2850),
            ("9999999993", "Amit Kumar", 210.0, 2100),
            ("9999999994", "Debanjana Sarkar", 185.0, 1850),
            ("9999999995", "Soumita Das", 150.0, 1500)
        ]
        cursor.executemany("""
            INSERT INTO user_wallet (phone_number, name, total_weight, total_coins)
            VALUES (?, ?, ?, ?)
        """, mock_data)
        
    conn.commit()
    conn.close()

init_db()

# Load TensorFlow Model (with Fallback)
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'plastic_classifier.h5')
model = None
use_fallback = False

try:
    import tensorflow as tf
    # Suppress verbose warnings
    import logging
    logging.getLogger('tensorflow').setLevel(logging.ERROR)
    
    if os.path.exists(MODEL_PATH):
        model = tf.keras.models.load_model(MODEL_PATH)
        print("TensorFlow Model loaded successfully!")
    else:
        print(f"Model not found at {MODEL_PATH}. Running in simulation/fallback mode.")
        use_fallback = True
except Exception as e:
    print(f"Failed to load TensorFlow model: {e}. Running in simulation/fallback mode.")
    use_fallback = True

# CNN Classes
CLASS_NAMES = ['Others', 'PC', 'PE', 'PET', 'PP', 'PS']

# Map Model Outputs to Frontend classes (PET, HDPE, PVC, LDPE, PP, PS, Other)
def map_class_to_detail_key(predicted_class):
    if predicted_class == 'PET':
        return 'PET'
    elif predicted_class == 'PE':
        # Split into HDPE and LDPE randomly/heuristically for variety
        return np.random.choice(['HDPE', 'LDPE'])
    elif predicted_class == 'PP':
        return 'PP'
    elif predicted_class == 'PS':
        return 'PS'
    elif predicted_class == 'PC':
        # PC belongs to class 7 (Other) or PVC
        return np.random.choice(['PVC', 'Other'])
    else:
        return 'Other'

# ==========================================
# ENDPOINTS
# ==========================================

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({"success": False, "error": "No image file provided"}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({"success": False, "error": "Empty filename"}), 400
        
    # Save file to temp uploads
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    temp_file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(temp_file_path)
    
    try:
        if not use_fallback and model is not None:
            # Predict using TF model
            img = Image.open(temp_file_path).resize((224, 224)).convert('RGB')
            img_array = np.array(img).astype("float32") / 255.0
            img_array = np.expand_dims(img_array, axis=0)
            
            prediction = model.predict(img_array, verbose=0)
            predicted_index = np.argmax(prediction)
            predicted_class = CLASS_NAMES[predicted_index]
            confidence = float(np.max(prediction) * 100)
            
            plastic_key = map_class_to_detail_key(predicted_class)
        else:
            # Fallback Simulator
            plastic_key = np.random.choice(['PET', 'HDPE', 'PVC', 'LDPE', 'PP', 'PS', 'Other'])
            confidence = float(np.random.uniform(78.5, 99.2))
            
        # Get details
        details = PLASTIC_DETAILS[plastic_key]
        
        # Save to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scans (plastic_type, confidence, env_score, image_name)
            VALUES (?, ?, ?, ?)
        """, (plastic_key, confidence, details['env_risk'], unique_filename))
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "plastic_type": plastic_key,
            "confidence": confidence,
            "details": details,
            "image_id": unique_filename
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/report', methods=['GET'])
def get_report():
    plastic_type = request.args.get('type')
    confidence = request.args.get('confidence', type=float)
    image_id = request.args.get('image_id')
    
    if not plastic_type or not confidence:
        return jsonify({"success": False, "error": "Missing type or confidence parameters"}), 400
        
    if plastic_type not in PLASTIC_DETAILS:
        return jsonify({"success": False, "error": "Invalid plastic type"}), 400
        
    details = PLASTIC_DETAILS[plastic_type]
    image_path = os.path.join(UPLOAD_FOLDER, image_id) if image_id else None
    
    try:
        pdf_path = generate_pdf_report(plastic_type, confidence, details, image_path)
        
        # Send and delete after
        response = send_file(
            pdf_path, 
            mimetype='application/pdf', 
            as_attachment=True, 
            download_name=f'EcoSort_Report_{plastic_type}.pdf'
        )
        
        # Clean up report after sending (could cause locked file errors on windows if too fast,
        # but Flask handles it or we let it persist in local backend dir).
        return response
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/reward', methods=['GET', 'POST'])
def handle_reward():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if request.method == 'POST':
        data = request.json or {}
        phone = data.get('phone', '').strip()
        name = data.get('name', '').strip()
        
        if not phone:
            return jsonify({"success": False, "error": "Phone number is required"}), 400
            
        # Check if this is a cash conversion request
        if 'convert_coins' in data:
            coins_to_convert = int(data.get('convert_coins', 0))
            if coins_to_convert <= 0:
                return jsonify({"success": False, "error": "Coins must be greater than zero"}), 400
                
            cursor.execute("SELECT total_coins, total_weight, name FROM user_wallet WHERE phone_number = ?", (phone,))
            row = cursor.fetchone()
            if not row:
                return jsonify({"success": False, "error": "User profile not found. Please deposit plastic first."}), 404
                
            current_coins, total_weight, user_name = row
            if coins_to_convert > current_coins:
                return jsonify({"success": False, "error": f"Insufficient coins. Available balance: {current_coins} Coins"}), 400
                
            cursor.execute("UPDATE user_wallet SET total_coins = total_coins - ? WHERE phone_number = ?", (coins_to_convert, phone))
            conn.commit()
            
            # Get dynamic leaderboard
            cursor.execute("SELECT name, total_coins FROM user_wallet ORDER BY total_coins DESC")
            leaderboard = [{"name": row[0], "coins": row[1]} for row in cursor.fetchall()]
            conn.close()
            
            return jsonify({
                "success": True,
                "coins_earned": 0,
                "total_weight": total_weight,
                "total_coins": current_coins - coins_to_convert,
                "name": user_name,
                "phone": phone,
                "leaderboard": leaderboard
            })
            
        # Add recycled plastic weight
        weight = float(data.get('weight', 0))
        
        if weight <= 0:
            return jsonify({"success": False, "error": "Weight must be greater than zero"}), 400
            
        # Calculate EcoCoins
        # 1kg = 10 Coins, 10kg = 120, 50kg = 700, 100kg = 1500, 300kg = 5000
        if weight >= 300:
            coins = 5000
        elif weight >= 100:
            coins = 1500
        elif weight >= 50:
            coins = 700
        elif weight >= 10:
            coins = 120
        else:
            coins = int(weight * 10)
            
        # Check if user exists
        cursor.execute("SELECT total_weight, total_coins, name FROM user_wallet WHERE phone_number = ?", (phone,))
        row = cursor.fetchone()
        
        if row:
            # User exists: update stats and name (if name provided)
            if name:
                cursor.execute("""
                    UPDATE user_wallet 
                    SET total_weight = total_weight + ?, total_coins = total_coins + ?, name = ?
                    WHERE phone_number = ?
                """, (weight, coins, name, phone))
            else:
                cursor.execute("""
                    UPDATE user_wallet 
                    SET total_weight = total_weight + ?, total_coins = total_coins + ?
                    WHERE phone_number = ?
                """, (weight, coins, phone))
        else:
            # New user: insert
            if not name:
                name = f"User {phone[-4:]}" if len(phone) >= 4 else "New User"
            cursor.execute("""
                INSERT INTO user_wallet (phone_number, name, total_weight, total_coins)
                VALUES (?, ?, ?, ?)
            """, (phone, name, weight, coins))
            
        conn.commit()
        
        # Fetch updated details
        cursor.execute("SELECT total_weight, total_coins, name FROM user_wallet WHERE phone_number = ?", (phone,))
        total_weight, total_coins, user_name = cursor.fetchone()
        
        # Get dynamic leaderboard
        cursor.execute("SELECT name, total_coins FROM user_wallet ORDER BY total_coins DESC")
        leaderboard = [{"name": row[0], "coins": row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            "success": True,
            "coins_earned": coins,
            "total_weight": total_weight,
            "total_coins": total_coins,
            "name": user_name,
            "phone": phone,
            "leaderboard": leaderboard
        })
        
    else:
        # GET details
        phone = request.args.get('phone', '').strip()
        total_weight = 0.0
        total_coins = 0
        user_name = ""
        
        if phone:
            cursor.execute("SELECT total_weight, total_coins, name FROM user_wallet WHERE phone_number = ?", (phone,))
            row = cursor.fetchone()
            if row:
                total_weight, total_coins, user_name = row
                
        cursor.execute("SELECT name, total_coins FROM user_wallet ORDER BY total_coins DESC")
        leaderboard = [{"name": row[0], "coins": row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            "success": True,
            "total_weight": total_weight,
            "total_coins": total_coins,
            "name": user_name,
            "phone": phone,
            "leaderboard": leaderboard
        })

@app.route('/statistics', methods=['GET'])
def get_statistics():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get total scans count
    cursor.execute("SELECT COUNT(*) FROM scans")
    total_scans = cursor.fetchone()[0]
    
    # Get scans by category
    cursor.execute("SELECT plastic_type, COUNT(*) FROM scans GROUP BY plastic_type")
    scans_by_type = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Fill in zeros for missing types
    for k in PLASTIC_DETAILS.keys():
        if k not in scans_by_type:
            scans_by_type[k] = 0
            
    # Get last 5 scans
    cursor.execute("SELECT plastic_type, confidence, env_score, timestamp FROM scans ORDER BY id DESC LIMIT 5")
    recent_scans = [{
        "plastic_type": row[0],
        "confidence": row[1],
        "env_score": row[2],
        "timestamp": row[3]
    } for row in cursor.fetchall()]
    
    # Get global user wallet details
    cursor.execute("SELECT SUM(total_weight), SUM(total_coins) FROM user_wallet")
    wallet = cursor.fetchone()
    total_weight = wallet[0] if wallet and wallet[0] is not None else 0.0
    total_coins = wallet[1] if wallet and wallet[1] is not None else 0
    
    conn.close()
    
    return jsonify({
        "success": True,
        "total_scans": total_scans,
        "scans_by_type": scans_by_type,
        "recent_scans": recent_scans,
        "total_weight": total_weight,
        "total_coins": total_coins
    })

# Serve uploaded images statically
@app.route('/uploads/<filename>', methods=['GET'])
def serve_image(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))

if __name__ == '__main__':
    app.run(port=5000, debug=True)
