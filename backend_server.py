import sqlite3
import time
import statistics
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_FILE = "activity_data.db"
PORT = 5001 

# --- CONFIGURATION ---
THRESHOLD_TIMEOUT = 5000 
WINDOW_SIZE = 5
BASELINE_SIZE = 30
RETENTION_DAYS = 30 
OFFLINE_TIMEOUT = 15 

TARGETS = {}
RTT_HISTORY = {}
BASELINE_HISTORY = {}

SYSTEM_STATUS = { "connection": "DISCONNECTED", "qr_code": None }

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS rtt_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, target_phone TEXT, rtt_ms INTEGER, status TEXT, timestamp REAL)")
        conn.execute("CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, target_phone TEXT, start_time TEXT, end_time TEXT, duration_sec REAL)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON rtt_logs(timestamp)")

def cleanup_old_data():
    try:
        limit_date = time.time() - (RETENTION_DAYS * 86400) 
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.execute("DELETE FROM rtt_logs WHERE timestamp < ?", (limit_date,))
            count = cursor.rowcount
            conn.execute("VACUUM")
        print(f"🧹 MAINTENANCE : {count} logs purgés.")
    except: pass

def check_timeouts():
    now = time.time()
    for t in TARGETS:
        if (now - TARGETS[t]['last_seen'] > OFFLINE_TIMEOUT) and TARGETS[t]['status'] != "OFFLINE":
            TARGETS[t]['status'] = "OFFLINE"

def determine_smart_status(current_rtt, history):
    # Sécurité de base
    if current_rtt > THRESHOLD_TIMEOUT: return "OFFLINE"
    
    # Pas assez de données pour faire des stats fiables
    if len(history) < 10: return "ONLINE" if current_rtt < 1500 else "IDLE"
    
    # --- ANALYSE Z-SCORE
    median = statistics.median(history)
    try:
        stdev = statistics.stdev(history)
    except:
        stdev = 0 
    
    if stdev < 20: stdev = 20

    # Seuil de déverrouillage : Médiane - (1.5 x Écart-Type)
    threshold_unlock = median - (1.5 * stdev)

    if current_rtt < threshold_unlock:
        return "UNLOCKED"
    
    if current_rtt < 1500: return "ONLINE"
    return "IDLE"

@app.route('/api/log_ping', methods=['POST'])
def log_ping():
    data = request.json
    target = data.get('target')
    raw_rtt = data.get('rtt')
    
    if not target or raw_rtt is None: return jsonify({"error": "Missing data"}), 400

    now = time.time()

    if target not in RTT_HISTORY: RTT_HISTORY[target] = []
    if target not in BASELINE_HISTORY: BASELINE_HISTORY[target] = []
    
    RTT_HISTORY[target].append(raw_rtt)
    if len(RTT_HISTORY[target]) > WINDOW_SIZE: RTT_HISTORY[target].pop(0)
    
    stable_rtt = statistics.median(RTT_HISTORY[target]) if len(RTT_HISTORY[target]) >= 3 else raw_rtt

    BASELINE_HISTORY[target].append(stable_rtt)
    if len(BASELINE_HISTORY[target]) > BASELINE_SIZE: BASELINE_HISTORY[target].pop(0)

    status = determine_smart_status(stable_rtt, BASELINE_HISTORY[target])

    if target in TARGETS:
        TARGETS[target]['status'] = status
        TARGETS[target]['last_seen'] = now

    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("INSERT INTO rtt_logs (target_phone, rtt_ms, status, timestamp) VALUES (?, ?, ?, ?)", (target, raw_rtt, status, now))
            
            cursor = conn.execute("SELECT id, start_time, end_time FROM sessions WHERE target_phone = ? ORDER BY id DESC LIMIT 1", (target,))
            last_session = cursor.fetchone()

            if status in ["ONLINE", "UNLOCKED"]:
                current_time_str = datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')
                if not last_session:
                    conn.execute("INSERT INTO sessions (target_phone, start_time, end_time) VALUES (?, ?, ?)", (target, current_time_str, current_time_str))
                else:
                    sess_id, start, end = last_session
                    last_end_ts = datetime.strptime(end, '%Y-%m-%d %H:%M:%S').timestamp()
                    if (now - last_end_ts) > 120:
                        conn.execute("INSERT INTO sessions (target_phone, start_time, end_time) VALUES (?, ?, ?)", (target, current_time_str, current_time_str))
                    else:
                        start_ts = datetime.strptime(start, '%Y-%m-%d %H:%M:%S').timestamp()
                        duration = now - start_ts
                        conn.execute("UPDATE sessions SET end_time = ?, duration_sec = ? WHERE id = ?", (current_time_str, duration, sess_id))
    except Exception as e: print(f"Erreur DB: {e}")

    return jsonify({"status": "logged", "stable_rtt": stable_rtt})

@app.route('/api/targets', methods=['GET', 'POST', 'DELETE'])
def manage_targets():
    global TARGETS, RTT_HISTORY, BASELINE_HISTORY
    check_timeouts()
    
    if request.method == 'POST':
        data = request.json
        raw_num = data.get('target', '').replace('+', '').replace(' ', '')
        if raw_num and not raw_num.endswith('@s.whatsapp.net'): raw_num += '@s.whatsapp.net'
        if raw_num not in TARGETS:
            TARGETS[raw_num] = {"avatar": None, "status": "Calibrage...", "last_seen": time.time()}
            RTT_HISTORY[raw_num] = []
            BASELINE_HISTORY[raw_num] = []
        return jsonify({"status": "added", "targets": list(TARGETS.keys())})

    if request.method == 'DELETE':
        data = request.json
        target = data.get('target')
        if target in TARGETS: del TARGETS[target]
        return jsonify({"status": "removed"})

    return jsonify(list(TARGETS.keys()))

@app.route('/api/update_status', methods=['POST'])
def update_status():
    global SYSTEM_STATUS
    data = request.json
    SYSTEM_STATUS['connection'] = data.get('status')
    if 'qr' in data: SYSTEM_STATUS['qr_code'] = data['qr']
    if SYSTEM_STATUS['connection'] == 'CONNECTED': SYSTEM_STATUS['qr_code'] = None
    return jsonify({"status": "ok"})

@app.route('/api/update_avatar', methods=['POST'])
def update_avatar():
    global TARGETS
    data = request.json
    if data.get('target') in TARGETS: 
        TARGETS[data.get('target')]['avatar'] = data.get('url')
    return jsonify({"status": "ok"})

@app.route('/api/dashboard_data', methods=['GET'])
def get_dashboard_data():
    check_timeouts()
    return jsonify({ "system": SYSTEM_STATUS, "targets": TARGETS })

@app.route('/api/history/<path:target_id>', methods=['GET'])
def get_history(target_id):
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        logs = conn.execute("SELECT * FROM rtt_logs WHERE target_phone = ? ORDER BY id DESC LIMIT 200", (target_id,)).fetchall()
        sessions = conn.execute("SELECT * FROM sessions WHERE target_phone = ? ORDER BY id DESC LIMIT 50", (target_id,)).fetchall()
        
    # --- ANALYSE SOMMEIL (> 1h) ---
    sleep_cycles = []
    sessions_data = [dict(row) for row in sessions]
    
    if len(sessions_data) > 0:
        last_active_str = sessions_data[0]['end_time']
        last_active_ts = datetime.strptime(last_active_str, '%Y-%m-%d %H:%M:%S').timestamp()
        current_gap = time.time() - last_active_ts
        
        if current_gap > 3600:
            hours = int(current_gap // 3600)
            mins = int((current_gap % 3600) // 60)
            sleep_cycles.append({
                "start": last_active_str.split(' ')[1][:5],
                "end": "En cours...",
                "duration": f"{hours}h {mins}min",
                "is_current": True
            })

        for i in range(len(sessions_data) - 1):
            current_sess_start = datetime.strptime(sessions_data[i]['start_time'], '%Y-%m-%d %H:%M:%S')
            prev_sess_end = datetime.strptime(sessions_data[i+1]['end_time'], '%Y-%m-%d %H:%M:%S')
            gap_seconds = (current_sess_start - prev_sess_end).total_seconds()
            
            if gap_seconds > 3600:
                hours = int(gap_seconds // 3600)
                mins = int((gap_seconds % 3600) // 60)
                sleep_cycles.append({
                    "start": prev_sess_end.strftime('%H:%M'),
                    "end": current_sess_start.strftime('%H:%M'),
                    "duration": f"{hours}h {mins}min",
                    "is_current": False
                })

    return jsonify({ 
        "logs": [dict(row) for row in logs], 
        "sessions": sessions_data[:20], 
        "sleep_cycles": sleep_cycles 
    })

@app.route('/')
def dashboard():
    try:
        with open('dashboard.html', 'r', encoding='utf-8') as f: return render_template_string(f.read())
    except: return "Error"

if __name__ == '__main__':
    init_db()
    cleanup_old_data()
    print(f">>> ANALYTICS STABLE (Z-Score + Sleep) PRET sur http://0.0.0.0:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)