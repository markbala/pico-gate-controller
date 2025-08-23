# Raspberry Pi Pico W - Gate Controller via Relay Switch

- A lightweight web server that runs on a **Raspberry Pi Pico W** to toggle a relay switch.
- Easily integrated into Home Assistant to work with sensors, automations and scripts
- For my purposes, the relay switch is soldered to a 433Mhz gate controller to close the switch and simulate a physical button press.

---

## Features

- Minimal HTTP server with routes:
  - `/` – simple UI page
  - `/led_on`, `/led_off` – onboard LED control, I used this to make sure everything was working before soldering the relay to the Pico Pi
  - `/toggle_gate` – pulse a relay for 1s (**GPIO 20** by default, but check the pinout to confirm that you are soldered to the right GPIO) 
- No external CSS/JS dependencies — small footprint for MicroPython

---

## Hardware

- **Raspberry Pi Pico W**
- **1-channel Relay Switch**
- **433MHz (or 330MHz) Gate Controller**
- Connect the Gate Controller to the Relay Module, and the Relay Module to **GPIO 20** of the Pico Pi (adjustable in `main.py`)
- 3.3V logic — ensure your relay board is compatible
---

## Demo

![Pico Gate Controller UI](docs/demo_screenshot1.png)
![Pico Pi + Relay + Gate Controller ](docs/demo_screenshot2.jpeg)
---

## Setup

### 1. Flash MicroPython
Flash the official [MicroPython firmware](https://micropython.org/download/rp2-pico-w/) to your Pico Pi W using the Raspberry Pi instructions.

### 2. Clone this repository
```bash
git clone https://github.com/<your-username>/pico-gate-controller.git
cd pico-gate-controller
```

### 3. Input WiFi Credentials
Copy the example file:
```bash
cp src/secrets.example.py src/secrets.py
```

Edit `src/secrets.py` with your details:
```python
WIFI_SSID = "YourWiFi"
WIFI_PASSWORD = "YourPassword"

```

⚠️ **Important**:  
- `src/secrets.py` is `.gitignore`’d — never commit your real passwords.

### 4. Upload to Pico W
You need `main.py`, `utils.py`, and your `secrets.py` on the board.  

With `mpremote`:
```bash
# Upload main file
mpremote cp src/main.py :/main.py

# Upload helper module
mpremote cp src/utils.py :/utils.py

# Upload your personal secrets (do not share this file)
mpremote cp src/secrets.py :/secrets.py
```

### 5. Reboot and check
- Reboot
- Open the serial console — you should see Wi-Fi connect logs and the Pico’s IP address.  
- Visit `http://<pico-ip>/` in a browser. Should be a local IP, e.g.`http://192.168.x.x`  

## Security Notes

- No TLS
- Use only on private LANs or behind a VPN / reverse proxy (Tailscale, Cloudflare Tunnel).
- Never expose directly to the internet.

---

## 6. Home Assistant Integration

You can call the Pico endpoints from Home Assistant using `rest_command`, then wrap them in a `script` and trigger them via an `automation` or UI button.

### 1) REST Commands (`configuration.yaml`)

```yaml
rest_command:
  pico_toggle_gate:
    url: "http://PICO_IP/toggle_gate"
    method: get

  pico_led_on:
    url: "http://PICO_IP/led_on"
    method: get

  pico_led_off:
    url: "http://PICO_IP/led_off"
    method: get
```

> Replace `PICO_IP` with the IP printed in the Pico serial logs (e.g., `192.168.1.123`).

### 2) Scripts (`configuration.yaml` or `scripts.yaml`)

```yaml
script:
  toggle_gate:
    alias: Toggle Gate
    mode: single
    sequence:
      - service: rest_command.pico_toggle_gate
```

### 3) Automations

Example: Open the gate when a specific person arrives home.
Can be integrated with sensor that checks if the gate is open or closed

### 4) Lovelace Buttons (UI)

Add a **Button** card and call the script on tap:

```yaml
type: button
name: Toggle Gate
icon: mdi:gate-open
tap_action:
  action: call-service
  service: script.toggle_gate
```

**Notes**

- Home Assistant must be able to reach the Pico’s IP (same LAN/VLAN).
- If you use VLANs or firewalls, allow outbound HTTP (port 80) from Home Assistant to the Pico IP.
- The Pico server is HTTP only (no TLS). Don’t expose it directly to the internet.

## License

MIT — see [LICENSE](./LICENSE).
