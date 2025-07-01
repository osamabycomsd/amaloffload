# dashboard.py
from flask import Flask, render_template, jsonify
from peer_discovery import discover_peers
import threading
import time
from typing import List, Dict
import logging

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# تهيئة قائمة الأقران
current_peers: Dict[str, List[Dict[str, str]]] = {"local": [], "external": []}

def update_peers_loop() -> None:
    """حلقة تحديث قائمة الأقران بشكل دوري"""
    global current_peers
    while True:
        try:
            new_peers = discover_peers()
            current_peers = new_peers
            total_peers = len(new_peers["local"]) + len(new_peers["external"])
            app.logger.info(f"تم تحديث قائمة الأقران: {total_peers} جهاز")
        except Exception as e:
            app.logger.error(f"خطأ في اكتشاف الأقران: {str(e)}")
        time.sleep(10)

@app.route("/")
def dashboard() -> str:
    """عرض لوحة التحكم الرئيسية"""
    total_peers = len(current_peers["local"]) + len(current_peers["external"])
    return render_template("dashboard.html",
                           peers_count=total_peers,
                           last_update=time.strftime("%Y-%m-%d %H:%M:%S"))

@app.route("/api/peers")
def get_peers() -> dict:
    """واجهة API للحصول على قائمة الأقران"""
    total_peers = len(current_peers["local"]) + len(current_peers["external"])
    return jsonify({
        "peers": current_peers,
        "count": total_peers,
        "status": "success"
    })

def start_background_thread() -> None:
    """بدء خيط الخلفية لتحديث الأقران"""
    thread = threading.Thread(target=update_peers_loop)
    thread.daemon = True
    thread.start()

if __name__ == "__main__":
    start_background_thread()
    app.run(host="0.0.0.0", port=7530, debug=False)

