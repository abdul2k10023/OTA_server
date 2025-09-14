from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import subprocess

app = Flask(__name__)

# Set the path to your firmware binary file and storage directory
FIRMWARE_DIR = 'firmwares/'  # Change this to the path of your firmware folder
FIRMWARE_FILE = 'firmware.bin'  # Name of the firmware binary file

# Ensure the firmware directory exists
if not os.path.exists(FIRMWARE_DIR):
    os.makedirs(FIRMWARE_DIR)

# MQTT Settings
MQTT_BROKER = "10.144.0.143"
MQTT_PORT = 1884
MQTT_SCHEDULE_TOPIC = "esp32/motor/schedule"
MQTT_OTA_TOPIC = "esp32/ota/command"
MQTT_MOTOR_CMD_TOPIC = "esp32/motor/command"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_firmware', methods=['POST'])
def upload_firmware():
    # Handle the .bin file upload
    file = request.files.get('firmware')  # 'firmware' is the name of the input in the HTML form
    if file and file.filename.endswith('.bin'):
        # Save the file locally
        file_path = os.path.join(FIRMWARE_DIR, FIRMWARE_FILE)
        file.save(file_path)
        return jsonify({"status": "success", "message": "Firmware uploaded successfully!"}), 200
    else:
        return jsonify({"status": "error", "message": "Invalid file format. Please upload a .bin file."}), 400

@app.route('/trigger_ota_update', methods=['POST'])
def trigger_ota_update():
    # Trigger the OTA update via MQTT using mosquitto_pub
    command = f"/usr/bin/mosquitto_pub -h {MQTT_BROKER} -p {MQTT_PORT} -t {MQTT_OTA_TOPIC} -m '{{\"cmd\": 1}}'"
    try:
        subprocess.run(command, shell=True, check=True)
        return jsonify({"status": "success", "message": "OTA update command sent!"}), 200
    except subprocess.CalledProcessError:
        return jsonify({"status": "error", "message": "Failed to send OTA update command!"}), 500

@app.route('/set_motor_mode', methods=['POST'])
def set_motor_mode():
    mode = request.json.get('mode')  # Get the mode (manual or scheduled)
    
    if mode == 'scheduled':
        # Execute scheduled mode command
        command = f"/usr/bin/mosquitto_pub -h {MQTT_BROKER} -p {MQTT_PORT} -t {MQTT_MOTOR_CMD_TOPIC} -m '{{\"cmd\": -1}}'"
    elif mode == 'manual':
        # Execute manual mode command
        command = f"/usr/bin/mosquitto_pub -h {MQTT_BROKER} -p {MQTT_PORT} -t {MQTT_MOTOR_CMD_TOPIC} -m '{{\"cmd\": 1}}'"
    else:
        return jsonify({"status": "error", "message": "Invalid mode!"}), 400
    
    try:
        subprocess.run(command, shell=True, check=True)
        return jsonify({"status": "success", "message": f"Motor mode set to {mode}!"}), 200
    except subprocess.CalledProcessError:
        return jsonify({"status": "error", "message": f"Failed to set motor mode to {mode}!"}), 500

@app.route('/send_schedule', methods=['POST'])
def send_schedule():
    # Get values from the form
    time_period = request.form.get('time_period')
    duration = request.form.get('duration')

    # Validate the inputs
    if time_period and duration:
        try:
            # Send the values via MQTT (mosquitto_pub)
            mqtt_message = f'{{"Duration": {duration}, "TimePeriod": {time_period}}}'
            subprocess.run(['/usr/bin/mosquitto_pub', '-h', MQTT_BROKER, '-p', str(MQTT_PORT), '-t', MQTT_SCHEDULE_TOPIC, '-m', mqtt_message])

            return jsonify({"status": "success", "message": f"Scheduled command sent: {mqtt_message}"}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": f"Error sending MQTT message: {e}"}), 500
    else:
        return jsonify({"status": "error", "message": "Please provide both TimePeriod and Duration."}), 400
    
@app.route('/firmware.bin', methods=['GET'])
def serve_firmware():
    # Serve the firmware file to the ESP32 on request
    return send_from_directory(FIRMWARE_DIR, FIRMWARE_FILE)

if __name__ == '__main__':
    # Start the server on port 5000
    app.run(host='0.0.0.0', port=5000)
