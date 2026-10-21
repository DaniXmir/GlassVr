//send position and rotation only

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
#define CHANGE_EPSILON    0.0001f
#define WIFI_RETRY_MS     5000

#define TARGET_IP         "255.255.255.255" //255.255.255.255 is a special broadcast ip, if it doesnt work then get you pc ip by typing "ipconfig" in cmd
#define UDP_PORT          9002 //hmd=9000 right=9001 left=9002 0tracker=9003...

WiFiUDP udp;
static bool udpStarted = false;

double posX = 0.0;
double posY = 0.0;
double posZ = 0.0;

double rotW = 1.0;
double rotX = 0.0;
double rotY = 0.0;
double rotZ = 0.0;

#if USE_BLUETOOTH
#include "BluetoothSerial.h"
BluetoothSerial SerialBT;
#endif

static double sPosX, sPosY, sPosZ, sRotW, sRotX, sRotY, sRotZ;

void writeSerialAndBT(const char* data, size_t len) {
  Serial.write((const uint8_t*)data, len);
#if USE_BLUETOOTH
  SerialBT.write((const uint8_t*)data, len);
#endif
}

void normalizeRotation() {
  double len = sqrt(rotW * rotW + rotX * rotX + rotY * rotY + rotZ * rotZ);
  if (len < 1e-9) {
    rotW = 1.0; rotX = rotY = rotZ = 0.0;
    return;
  }
  rotW /= len; rotX /= len; rotY /= len; rotZ /= len;
}

void sendData() {
  normalizeRotation();

  char buf[128];
  int n = snprintf(buf, sizeof(buf), "pos x=%.5f y=%.5f z=%.5f\n", posX, posY, posZ);
  if (n > 0) writeSerialAndBT(buf, (size_t)n);
  n = snprintf(buf, sizeof(buf), "rot w=%.5f x=%.5f y=%.5f z=%.5f\n", rotW, rotX, rotY, rotZ);
  if (n > 0) writeSerialAndBT(buf, (size_t)n);

  if (WiFi.status() == WL_CONNECTED) {
    const double pos[3] = { posX, posY, posZ };
    udp.beginPacket(TARGET_IP, UDP_PORT);
    udp.write((const uint8_t*)"pos", 3);
    udp.write((const uint8_t*)pos, sizeof(pos));
    udp.endPacket();

    const double rot[4] = { rotW, rotX, rotY, rotZ };
    udp.beginPacket(TARGET_IP, UDP_PORT);
    udp.write((const uint8_t*)"rot", 3);
    udp.write((const uint8_t*)rot, sizeof(rot));
    udp.endPacket();
  }

  sPosX = posX; sPosY = posY; sPosZ = posZ;
  sRotW = rotW; sRotX = rotX; sRotY = rotY; sRotZ = rotZ;
}

static bool differs(double a, double b) {
  double d = a - b;
  if (d < 0) d = -d;
  return d >= CHANGE_EPSILON;
}

void setup() {
  Serial.begin(SERIAL_BAUD);

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

  const bool changed =
    differs(posX, sPosX) || differs(posY, sPosY) || differs(posZ, sPosZ) ||
    differs(rotW, sRotW) || differs(rotX, sRotX) || differs(rotY, sRotY) || differs(rotZ, sRotZ);

  if (first || changed || now - lastSend >= HEARTBEAT_MS) {
    sendData();
    lastSend = now;
  }
  first = false;
}