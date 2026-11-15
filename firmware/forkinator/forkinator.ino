// Forkinator 3000 - ESP32 firmware
// HC-SR04 watches the food. When the fork gets too close, the servo flicks the
// spoon/fork head 90 degrees so you can't pick the food up.
// Serial protocol (115200 baud) read by overlord-bob.html:
//   DIST:<cm>   every ~200 ms
//   BEND        every time the servo flicks
// Library: "ESP32Servo" by Kevin Harrington (Arduino Library Manager).

#include <ESP32Servo.h>

const int PIN_SERVO = 18;
const int PIN_TRIG  = 26;
const int PIN_ECHO  = 27;   // through the 1k/2k divider: HC-SR04 Echo is 5 V

const float TRIGGER_CM   = 6.0;   // keep in sync with TRIGGER_CM in the page
const int   SERVO_REST   = 0;
const int   SERVO_FLICK  = 90;
const unsigned long HOLD_MS     = 900;
const unsigned long COOLDOWN_MS = 1500;
const int   HITS_NEEDED  = 2;     // consecutive close readings, filters noise

Servo servo;
unsigned long lastFlick = 0, lastReport = 0;
int hits = 0;

float readCm() {
  digitalWrite(PIN_TRIG, LOW);  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH); delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);
  unsigned long us = pulseIn(PIN_ECHO, HIGH, 25000UL);  // ~4 m max
  if (us == 0) return -1;
  return us / 58.0;
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  servo.setPeriodHertz(50);
  servo.attach(PIN_SERVO, 500, 2400);
  servo.write(SERVO_REST);
}

void loop() {
  float cm = readCm();

  if (millis() - lastReport > 200) {
    Serial.print("DIST:");
    Serial.println(cm < 0 ? 400.0 : cm, 1);
    lastReport = millis();
  }

  hits = (cm > 0 && cm <= TRIGGER_CM) ? hits + 1 : 0;

  if (hits >= HITS_NEEDED && millis() - lastFlick > COOLDOWN_MS) {
    servo.write(SERVO_FLICK);
    Serial.println("BEND");
    delay(HOLD_MS);
    servo.write(SERVO_REST);
    lastFlick = millis();
    hits = 0;
  }

  delay(60);
}
