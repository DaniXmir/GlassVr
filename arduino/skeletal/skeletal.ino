//skeletal only, can be used to add extra skeletal inputs to controllers that dont support like quest via hooks!

// safe pins!

// analog:
// 32,33,34,35,36(VP),39(VN)

// digital only:
// 16,17,18,19,21,22,23

// digital (no analog with wifi):
// 4,13,14,25,26,27

// avoid:
// 0,1,2,3,6,7,8,9,10,11,12,15

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>

#define WIFI_SSID         "wifi_name" //statistically its probably just your dad's name
#define WIFI_PASSWORD     "wifi_password" //statistically its probably your dad's phone number lol

#define SERIAL_BAUD       115200
#define USE_BLUETOOTH     0 //1 to enable bluetooth ()
#define BT_DEVICE_NAME    "GlassVR cr" //only used for bluetooth, can be anything

#define SEND_INTERVAL_MS  10//send rate
#define HEARTBEAT_MS      250
#define CHANGE_EPSILON    0.002f
#define OVERSAMPLE        8
#define ANALOG_SMOOTHING  0.5f
#define DIGITAL_SMOOTHING 0.35f//idk claude
#define DEBOUNCE_MS       20
#define WIFI_RETRY_MS     5000

#define TARGET_IP         "255.255.255.255" //255.255.255.255 is a special broadcast ip, if it doesnt work then get you pc ip by typing "ipconfig" in cmd
#define UDP_PORT          9002 //hmd=9000 right=9001 left=9002 0tracker=9003...

WiFiUDP udp;
static bool udpStarted = false;

enum FingerId { F_THUMB = 0, F_INDEX, F_MIDDLE, F_RING, F_PINKY, FINGER_COUNT };
enum InputMode { IN_NONE = 0, IN_ANALOG, IN_DIGITAL };

struct Channel {
  const char* name;
  InputMode   mode;
  int8_t      pin;
  bool        activeLow;   // digital only
  int         rawMin;      // analog only
  int         rawMax;      // analog only
  bool        invert;      // analog only
  float       pressed;     // value at full press / rawMax
  float       released;    // value at rest / rawMin, also the temp value for IN_NONE
  float       value;       // current value
  float       sent;        // value at the last send
  bool        stable;      // digital: debounced state, true = pressed
  bool        lastRead;    // digital: raw state at the last sample
  uint32_t    lastChange;  // digital: ms of the last raw change
};

Channel curl[FINGER_COUNT] = {
  // name      mode        pin  activeLow rawMin rawMax invert pressed released value sent stable lastRead lastChange
  { "thumb",   IN_NONE,    -1,  true,     0,     4095,  false,  1.0f,   0.0f,    0,    0,   false, false,   0 },
  { "index",   IN_NONE,    -1,  true,     0,     4095,  false,  1.0f,   0.0f,    0,    0,   false, false,   0 },
  { "middle",  IN_NONE,    -1,  true,     0,     4095,  false,  1.0f,   0.0f,    0,    0,   false, false,   0 },
  { "ring",    IN_ANALOG, 32,  true,     0,     4095,  false,  1.0f,   0.0f,    0,    0,   false, false,   0 },
  { "pinky",   IN_ANALOG, 33,  true,     0,     4095,  false,  1.0f,   0.0f,    0,    0,   false, false,   0 },
};

Channel splay[FINGER_COUNT] = {
  // name      mode        pin  activeLow rawMin rawMax invert pressed released value sent stable lastRead lastChange
  { "thumb",   IN_NONE,    -1,  true,     0,     4095,  false,  1.0f,   0.0f,    0,    0,   false, false,   0 },
  { "index",   IN_NONE,    -1,  true,     0,     4095,  false,  1.0f,   0.0f,    0,    0,   false, false,   0 },
  { "middle",  IN_NONE,    -1,  true,     0,     4095,  false,  1.0f,   0.0f,    0,    0,   false, false,   0 },
  { "ring",    IN_NONE,    -1,  true,     0,     4095,  false,  1.0f,   0.0f,    0,    0,   false, false,   0 },
  { "pinky",   IN_NONE,    -1,  true,     0,     4095,  false,  1.0f,   0.0f,    0,    0,   false, false,   0 },
};

#if USE_BLUETOOTH
#include "BluetoothSerial.h"
BluetoothSerial SerialBT;
#endif

// ---------------------------------------------------------------------------------------------

float readRaw(uint8_t pin) {
  uint32_t sum = 0;
  for (int i = 0; i < OVERSAMPLE; i++) sum += analogRead(pin);
  return (float)sum / (float)OVERSAMPLE;
}

void writeSerialAndBT(const char* data, size_t len) {
  Serial.write((const uint8_t*)data, len);
#if USE_BLUETOOTH
  SerialBT.write((const uint8_t*)data, len);
#endif
}

void initChannel(Channel& c) {
  c.value = c.released;
  c.sent = c.released;
  if (c.pin < 0) return;

  if (c.mode == IN_ANALOG) {
    pinMode(c.pin, INPUT);
    analogSetPinAttenuation(c.pin, ADC_11db);
  } else if (c.mode == IN_DIGITAL) {
    pinMode(c.pin, INPUT_PULLUP);
  }
}

// Reads one channel, smooths it, returns true when it moved enough since the last send to be worth sending.
bool updateChannel(Channel& c, bool first) {
  float target = c.released;
  float k = 1.0f;

  if (c.mode == IN_ANALOG && c.pin >= 0) {
    const float raw = readRaw((uint8_t)c.pin);
    float t = 0.0f;
    if (c.rawMax != c.rawMin) t = (raw - (float)c.rawMin) / (float)(c.rawMax - c.rawMin);
    if (t < 0.0f) t = 0.0f;
    if (t > 1.0f) t = 1.0f;
    if (c.invert) t = 1.0f - t;
    target = c.released + t * (c.pressed - c.released);
    k = ANALOG_SMOOTHING;
  }
  else if (c.mode == IN_DIGITAL && c.pin >= 0) {
    const uint32_t now = millis();
    bool down = (digitalRead(c.pin) == (c.activeLow ? LOW : HIGH));
    if (c.invert) down = !down;

    if (first) {
      c.stable = down;
      c.lastRead = down;
      c.lastChange = now;
    } else if (down != c.lastRead) {
      c.lastRead = down;               // changed / bounced: restart the debounce timer
      c.lastChange = now;
    } else if (down != c.stable && now - c.lastChange >= DEBOUNCE_MS) {
      c.stable = down;                 // held long enough: accept
    }
    target = c.stable ? c.pressed : c.released;
    k = DIGITAL_SMOOTHING;
  }

  if (first || k >= 1.0f) {
    c.value = target;
  } else {
    c.value += k * (target - c.value);
    float left = target - c.value;
    if (left < 0) left = -left;
    if (left < 0.005f) c.value = target;   // finish the ramp, no endless tiny updates
  }

  float moved = c.value - c.sent;
  if (moved < 0) moved = -moved;
  return moved >= CHANGE_EPSILON;
}

void sendData() {
  // "skl thumb=0.000 ... pinky=0.000 thumb_splay=0.000 ... pinky_splay=0.000\n" is ~190 chars
  char buf[320];
  int n = snprintf(buf, sizeof(buf), "skl");

  double flexions[20] = { 0 };
  double splays[5] = { 0 };

  for (int i = 0; i < FINGER_COUNT; i++) {
    if (n < 0 || n >= (int)sizeof(buf) - 48) break;

    n += snprintf(buf + n, sizeof(buf) - n, " %s=%.3f", curl[i].name, curl[i].value);
    n += snprintf(buf + n, sizeof(buf) - n, " %s_splay=%.3f", splay[i].name, splay[i].value);

    curl[i].sent = curl[i].value;
    splay[i].sent = splay[i].value;
    flexions[i * 4] = (double)curl[i].value;    // thumb 0, index 4, middle 8, ring 12, pinky 16
    splays[i]       = (double)splay[i].value;   // thumb 0, index 1, middle 2, ring 3, pinky 4
  }

  // 1. Serial / Bluetooth text line
  buf[n++] = '\n';
  writeSerialAndBT(buf, (size_t)n);

  // 2. UDP packet: "skl" + 20 doubles + 5 doubles (= PacketSkeletal)
  if (WiFi.status() == WL_CONNECTED) {
    udp.beginPacket(TARGET_IP, UDP_PORT);
    udp.write((const uint8_t*)"skl", 3);
    udp.write((const uint8_t*)flexions, sizeof(flexions));
    udp.write((const uint8_t*)splays, sizeof(splays));
    udp.endPacket();
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  analogReadResolution(12);

  for (int i = 0; i < FINGER_COUNT; i++) {
    initChannel(curl[i]);
    initChannel(splay[i]);
  }

#if USE_BLUETOOTH
  SerialBT.begin(BT_DEVICE_NAME);
#endif

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to Wi-Fi");

  unsigned long startAttemptTime = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 15000) {
    delay(500);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConnected! IP: " + WiFi.localIP().toString());
    udp.begin(UDP_PORT);
    udpStarted = true;
  } else {
    Serial.println("\nWi-Fi Connection Failed! Continuing with Serial/Bluetooth only.");
  }
}

void loop() {
  static uint32_t lastSample = 0;
  static uint32_t lastSend = 0;
  static uint32_t lastWifiTry = 0;
  static bool first = true;

  const uint32_t now = millis();

  if (WiFi.status() == WL_CONNECTED) {
    if (!udpStarted) {
      udp.begin(UDP_PORT);
      udpStarted = true;
      Serial.println("Wi-Fi connected! IP: " + WiFi.localIP().toString());
    }
  } else {
    udpStarted = false;
    if (now - lastWifiTry >= WIFI_RETRY_MS) {
      lastWifiTry = now;
      WiFi.reconnect();
    }
  }

  if (!first && now - lastSample < SEND_INTERVAL_MS) return;
  lastSample = now;

  bool changed = false;
  for (int i = 0; i < FINGER_COUNT; i++) {
    if (updateChannel(curl[i], first)) changed = true;
    if (updateChannel(splay[i], first)) changed = true;
  }

  if (first || changed || now - lastSend >= HEARTBEAT_MS) {
    sendData();
    lastSend = now;
  }
  first = false;
}