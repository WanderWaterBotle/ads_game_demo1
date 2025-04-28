from flask import Flask, request, jsonify, send_from_directory
import json
import os
from datetime import datetime

app = Flask(__name__, static_folder='static')

USER_FILE = 'users.json'
LEADERBOARD_FILE = 'leaderboard.json'

# 初始化文件
if not os.path.exists(USER_FILE):
    with open(USER_FILE, 'w', encoding='utf-8') as f:
        json.dump({"users": []}, f)

if not os.path.exists(LEADERBOARD_FILE):
    with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
        json.dump({"date": datetime.now().strftime("%Y-%m-%d"), "players": []}, f)

def load_json(file):
    with open(file, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 自动重置日期逻辑
def load_leaderboard_with_reset():
    today = datetime.now().strftime("%Y-%m-%d")
    data = load_json(LEADERBOARD_FILE)
    if data.get("date") != today:
        data = {"date": today, "players": []}
        save_json(LEADERBOARD_FILE, data)
    return data

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    users = load_json(USER_FILE)
    if any(u['username'] == data['username'] for u in users['users']):
        return jsonify({"success": False, "message": "用户名已被注册"})
    users['users'].append({"username": data['username'], "password": data['password']})
    save_json(USER_FILE, users)
    return jsonify({"success": True, "message": "注册成功"})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    users = load_json(USER_FILE)
    if any(u['username'] == data['username'] and u['password'] == data['password'] for u in users['users']):
        return jsonify({"success": True, "message": "登录成功"})
    return jsonify({"success": False, "message": "用户名或密码错误"})

@app.route('/api/join', methods=['POST'])
def join():
    username = request.json.get('username')
    lb = load_leaderboard_with_reset()
    if not any(p['username'] == username for p in lb['players']):
        lb['players'].append({"username": username, "time": 0, "invites": 1})
        save_json(LEADERBOARD_FILE, lb)
    return jsonify({"success": True})

@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    lb = load_leaderboard_with_reset()
    return jsonify(lb)

@app.route('/api/watch', methods=['POST'])
def watch():
    username = request.json.get('username')
    lb = load_leaderboard_with_reset()
    for p in lb['players']:
        if p['username'] == username:
            p['time'] += 1 * p['invites']
    save_json(LEADERBOARD_FILE, lb)
    return jsonify({"success": True})

@app.route('/api/invite', methods=['POST'])
def invite():
    username = request.json.get('username')
    lb = load_leaderboard_with_reset()
    for p in lb['players']:
        if p['username'] == username:
            p['invites'] *= 2
    save_json(LEADERBOARD_FILE, lb)
    return jsonify({"success": True})

@app.route('/api/exit', methods=['POST'])
def exit_game():
    username = request.json.get('username')
    lb = load_leaderboard_with_reset()
    lb['players'] = [p for p in lb['players'] if p['username'] != username]
    save_json(LEADERBOARD_FILE, lb)
    return jsonify({"success": True, "message": "已退出比赛，1元已退还"})

@app.route('/api/status', methods=['GET'])
def get_status():
    lb = load_leaderboard_with_reset()
    players_count = len(lb['players'])
    prize_pool = round(players_count * 0.9, 2)
    return jsonify({"players": players_count, "pool": prize_pool})

@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True)
