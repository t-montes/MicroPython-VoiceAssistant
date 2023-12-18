import env
from machine import Pin
from time import sleep, time
from network import WLAN, STA_IF
from requests import get, post
from gc import mem_alloc, mem_free
from os import urandom
from ubinascii import hexlify

# ------------------ CONSTANTS ------------------

builtin_led = Pin(2, Pin.OUT)

# ------------------ UTIL FUNCTIONS ------------------

def status():
    print(f"Memory currently in use: {(mem_alloc()/1e3):.1f} kB")
    print(f"Memory currently available: {(mem_free()/1e3):.1f} kB")

def blink(times, delay):
    lap = 0
    while lap < times:
        builtin_led.on()
        sleep(delay / 2)
        builtin_led.off()
        sleep(delay / 2)
        lap += 1

def connect():
    wlan = WLAN(STA_IF)
    wlan.active(True)

    tries = 0
    while (tries := tries + 1) <= 3:
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
    if tries > 3:
        raise Exception("Error connecting to Wi-Fi")

def test_get():
    start_time = time()
    url = f'http://{env.SERVER_HOST}:{env.SERVER_PORT}/test-get'
    print("Testing HTTP GET...")
    response = get(url)
    try:
        assert (response.status_code == 200), f"Error in test GET [{response.status_code}]: {response.text}"
        print(f"Test GET (first access) successful in: {time() - start_time:.2f} s")
        blink(3, 0.2)
    except Exception as e:
        print(e)
        blink(1, 1)

def test_post():
    start_time = time()
    # create sample audio file
    with open('sample-request.wav', 'wb') as f:
        f.write(b'this is a sample of what the system would receive from the microphone')
    
    url = f'http://{env.SERVER_HOST}:{env.SERVER_PORT}/test'
    boundary = '----WebKitFormBoundary' + hexlify(urandom(16)).decode()
    headers = {'Content-Type': 'multipart/form-data; boundary=%s' % boundary}

    body = ('--%s\r\n' % boundary +
            'Content-Disposition: form-data; name="audio"; filename="sample-request.wav"\r\n' +
            'Content-Type: audio/wav\r\n\r\n').encode('utf-8')
    with open('sample-request.wav', 'rb') as f:
        body += f.read()
    body += ('\r\n--%s--\r\n' % boundary).encode('utf-8')

    print("Testing HTTP POST...")
    response = post(url, headers=headers, data=body)
    
    try:
        assert (response.status_code == 200), f"Error in test POST [{response.status_code}]: {response.text}"
        #assert (response.content == b'sample audio'), f"Error in test POST: response content is not the same as the request content"

        with open('sample-response.wav', 'wb') as f:
            f.write(response.content)

        print(f"Test POST successful in: {time() - start_time:.2f} s")
        blink(3, 0.2)
    except Exception as e:
        print(e)
        blink(1, 1)

# ------------------ MAIN ------------------

def main():
    blink(5, 0.1) # hello
    wlan, ip = connect()
    test_get()
    test_post()

    # TODO: record audio
    # TODO: send audio to server
    # TODO: speak response

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
# it's possible to access the Python REPL with PuTTY at Serial 115200 bauds
