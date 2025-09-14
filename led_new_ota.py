from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import os
import json
import paho.mqtt.client as mqtt

app = Flask(__name__)
socketio = SocketIO(app)

# Config
FIRMWARE_DIR = 'firmwares'
FIRMWARE_FILE = 'firmware.bin'

MQTT_BROKER = "10.144.0.143"
MQTT_PORT = 1884
MQTT_ACK_TOPIC = "esp32/motor/ack"
MQTT_SCHEDULE_TOPIC = "esp32/motor/schedule"
MQTT_OTA_TOPIC = "esp32/ota/command"
MQTT_MOTOR_CMD_TOPIC = "esp32/motor/command"

# Global MQTT client
mqtt_client = mqtt.Client()

# Ensure firmware dir exists
os.makedirs(FIRMWARE_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('new_index.html')

@app.route('/upload_firmware', methods=['POST'])
def upload_firmware():
    file = request.files.get('firmware')
    if file and file.filename.endswith('.bin'):
        file_path = os.path.join(FIRMWARE_DIR, FIRMWARE_FILE)
        file.save(file_path)
        return jsonify({"status": "success", "message": "Firmware uploaded successfully!"})
    return jsonify({"status": "error", "message": "Invalid file format. Please upload a .bin file."}), 400

@app.route('/trigger_ota_update', methods=['POST'])
def trigger_ota_update():
    payload = json.dumps({"cmd": 1})
    result = mqtt_client.publish(MQTT_OTA_TOPIC, payload)
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        return jsonify({"status": "success", "message": "OTA update command sent!"})
    else:
        return jsonify({"status": "error", "message": "Failed to send OTA update command!"}), 500

@app.route('/set_motor_mode', methods=['POST'])
def set_motor_mode():
    mode = request.json.get('mode')
    if mode == 'scheduled':
        payload = json.dumps({"cmd": -1})
    elif mode == 'manual':
        payload = json.dumps({"cmd": 1})
    else:
        return jsonify({"status": "error", "message": "Invalid mode!"}), 400

    result = mqtt_client.publish(MQTT_MOTOR_CMD_TOPIC, payload)
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        return jsonify({"status": "success", "message": f"Motor mode set to {mode}!"})
    else:
        return jsonify({"status": "error", "message": f"Failed to set motor mode to {mode}!"}), 500

@app.route('/send_schedule', methods=['POST'])
def send_schedule():
    time_period = request.form.get('time_period')
    duration = request.form.get('duration')
    if time_period and duration:
        payload = json.dumps({"Duration": int(duration), "TimePeriod": int(time_period)})
        result = mqtt_client.publish(MQTT_SCHEDULE_TOPIC, payload)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            return jsonify({"status": "success", "message": f"Scheduled command sent: {payload}"})
        else:
            return jsonify({"status": "error", "message": "Failed to send schedule!"}), 500
    return jsonify({"status": "error", "message": "Please provide both TimePeriod and Duration."}), 400

@app.route('/firmware.bin', methods=['GET'])
def serve_firmware():
    return send_from_directory(FIRMWARE_DIR, FIRMWARE_FILE)

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print("MQTT connected with result code", rc)
    client.subscribe(MQTT_ACK_TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(payload)
        socketio.emit("motor_ack", {"status": payload.get("status")})
    except Exception as e:
        print("Failed to parse MQTT message:", e)

# MQTT Initialization
def init_mqtt():
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()

if __name__ == '__main__':
    init_mqtt()
    socketio.run(app, host='0.0.0.0', port=5000)
