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
        print("[LOG] Wi-Fi: connecting…")
        sta.connect(ssid, password)
        start = time.ticks_ms()
        while not sta.isconnected():
            if time.ticks_diff(time.ticks_ms(), start) > (timeout_s * 1000):
                print("[WARN] Wi-Fi: connect timeout")
                return None
            time.sleep(0.2)
    print("[LOG] Wi-Fi: connected", sta.ifconfig())
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
print("[LOG] Listening on", addr)

def toggle_gate():
    print("[LOG] Gate toggle start")
    relay.value(1)
    time.sleep(1)
    relay.value(0)
    print("[LOG] Gate toggle end")

def http_send(conn, body, code=200, ctype="text/html"):
    try:
        conn.send("HTTP/1.1 {} OK\r\n".format(code))
        conn.send("Content-Type: {}\r\n".format(ctype))
        conn.send("Connection: close\r\n\r\n")
        conn.sendall(body if isinstance(body, str) else str(body))
        print("[LOG] Sent response with code", code, "| length:", len(body))
    except Exception as e:
        print("[ERR] Send failed:", e)
        raise

def ensure_wifi(ssid, password):
    sta = network.WLAN(network.STA_IF)
    if not sta.isconnected():
        print("[WARN] Wi-Fi dropped, reconnecting…")
        sta.connect(ssid, password)
        for _ in range(50):  # ~10s timeout
            if sta.isconnected():
                print("[LOG] Wi-Fi reconnected", sta.ifconfig())
                break
            time.sleep(0.2)

while True:
    try:
        ensure_wifi(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)
        conn, addr = s.accept()
        print("[LOG] Accepted connection from", addr)
        start = time.ticks_ms()

        conn.settimeout(1.0)  # shorter wait for idle sockets
        try:
            req = conn.recv(1024)
        except OSError as oe:
            # 110 = ETIMEDOUT (client connected but sent nothing)
            if getattr(oe, "args", [None])[0] == 110:
                print("[INFO] Idle connection (no data), closed")
                conn.close()
                continue
            raise
        finally:
            conn.settimeout(None)


        first_line = req.split(b"\r\n", 1)[0]
        try:
            print("[LOG] Request:", first_line.decode())
        except:
            print("[LOG] Request (raw):", first_line)

        path, query = parse_request_path(req)
        print("[LOG] Parsed path:", path)

        code = 200

        if path == "/":
            body = html_page(led_state)

        elif path == "/led_on":
            LED.on()
            led_state = "ON"
            print("[LOG] Action: LED ON")
            body = html_page(led_state)

        elif path == "/led_off":
            LED.off()
            led_state = "OFF"
            print("[LOG] Action: LED OFF")
            body = html_page(led_state)

        elif path == "/toggle_gate":
            toggle_gate()
            body = html_page("TOGGLED")

        else:
            code, body = 404, "Not Found"
            print("[WARN] 404 Not Found:", path)

        http_send(conn, body, code=code)
        conn.close()

        elapsed = time.ticks_diff(time.ticks_ms(), start)
        print("[LOG] Served", path, "in", elapsed, "ms | free mem:", gc.mem_free())

        gc.collect()
    except OSError as oe:
        try: conn.close()
        except: pass
        print("[ERR] OSError:", oe)
        print("[WARN] Connection closed due to OSError")
    except Exception as e:
        try: conn.close()
        except: pass
        print("[ERR] Exception:", e)
        gc.collect()

