# Pico Gate Controller (MicroPython, Raspberry Pi Pico W)
# Last Updated: 23 Aug 2025

try:
    import usocket as socket
except:
    import socket

import network, time, gc
from machine import Pin
from utils import parse_request_path, html_page

try:
    import secrets  # user-created, ignored by git
except ImportError:
    # Fallback: define secrets directly here if no secrets.py exists
    class secrets:
        WIFI_SSID = ""
        WIFI_PASSWORD = ""

# --- GPIO setup ---
gc.collect()
RELAY_PIN = 20
relay = Pin(RELAY_PIN, Pin.OUT)
relay.value(0)

LED = Pin("LED", Pin.OUT)
led_state = "OFF"

# --- Wi-Fi connect ---
def connect_wifi(ssid, password, timeout_s=20):
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if not sta.isconnected():
        sta.connect(ssid, password)
        start = time.ticks_ms()
        while not sta.isconnected():
            if time.ticks_diff(time.ticks_ms(), start) > (timeout_s * 1000):
                return None
            time.sleep(0.2)
    return sta

sta = connect_wifi(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)
if sta:
    print("Wi-Fi connected:", sta.ifconfig())
else:
    print("Wi-Fi connection failed.")

# --- HTTP server ---
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(5)
print("Listening on", addr)

def toggle_gate():
    relay.value(1)
    time.sleep(1)
    relay.value(0)

def http_send(conn, body, code=200, ctype="text/html"):
    conn.send("HTTP/1.1 {} OK\r\n".format(code))
    conn.send("Content-Type: {}\r\n".format(ctype))
    conn.send("Connection: close\r\n\r\n")
    conn.sendall(body if isinstance(body, str) else str(body))

while True:
    try:
        conn, addr = s.accept()
        conn.settimeout(3.0)
        req = conn.recv(1024)
        conn.settimeout(None)

        path, query = parse_request_path(req)

        global led_state
        code = 200

        if path == "/":
            body = html_page(led_state)

        elif path == "/led_on":
            LED.on()
            led_state = "ON"
            body = html_page(led_state)

        elif path == "/led_off":
            LED.off()
            led_state = "OFF"
            body = html_page(led_state)

        elif path == "/toggle_gate":
            toggle_gate()
            body = html_page("TOGGLED")

        else:
            code, body = 404, "Not Found"

        http_send(conn, body, code=code)
        conn.close()
        gc.collect()
    except OSError:
        try: conn.close()
        except: pass
        print("Connection closed")
    except Exception as e:
        try: conn.close()
        except: pass
        print("Error:", e)
        gc.collect()
