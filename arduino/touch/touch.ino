//touch, plz report any bugs you see!

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

#define CLICK_AT          0.95   // analog value that counts as a click
#define CAP_AT            0.05   // analog value that counts as a touch
#define JOY_DEADZONE      0.1    // analog sticks / pads below this are treated as exactly 0 (no thumb / touch noise)

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
  float       released;    // value at rest / rawMin
  float       temp;        // value sent while mode = IN_NONE
  float       value;       // current value
  float       sent;        // unused, kept so the row layout matches the other sketches
  bool        stable;      // digital: debounced state, true = pressed
  bool        lastRead;    // digital: raw state at the last sample
  uint32_t    lastChange;  // digital: ms of the last raw change
};

enum ChannelId {
  C_TRIGGER,
  C_GRIP,
  C_A,
  C_B,
  C_SYSTEM,
  C_JOY_BTN,
  C_RING,
  C_PINKY,
  C_JOY_X,
  C_JOY_Y,
  CH_COUNT
};

//although the driver does full bindings for this and every controller type it has, for simplicity this file doesnt include then all, for example capacitive inputs are merged with buttons, modify if needed!
Channel ch[CH_COUNT] = {
  // name        mode        pin  activeLow rawMin rawMax invert pressed released temp value sent stable lastRead lastChange
  { "trigger",  IN_ANALOG,  32, true,     0,     4095,  false,  1.0f,   0.0f,    0.0f, 0,    0,   false, false,   0 },   // also affets index skeletal
  { "grip",     IN_ANALOG,  33, true,     0,     4095,  false,  1.0f,   0.0f,    0.0f, 0,    0,   false, false,   0 },   // primary grip also affets middle skeletal
  { "a",        IN_DIGITAL,  16, true,     0,     4095,  false,  1.0f,   0.0f,    0.0f, 0,    0,   false, false,   0 },   // also affets thumb skeletal
  { "b",        IN_DIGITAL,  34, true,     0,     4095,  false,  1.0f,   0.0f,    0.0f, 0,    0,   false, false,   0 },   // also affets thumb skeletal
  { "system",   IN_DIGITAL,  17, true,     0,     4095,  false,  1.0f,   0.0f,    0.0f, 0,    0,   false, false,   0 },   // also affets thumb skeletal
  { "joy_btn",  IN_DIGITAL,  18, true,     0,     4095,  false,  1.0f,   0.0f,    0.0f, 0,    0,   false, false,   0 },   // also affets thumb skeletal
  { "ring",     IN_ANALOG,  34, true,     0,     4095,  false,  1.0f,   0.0f,    0.0f, 0,    0,   false, false,   0 },   // (special) also affets grip input, leaving IN_NONE will cause grip to affect ring skeletal, may cause bugs!
  { "pinky",    IN_ANALOG,  35, true,     0,     4095,  false,  1.0f,   0.0f,    0.0f, 0,    0,   false, false,   0 },   // (special) also affets grip input, leaving IN_NONE will cause grip to affect pinky skeletal, may cause bugs!
  { "joy_x",    IN_ANALOG,    36, true,     0,     4095,  false,  1.0f,   -1.0f,    0.0f, 0,    0,   false, false,   0 },   // also affets thumb splay skeletal
  { "joy_y",    IN_ANALOG,    39, true,     0,     4095,  false,  1.0f,   -1.0f,    0.0f, 0,    0,   false, false,   0 },   // also affets thumb skeletal
};

enum FingerId { F_THUMB = 0, F_INDEX, F_MIDDLE, F_RING, F_PINKY, FINGER_COUNT };
Channel splay[FINGER_COUNT] = {
  { "thumb",    IN_NONE,      -1, true,     0,     4095,  false,  1.0f,   -1.0f,    0.0f, 0,    0,   false, false,   0 }, // (special) may cause bugs!
  { "index",    IN_NONE,      -1, true,     0,     4095,  false,  1.0f,   -1.0f,    0.0f, 0,    0,   false, false,   0 }, // (special) may cause bugs!
  { "middle",   IN_NONE,      -1, true,     0,     4095,  false,  1.0f,   -1.0f,    0.0f, 0,    0,   false, false,   0 }, // (special) may cause bugs!
  { "ring",     IN_NONE,      -1, true,     0,     4095,  false,  1.0f,   -1.0f,    0.0f, 0,    0,   false, false,   0 }, // (special) may cause bugs!
  { "pinky",    IN_NONE,      -1, true,     0,     4095,  false,  1.0f,   -1.0f,    0.0f, 0,    0,   false, false,   0 }, // (special) may cause bugs!
};

//itc
struct __attribute__((packed)) PacketInputTouch {
  bool system;
  bool a_x, a_x_cap;
  bool b_y, b_y_cap;
  bool trigger_cap;
  bool joy_btn, joy_cap;
  double trigger, grip, joy_x, joy_y;
};
typedef PacketInputTouch InputPacket;
#define INPUT_TAG "itc"

#if USE_BLUETOOTH
#include "BluetoothSerial.h"
BluetoothSerial SerialBT;
#endif

static inline double maxd(double a, double b) { return a > b ? a : b; }
static inline double clamp01(double v) { return v < 0.0 ? 0.0 : (v > 1.0 ? 1.0 : v); }
static inline double deadzone(double v) { return fabs(v) < JOY_DEADZONE ? 0.0 : v; }

static inline bool on(int id) { return ch[id].value >= 0.5f; }

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
  c.value = c.temp;
  if (c.pin < 0) return;

  if (c.mode == IN_ANALOG) {
    pinMode(c.pin, INPUT);
    analogSetPinAttenuation(c.pin, ADC_11db);
  } else if (c.mode == IN_DIGITAL) {
    pinMode(c.pin, INPUT_PULLUP);
  }
}

void updateChannel(Channel& c, bool first) {
  if (c.pin < 0) { c.value = c.temp; return; }

  if (c.mode == IN_ANALOG) {
    const float raw = readRaw((uint8_t)c.pin);
    float t = 0.0f;
    if (c.rawMax != c.rawMin) t = (raw - (float)c.rawMin) / (float)(c.rawMax - c.rawMin);
    if (t < 0.0f) t = 0.0f;
    if (t > 1.0f) t = 1.0f;
    if (c.invert) t = 1.0f - t;
    const float target = c.released + t * (c.pressed - c.released);
    c.value = first ? target : c.value + ANALOG_SMOOTHING * (target - c.value);
  }
  else if (c.mode == IN_DIGITAL) {
    const uint32_t now = millis();
    bool down = (digitalRead(c.pin) == (c.activeLow ? LOW : HIGH));
    if (c.invert) down = !down;

    if (first) {
      c.stable = down;
      c.lastRead = down;
      c.lastChange = now;
    } else if (down != c.lastRead) {
      c.lastRead = down;
      c.lastChange = now;
    } else if (down != c.stable && now - c.lastChange >= DEBOUNCE_MS) {
      c.stable = down;
    }
    c.value = c.stable ? c.pressed : c.released;
  }
  else {
    c.value = c.temp;
  }
}

static double flexions[20];
static double sentFlex[20];

static double splays[5];
static double sentSplays[5];

static InputPacket inputPkt;
static InputPacket sentInput;

static void buildSkeletal(double trig, bool thumbDown, double gripV, double ringV, double pinkyV) {
  for (int i = 0; i < 20; i++) flexions[i] = 0.0;
  flexions[0]  = thumbDown ? 1.0 : 0.0;      // thumb
  flexions[4]  = trig;                       // index
  flexions[8]  = gripV;                      // middle
  flexions[12] = ringV;                      // ring
  flexions[16] = pinkyV;                     // pinky
}

static double finalGrip(double hardwareGrip) {
  return maxd(hardwareGrip, maxd(flexions[12], flexions[16]));
}

void buildPackets() {
  const double trig = clamp01(ch[C_TRIGGER].value);
  const bool trigCap = trig > CAP_AT;

  const double joyX = deadzone(ch[C_JOY_X].value);
  const double joyY = deadzone(ch[C_JOY_Y].value);
  const bool joyBtn = on(C_JOY_BTN);
  const bool joyCap = joyBtn || joyX != 0.0 || joyY != 0.0;

  const bool a = on(C_A), b = on(C_B), sys = on(C_SYSTEM);

  const double gripV = clamp01(ch[C_GRIP].value);
  const double ringV  = ch[C_RING].mode  == IN_NONE ? gripV : clamp01(ch[C_RING].value);
  const double pinkyV = ch[C_PINKY].mode == IN_NONE ? gripV : clamp01(ch[C_PINKY].value);
  const bool thumbDown = a || b || sys || joyBtn;
  buildSkeletal(trig, thumbDown, gripV, ringV, pinkyV);
  const double gripVal = finalGrip(gripV);

  for (int i = 0; i < FINGER_COUNT; i++) splays[i] = splay[i].value;
  splays[F_THUMB] = joyX;

  inputPkt.system = sys;
  inputPkt.a_x = a;  inputPkt.a_x_cap = a;
  inputPkt.b_y = b;  inputPkt.b_y_cap = b;
  inputPkt.trigger_cap = trigCap;
  inputPkt.joy_btn = joyBtn;  inputPkt.joy_cap = joyCap;
  inputPkt.trigger = trig;  inputPkt.grip = gripVal;
  inputPkt.joy_x = joyX;  inputPkt.joy_y = joyY;
}

void sendData() {
  static const char* FINGER_NAMES[5] = { "thumb", "index", "middle", "ring", "pinky" };
  char buf[320];
  int n = snprintf(buf, sizeof(buf), "skl");
  for (int i = 0; i < 5; i++) {
    if (n < 0 || n >= (int)sizeof(buf) - 48) break;
    n += snprintf(buf + n, sizeof(buf) - n, " %s=%.3f", FINGER_NAMES[i], flexions[i * 4]);
    n += snprintf(buf + n, sizeof(buf) - n, " %s_splay=%.3f", FINGER_NAMES[i], splays[i]);
  }
  buf[n++] = ' ';
  writeSerialAndBT(buf, (size_t)n);

  char ibuf[192];
  int m = snprintf(ibuf, sizeof(ibuf),
    "%s system=%d a=%d a_cap=%d b=%d b_cap=%d trigger_cap=%d joy_btn=%d joy_cap=%d trigger=%.3f grip=%.3f joy_x=%.3f joy_y=%.3f\n",
    INPUT_TAG,
    inputPkt.system, inputPkt.a_x, inputPkt.a_x_cap, inputPkt.b_y, inputPkt.b_y_cap,
    inputPkt.trigger_cap, inputPkt.joy_btn, inputPkt.joy_cap,
    inputPkt.trigger, inputPkt.grip, inputPkt.joy_x, inputPkt.joy_y);
  if (m > 0) {
    if (m >= (int)sizeof(ibuf)) m = sizeof(ibuf) - 1;
    writeSerialAndBT(ibuf, (size_t)m);
  }

  if (WiFi.status() == WL_CONNECTED) {
    udp.beginPacket(TARGET_IP, UDP_PORT);
    udp.write((const uint8_t*)INPUT_TAG, 3);
    udp.write((const uint8_t*)&inputPkt, sizeof(inputPkt));
    udp.endPacket();

    udp.beginPacket(TARGET_IP, UDP_PORT);
    udp.write((const uint8_t*)"skl", 3);
    udp.write((const uint8_t*)flexions, sizeof(flexions));
    udp.write((const uint8_t*)splays, sizeof(splays));
    udp.endPacket();
  }

  sentInput = inputPkt;
  memcpy(sentFlex, flexions, sizeof(flexions));
  memcpy(sentSplays, splays, sizeof(splays));
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  analogReadResolution(12);

  for (int i = 0; i < CH_COUNT; i++) initChannel(ch[i]);
  for (int i = 0; i < FINGER_COUNT; i++) initChannel(splay[i]);

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

  for (int i = 0; i < CH_COUNT; i++) updateChannel(ch[i], first);
  for (int i = 0; i < FINGER_COUNT; i++) updateChannel(splay[i], first);
  buildPackets();

  const bool changed = memcmp(&inputPkt, &sentInput, sizeof(inputPkt)) != 0 ||
                       memcmp(flexions, sentFlex, sizeof(flexions)) != 0 ||
                       memcmp(splays, sentSplays, sizeof(splays)) != 0;

  if (first || changed || now - lastSend >= HEARTBEAT_MS) {
    sendData();
    lastSend = now;
  }
  first = false;
}