# Forkinator 3000

A fork that refuses to feed you. An HC-SR04 sensor on the fork watches the food. When you lower the fork to grab a bite, an SG90 servo flicks the head 90° and you miss. A web page shows Bob, a blob who reacts to every miss. Bob can wear your face, and every miss plays a Plankton sound.

```
overlord-bob.html                    the web UI (single file, no build step)
firmware/forkinator/forkinator.ino   ESP32 firmware (Arduino)
sounds/                              put your Plankton clips here (not in the repo)
```

## 1. Run the web UI

The page has to be served over `http://localhost`. If you open it straight from disk, the camera and Web Serial don't work.

```bash
git clone https://github.com/Solarcemir/Forkinator3000.git
cd Forkinator3000
python -m http.server 8765
```

Then open **http://localhost:8765/overlord-bob.html** in **Chrome or Edge** on desktop. Web Serial only works in those two.

### Plankton sounds

Create a `sounds/` folder and add your clips:

```
sounds/plankton.mp3
sounds/plankton2.mp3   (optional)
sounds/plankton3.mp3   (optional)
```

To use other file names, edit `PLANKTON_SOUNDS` at the top of the `<script>` in `overlord-bob.html`. If a file is missing, the page plays a synthesized "boing" instead.

### Controls

| Key | Action |
|---|---|
| `1` | Put your face on Bob (webcam or photo upload) |
| `2` | Feed Bob |
| `3` / `Space` | Simulate a fork flick |
| `4` | Connect the real fork over USB |

Without hardware, drag the distance slider in the sensor panel down to 6 cm or less to trigger a flick.

## 2. Flash the ESP32

1. Install the [Arduino IDE](https://www.arduino.cc/en/software).
2. Add the ESP32 boards: **File → Preferences → Additional boards manager URLs**:
   `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
   Then **Tools → Board → Boards Manager**, search for **esp32** and install it.
3. **Tools → Manage Libraries**, search for **ESP32Servo** (by Kevin Harrington) and install it.
4. Open `firmware/forkinator/forkinator.ino`, select **ESP32 Dev Module** and your COM port, then click **Upload**.
5. Optional check: open the Serial Monitor at **115200** baud. You should see `DIST:<cm>` lines, plus `BEND` each time the servo flicks.

### Wiring (soldered, no breadboard)

| Part | Pin | ESP32 |
|---|---|---|
| SG90 servo | signal (orange) | GPIO 18 |
| SG90 servo | + (red) / − (brown) | 5 V / GND |
| HC-SR04 | Trig | GPIO 26 |
| HC-SR04 | Echo | GPIO 27 **through a divider** (1 kΩ in series, 2 kΩ to GND) |
| HC-SR04 | VCC / GND | 5 V / GND |

- **Echo outputs 5 V and the ESP32 pins are not 5 V tolerant.** Don't skip the divider.
- Solder a 1000 µF capacitor across the servo's 5 V and GND. Without it, the ESP32 resets every time the servo moves.
- For battery power, use a 1S LiPo with a charge + 5 V boost module.

### Tuning

These values are in the firmware:

| Setting | Default | What it does |
|---|---|---|
| `TRIGGER_CM` | 6 | Distance that triggers a flick. Keep it in sync with `TRIGGER_CM` in the HTML. |
| `SERVO_FLICK` | 90° | How far the servo turns. |
| `HOLD_MS` | 900 ms | How long it stays turned. |
| `COOLDOWN_MS` | 1500 ms | Minimum time between flicks. |

## 3. Connect the fork to the page

Plug the ESP32 in over USB. On the page, click **Connect the real fork**, pick its port and allow access. The dot in the sensor panel turns green. From then on, the live distance and every flick show up on screen.

Close the Arduino Serial Monitor first. Only one program can use the port at a time.
