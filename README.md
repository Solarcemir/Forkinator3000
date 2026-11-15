# Forkinator 3000

A fork that refuses to feed you. An HC-SR04 ultrasonic sensor on the fork watches the food. When you lower the fork to take a bite, an SG90 servo flicks the head 90° and you miss.

A web page on your laptop turns every miss into a show:
- Plankton takes over the whole screen.
- Bob, a Pou-style blob wearing your face, gets slimmer.
- Bob also gives you terrible fitness advice, powered by Gemini.

## How it works

```
 ┌──────────── fork ────────────┐        USB serial         ┌──────────── laptop ─────────────┐
 │ HC-SR04 ──> ESP32 ──> SG90   │  ── "DIST:12.3" ──────>   │ overlord-bob.html (Chrome)      │
 │  (distance)   │    (flick 90°)│  ── "BEND" ───────────>   │  • Plankton full-screen + sound │
 └───────────────┼──────────────┘      115200 baud          │  • Bob slims, menu updates      │
                 └ decides on its own, the page only watches │  • webcam: face + jumping jacks │
                                                             │        │ POST /api/bob           │
                                                             │  server.py ──> Gemini API       │
                                                             └─────────────────────────────────┘
```

1. **The fork decides by itself.** The ESP32 reads the HC-SR04 every 60 ms. If the food is 6 cm or closer on 2 readings in a row, it turns the servo to 90°, holds it 0.9 s and turns it back. A 1.5 s cooldown stops it from re-firing. The fork works without the laptop.
2. **It reports to the page.** Over USB serial at 115200 baud, the ESP32 prints `DIST:<cm>` every 200 ms and `BEND` on every flick. The page connects with the Web Serial API (Chrome/Edge).
3. **The page reacts to every `BEND`:**
   - Plankton (`assets/plankton.jpeg` + `sounds/plankton.mp3`) slams in over the whole screen for 2.5–4 s.
   - The fork on screen flips.
   - A random food is crossed off the "Menu of Shame" board.
   - The calories you didn't eat make Bob slimmer.
4. **Bob's size is your progress.** Bob goes from ~170 kg ("Chunky Bob") down to ~45 kg ("OVERLORD BOB").
   - Fork flicks and jumping jacks slim him down. Feeding him (card 2) fattens him up.
   - Every change animates the body and pops a red **FATTER** or green **SLIMMER** badge.
5. **Your face on Bob.** You take a photo with the webcam.
   - MediaPipe finds your eyes, nose and mouth.
   - Each one is cut out, recolored to Bob's skin and placed at a fixed spot on Bob. The light and shadow are kept, so it still looks like you.
6. **Jumping jacks.** MediaPipe Pose tracks your wrists, head and shoulders. Hands above your head, then below your shoulders, counts as 1 rep.
7. **BobGPT.** The chat sends your question to `server.py`, which asks Gemini with a prompt that makes Bob confidently useless. The API key stays on the server, in `.env`.

Video from the webcam is processed in the browser and never uploaded.

## Project files

```
overlord-bob.html                    the whole web UI (single file, no build step)
server.py                            local server: serves the page + proxies the chat to Gemini
firmware/forkinator/forkinator.ino   ESP32 firmware (Arduino)
assets/                              Pou eyes/smile and the Plankton image
sounds/                              Plankton sound(s)
worker/bobgpt-worker.js              optional Cloudflare Worker, only for hosting the page online
.env                                 your Gemini key (you create it, never committed)
```

## 1. Run the web UI

You need Python 3 (no extra packages) and Chrome or Edge on desktop.

```bash
git clone https://github.com/Solarcemir/Forkinator3000.git
cd Forkinator3000
git checkout pou
```

Create a file called `.env` in the project folder with a [Gemini API key](https://aistudio.google.com/apikey):

```
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-flash-lite-latest
```

Start the server:

```bash
python server.py
```

Open **http://localhost:8765/overlord-bob.html**.

- Without a `.env`, everything still works, and Bob answers with canned jokes instead of Gemini.
- Don't open the HTML file directly from disk. The camera and USB connection only work over `http://localhost`.
- Face detection and jumping jacks load the MediaPipe models from the internet the first time.

### Controls

| Key | Action |
|---|---|
| `1` | Put your face on Bob (webcam or photo upload) |
| `2` | Feed Bob a burger (fatter) |
| `3` / `Space` | Simulate a fork flick |
| `4` | Connect the real fork over USB |
| `5` | Jumping jacks (slimmer) |
| 🎩 Style | Hats, glasses and extras for Bob |
| 💬 | Ask Bob something |

Without hardware, drag the distance slider in the sensor panel to 6 cm or less to trigger a flick.

## 2. Build and flash the fork

### Parts
ESP32 DevKit, HC-SR04, SG90 servo, a metal spoon or fork, and wires. Recommended extras: 1 kΩ + 2 kΩ resistors and a 1000 µF capacitor.

### Wiring (soldered, no breadboard)

| Part | Pin | Connect to |
|---|---|---|
| SG90 servo | signal (orange) | ESP32 GPIO 18 |
| SG90 servo | + (red) / − (brown) | 5 V / GND |
| HC-SR04 | Trig | ESP32 GPIO 26 |
| HC-SR04 | Echo | ESP32 GPIO 27 (see note) |
| HC-SR04 | VCC / GND | 5 V / GND |

- **Echo outputs 5 V when the sensor runs on 5 V, and ESP32 pins are 3.3 V.** Put a 1 kΩ resistor in series and a 2 kΩ resistor to GND. It works without them for a demo, but the pin can wear out over time.
- **The HC-SR04 needs 5 V.** On 3.3 V it gives garbage readings (~2 cm all the time), which makes the servo fire non-stop.
- A 1000 µF capacitor across the servo's 5 V and GND stops the ESP32 from resetting when the servo moves.
- **Mount the servo on its side**, with the shaft pointing sideways out of the handle. The horn then swings up and down instead of sideways. Glue or zip-tie the spoon to the horn.
- Point the sensor the same way the spoon points, so it "sees" the food the spoon is approaching.

### Flash the firmware

**Option A: Arduino IDE**
1. Install the [Arduino IDE](https://www.arduino.cc/en/software).
2. Add the ESP32 boards:
   - Go to **File → Preferences → Additional boards manager URLs** and add `https://espressif.github.io/arduino-esp32/package_esp32_index.json`.
   - Then go to **Tools → Board → Boards Manager**, search for **esp32** and install it.
3. Go to **Tools → Manage Libraries** and install **ESP32Servo** (by Kevin Harrington).
4. Open `firmware/forkinator/forkinator.ino`, choose **ESP32 Dev Module** and your COM port, then click **Upload**.

**Option B: arduino-cli** (replace `COM9` with your port; `arduino-cli board list` shows it)
```bash
arduino-cli core install esp32:esp32
arduino-cli lib install ESP32Servo
arduino-cli compile --upload -p COM9 --fqbn esp32:esp32:esp32 firmware/forkinator
```

Check it works: open a serial monitor at **115200** baud. You should see `DIST:` lines, and `BEND` when you put your hand close to the sensor.

### Tuning (in the firmware)

| Setting | Default | What it does |
|---|---|---|
| `PIN_SERVO`, `PIN_TRIG`, `PIN_ECHO` | 18, 26, 27 | GPIO pins |
| `TRIGGER_CM` | 6 | Distance that triggers a flick. Also change `TRIGGER_CM` in the HTML. |
| `SERVO_FLICK` | 90° | How far the servo turns |
| `HOLD_MS` | 900 ms | How long it stays turned |
| `COOLDOWN_MS` | 1500 ms | Minimum time between flicks |

## 3. Connect the fork to the page

1. Plug the ESP32 into the laptop with USB.
2. Close any serial monitor. Only one program can use the port at a time.
3. On the page, press **4 · Connect the real fork**, pick the ESP32's port and allow access.

The dot in the sensor panel turns green, and from then on the live distance and every flick show up on screen. The page and firmware both use **115200** baud. If you change it, change `BAUD` in the HTML and `Serial.begin` in the firmware.

## 4. Customize

| What | Where |
|---|---|
| Plankton image / sounds | `PLANKTON_IMG`, `PLANKTON_SOUNDS` at the top of the script. Add `sounds/plankton2.mp3` etc. for variety. |
| How long Plankton covers the screen | `PLANK_MS` (minimum, default 2500 ms) |
| Calories per jumping jack | `JACK_CAL` (default 150) |
| Calories from fat Bob to Overlord | `GOAL` (default 6000) |
| Where your eyes / nose / mouth go on Bob, skin color | `SPOT`, `BOB_SKIN` in `fuseFace` |
| Bob's personality | `SYSTEM` in `server.py` |
| Gemini model | `GEMINI_MODEL` in `.env` |

The style picks, your face photo and the Googly-eyes option are saved in the browser (localStorage). To start fresh, clear the site data.

## Hosting online (optional)

`server.py` is for running locally. To put the page on a static host (GitHub Pages), the chat needs a backend somewhere else:
1. Deploy `worker/bobgpt-worker.js` as a Cloudflare Worker, with your key as a Worker secret.
2. Set `PROXY_URL` in the HTML to the Worker's URL.

Never put an API key in the HTML.

## Troubleshooting

| Problem | Fix |
|---|---|
| Servo fires non-stop, distance ~2 cm | HC-SR04 is on 3.3 V. Move VCC to 5 V, and point it at open space to test. |
| ESP32 resets when the servo moves | Add the 1000 µF capacitor, or power the servo from a stronger 5 V source |
| "Connect the real fork" does nothing | Use Chrome/Edge, open the page via `http://localhost`, close other serial monitors |
| Bob only tells canned jokes | `.env` missing or wrong key. Check the `server.py` console for the Gemini error. |
| Camera doesn't open | Allow camera access in the address bar. The page must be on `http://localhost`. |
| Buttons do nothing | Hard-reload (Ctrl+F5). If it persists, open DevTools (F12) → Console and check for errors. |
