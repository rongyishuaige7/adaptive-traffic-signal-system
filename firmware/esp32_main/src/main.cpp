/**
 * ESP32 main: 12 traffic LEDs + 4x 0.91" SSD1306 via TCA9548A (I2C SDA=4 SCL=5) + WebSocket client.
 * TCA9548A addr=0x70 (A0/A1/A2 to GND). OLED_N=CH0, OLED_S=CH1, OLED_E=CH2, OLED_W=CH3.
 * Set WIFI_SSID, WIFI_PASS, PC_HOST (IP of FastAPI PC), PC_PORT.
 */
#include <Arduino.h>
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <Wire.h>
#include <ArduinoJson.h>
#include <U8g2lib.h>

#ifndef WIFI_SSID
#define WIFI_SSID ""
#endif
#ifndef WIFI_PASS
#define WIFI_PASS ""
#endif
#ifndef PC_HOST
#define PC_HOST "127.0.0.1"
#endif
#ifndef PC_PORT
#define PC_PORT 8000
#endif

// GPIO map — see docs/wiring.md
#define PIN_N_R 13
#define PIN_N_Y 14
#define PIN_N_G 27  // was 15 (strapping pin, LED 下拉会影响启动)
#define PIN_S_R 16
#define PIN_S_Y 17
#define PIN_S_G 18
#define PIN_E_R 19
#define PIN_E_Y 21
#define PIN_E_G 22
#define PIN_W_R 23
#define PIN_W_Y 25
#define PIN_W_G 26

#define OLED_SDA 4
#define OLED_SCL 5

// TCA9548A I2C multiplexer — default address when A0/A1/A2 all GND
#define TCA9548A_ADDR 0x70
// Channel assignments: each OLED shares address 0x3C, distinguished by channel
#define TCA_CH_N 0
#define TCA_CH_S 1
#define TCA_CH_E 2
#define TCA_CH_W 3

// Four identical OLED instances — each activated via tcaSelect() before use
U8G2_SSD1306_128X32_UNIVISION_F_HW_I2C u8g2_N(U8G2_R0, U8X8_PIN_NONE);
U8G2_SSD1306_128X32_UNIVISION_F_HW_I2C u8g2_S(U8G2_R0, U8X8_PIN_NONE);
U8G2_SSD1306_128X32_UNIVISION_F_HW_I2C u8g2_E(U8G2_R0, U8X8_PIN_NONE);
U8G2_SSD1306_128X32_UNIVISION_F_HW_I2C u8g2_W(U8G2_R0, U8X8_PIN_NONE);

WebSocketsClient ws;

static String g_phase = "NS_GREEN";
static int g_remain = 0;
static int g_total = 0;
static int g_yellow = 3;
static int flowN = 0, flowS = 0, flowE = 0, flowW = 0;
static unsigned long lastHb = 0;
static bool wsConnected = false;

// Switch TCA9548A to the given channel (0-7). Pass 0xFF to disable all channels.
static void tcaSelect(uint8_t channel) {
  Wire.beginTransmission(TCA9548A_ADDR);
  Wire.write(channel > 7 ? 0x00 : (1 << channel));
  Wire.endTransmission();
}

static void allLedsOff() {
  const int pins[] = {PIN_N_R, PIN_N_Y, PIN_N_G, PIN_S_R, PIN_S_Y, PIN_S_G,
                      PIN_E_R, PIN_E_Y, PIN_E_G, PIN_W_R, PIN_W_Y, PIN_W_G};
  for (int p : pins)
    digitalWrite(p, LOW);
}

static void applyPhase(const String &ph) {
  allLedsOff();
  if (ph == "NS_GREEN") {
    digitalWrite(PIN_N_G, HIGH);
    digitalWrite(PIN_S_G, HIGH);
    digitalWrite(PIN_E_R, HIGH);
    digitalWrite(PIN_W_R, HIGH);
  } else if (ph == "NS_YELLOW") {
    digitalWrite(PIN_N_Y, HIGH);
    digitalWrite(PIN_S_Y, HIGH);
    digitalWrite(PIN_E_R, HIGH);
    digitalWrite(PIN_W_R, HIGH);
  } else if (ph == "EW_GREEN") {
    digitalWrite(PIN_E_G, HIGH);
    digitalWrite(PIN_W_G, HIGH);
    digitalWrite(PIN_N_R, HIGH);
    digitalWrite(PIN_S_R, HIGH);
  } else if (ph == "EW_YELLOW") {
    digitalWrite(PIN_E_Y, HIGH);
    digitalWrite(PIN_W_Y, HIGH);
    digitalWrite(PIN_N_R, HIGH);
    digitalWrite(PIN_S_R, HIGH);
  } else {
    // safe: all red
    digitalWrite(PIN_N_R, HIGH);
    digitalWrite(PIN_S_R, HIGH);
    digitalWrite(PIN_E_R, HIGH);
    digitalWrite(PIN_W_R, HIGH);
  }
}

// Draw one OLED: dir="N"/"S"/"E"/"W", myFlow=本方向流量, oppFlow=对向流量
static void drawOneOled(U8G2_SSD1306_128X32_UNIVISION_F_HW_I2C &disp,
                        uint8_t tcaCh, const char *dir, int myFlow,
                        int oppFlow) {
  tcaSelect(tcaCh);
  disp.clearBuffer();
  disp.setFont(u8g2_font_6x12_tf);

  // Line 1: direction + phase + countdown
  char line1[32];
  if (wsConnected) {
    snprintf(line1, sizeof(line1), "[%s] %s %ds", dir, g_phase.c_str(),
             g_remain);
  } else {
    snprintf(line1, sizeof(line1), "[%s] WS WAIT", dir);
  }
  disp.drawStr(0, 12, line1);

  // Line 2: this direction flow / opposite flow
  char line2[32];
  if (wsConnected) {
    snprintf(line2, sizeof(line2), "me:%d/min op:%d/min", myFlow, oppFlow);
  } else {
    snprintf(line2, sizeof(line2), "%s:%d", PC_HOST, PC_PORT);
  }
  disp.drawStr(0, 28, line2);

  disp.sendBuffer();
}

static void drawOled() {
  // North: opposite is South
  drawOneOled(u8g2_N, TCA_CH_N, "N", flowN, flowS);
  // South: opposite is North
  drawOneOled(u8g2_S, TCA_CH_S, "S", flowS, flowN);
  // East: opposite is West
  drawOneOled(u8g2_E, TCA_CH_E, "E", flowE, flowW);
  // West: opposite is East
  drawOneOled(u8g2_W, TCA_CH_W, "W", flowW, flowE);
}

void onWsEvent(WStype_t type, uint8_t *payload, size_t length) {
  if (type == WStype_TEXT) {
    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, payload, length);
    if (err)
      return;
    const char *t = doc["type"] | "";
    if (strcmp(t, "state") != 0)
      return;
    const char *ph = doc["phase"] | "NS_GREEN";
    g_phase = String(ph);
    g_remain = doc["remain_s"] | 0;
    g_total = doc["total_s"] | 0;
    g_yellow = doc["yellow_s"] | 3;
    if (doc["flow_per_min"].is<JsonObject>()) {
      JsonObject f = doc["flow_per_min"];
      flowN = f["N"] | 0;
      flowS = f["S"] | 0;
      flowE = f["E"] | 0;
      flowW = f["W"] | 0;
    }
    applyPhase(g_phase);
    drawOled();
  } else if (type == WStype_CONNECTED) {
    wsConnected = true;
    Serial.println("WS connected");
    drawOled();
  } else if (type == WStype_DISCONNECTED) {
    wsConnected = false;
    Serial.println("WS disconnected");
    allLedsOff();
    digitalWrite(PIN_N_R, HIGH);
    digitalWrite(PIN_S_R, HIGH);
    digitalWrite(PIN_E_R, HIGH);
    digitalWrite(PIN_W_R, HIGH);
    drawOled();
  } else if (type == WStype_ERROR) {
    wsConnected = false;
    Serial.println("WS error");
    drawOled();
  }
}

void setup() {
  Serial.begin(115200);
  const int pins[] = {PIN_N_R, PIN_N_Y, PIN_N_G, PIN_S_R, PIN_S_Y, PIN_S_G,
                      PIN_E_R, PIN_E_Y, PIN_E_G, PIN_W_R, PIN_W_Y, PIN_W_G};
  for (int p : pins) {
    pinMode(p, OUTPUT);
    digitalWrite(p, LOW);
  }
  allLedsOff();
  digitalWrite(PIN_N_R, HIGH);
  digitalWrite(PIN_S_R, HIGH);
  digitalWrite(PIN_E_R, HIGH);
  digitalWrite(PIN_W_R, HIGH);

  Wire.begin(OLED_SDA, OLED_SCL);

  // Init all four OLEDs through TCA9548A
  tcaSelect(TCA_CH_N); u8g2_N.begin();
  tcaSelect(TCA_CH_S); u8g2_S.begin();
  tcaSelect(TCA_CH_E); u8g2_E.begin();
  tcaSelect(TCA_CH_W); u8g2_W.begin();
  drawOled();

  WiFi.mode(WIFI_STA);
  if (strlen(WIFI_SSID) == 0 || strcmp(PC_HOST, "127.0.0.1") == 0) {
    Serial.println("WiFi/PC host not configured; provide untracked local build flags");
    while (true)
      delay(1000);
  }
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(WiFi.localIP());

  ws.onEvent(onWsEvent);
  Serial.print("WS target: ws://");
  Serial.print(PC_HOST);
  Serial.print(":");
  Serial.print(PC_PORT);
  Serial.println("/ws/device");
  ws.begin(PC_HOST, PC_PORT, "/ws/device");
  ws.setReconnectInterval(3000);
  ws.enableHeartbeat(15000, 3000, 2);
}

void loop() {
  ws.loop();
  unsigned long now = millis();
  if (now - lastHb > 10000) {
    lastHb = now;
    if (ws.isConnected()) {
      JsonDocument d;
      d["type"] = "heartbeat";
      d["device"] = "main";
      d["rssi"] = WiFi.RSSI();
      d["uptime"] = (uint32_t)(millis() / 1000);
      String out;
      serializeJson(d, out);
      ws.sendTXT(out);
    }
  }
}
