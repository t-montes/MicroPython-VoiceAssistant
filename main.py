from machine import Pin
import time
import network
import env
import requests
import json
import gc

# ------------------ CONSTANTS ------------------

builtin_led = Pin(2, Pin.OUT)

# ------------------ UTIL FUNCTIONS ------------------

def status():
    print("Memory currently in use:", gc.mem_alloc(), "bytes")
    print("Memory currently available:", gc.mem_free(), "bytes")

def blink(times, delay):
    lap = 0
    while lap < times:
        builtin_led.on()
        time.sleep(delay / 2)
        builtin_led.off()
        time.sleep(delay / 2)
        lap += 1

def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    while True:
        print("Connecting to Wi-Fi", env.WIFI_SSID, "...")
        try:
            wlan.connect(env.WIFI_SSID, env.WIFI_PASSWORD)
            while not wlan.isconnected():
                pass  # Wait for the connection to establish
            blink(3, 0.2)
            ip = wlan.ifconfig()[0]
            print("IP address:", ip)
            return wlan, ip
        except Exception as e:
            print("Error connecting:", e)
            blink(1, 1)

def test_post():
    print("Testing HTTP POST...")
    url = 'https://jsonplaceholder.typicode.com/posts'
    data = {
        'title': 'test',
        'working': 'yes',
    }
    json_data = json.dumps(data)
    headers = {'Content-type': 'application/json; charset=UTF-8'}
    response = requests.post(url, data=json_data, headers=headers)
    assert response.status_code == 201, "Error in HTTP POST"
    print(response.json())
    blink(3, 0.2)

# ------------------ MAIN ------------------

def main():
    wlan, ip = connect()
    test_post()

    # TODO: speech to text to receive voice commands and print them

if __name__ == '__main__':
    main()

# 1 blink: error
# 3 blinks: success

# to upload:
# ampy --port /dev/ttyUSB0 put main.py
# ampy --port /dev/ttyUSB0 put env.py

# to run:
# ampy --port /dev/ttyUSB0 run main.py
# or, as main.py is the default file, just press EN button on ESP32
