from flask import Flask, send_from_directory
import os

app = Flask(__name__)

# Set the path to your firmware binary file
FIRMWARE_DIR = '../firmwares/'  # Change this to the path of your firmware folder
FIRMWARE_FILE = 'firmware.bin'  # Name of the firmware binary file

@app.route('/')
def hello():
    return "Welcome to the OTA update server!"

@app.route('/firmware.bin', methods=['GET'])
def serve_firmware():
    # Serve the firmware file to the ESP32 on request
    return send_from_directory(FIRMWARE_DIR, FIRMWARE_FILE)

if __name__ == '__main__':
    # Start the server on port 5000 (or any other port you prefer)
    app.run(host='0.0.0.0', port=5000)
