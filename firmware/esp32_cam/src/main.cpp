/**
 * ESP32-CAM (AI Thinker): WiFi + MJPEG /stream + mDNS.
 * Per device: set WIFI_SSID, WIFI_PASS, CAM_DIRECTION (N/S/E/W).
 */
#include <Arduino.h>
#include <WiFi.h>
#include "esp_camera.h"
#include "esp_http_server.h"
#include "img_converters.h"
#include "esp_heap_caps.h"
#include <ESPmDNS.h>

#ifndef CAM_DIRECTION
#define CAM_DIRECTION "N"
#endif
#ifndef WIFI_SSID
#define WIFI_SSID ""
#endif
#ifndef WIFI_PASS
#define WIFI_PASS ""
#endif
#ifdef STATIC_IP
#ifndef STATIC_GW
#error "STATIC_GW is required when STATIC_IP is set"
#endif
#ifndef STATIC_SUBNET
#error "STATIC_SUBNET is required when STATIC_IP is set"
#endif
#ifndef STATIC_DNS
#define STATIC_DNS STATIC_GW
#endif
#endif
#ifndef CAMERA_FRAME_SIZE
#define CAMERA_FRAME_SIZE FRAMESIZE_QVGA
#endif
#ifndef CAMERA_JPEG_QUALITY
#define CAMERA_JPEG_QUALITY 14
#endif
#ifndef STREAM_FRAME_DELAY_MS
#define STREAM_FRAME_DELAY_MS 150
#endif

#define PART_BOUNDARY "123456789000000000000987654321"
static const char *_STREAM_CONTENT_TYPE =
    "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char *_STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char *_STREAM_PART =
    "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

#if defined(CAMERA_MODEL_AI_THINKER)
#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27
#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22
#endif

static httpd_handle_t stream_httpd = NULL;

static bool parse_ip(IPAddress &ip, const char *value, const char *name) {
  if (ip.fromString(value))
    return true;
  Serial.printf("Invalid %s: %s\n", name, value);
  return false;
}

static void configure_wifi_ip() {
  Serial.print("MAC: ");
  Serial.println(WiFi.macAddress());

#ifdef STATIC_IP
  IPAddress local_ip;
  IPAddress gateway;
  IPAddress subnet;
  IPAddress dns;
  if (!parse_ip(local_ip, STATIC_IP, "STATIC_IP") ||
      !parse_ip(gateway, STATIC_GW, "STATIC_GW") ||
      !parse_ip(subnet, STATIC_SUBNET, "STATIC_SUBNET") ||
      !parse_ip(dns, STATIC_DNS, "STATIC_DNS")) {
    Serial.println("Static IP disabled because config is invalid");
    return;
  }

  if (WiFi.config(local_ip, gateway, subnet, dns)) {
    Serial.print("Static IP configured: ");
    Serial.println(local_ip);
  } else {
    Serial.println("Static IP config failed, fallback to DHCP");
  }
#else
  Serial.println("IP config: DHCP");
#endif
}

static bool test_camera_capture(const char *tag) {
  for (int i = 0; i < 5; i++) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (fb) {
      Serial.printf("%s: capture OK, %ux%u, len=%u\n", tag,
                    (unsigned)fb->width, (unsigned)fb->height,
                    (unsigned)fb->len);
      esp_camera_fb_return(fb);
      return true;
    }
    Serial.printf("%s: capture failed, retry %d\n", tag, i + 1);
    delay(300);
  }
  return false;
}

static esp_err_t index_handler(httpd_req_t *req) {
  static const char html[] =
      "<!doctype html><html><head><meta name=\"viewport\" "
      "content=\"width=device-width,initial-scale=1\">"
      "<title>ESP32-CAM</title></head><body>"
      "<h3>ESP32-CAM</h3>"
      "<p><a href=\"/jpg\">Single JPG</a></p>"
      "<p><a href=\"/stream\">MJPEG stream</a></p>"
      "</body></html>";
  httpd_resp_set_type(req, "text/html");
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  return httpd_resp_send(req, html, HTTPD_RESP_USE_STRLEN);
}

static esp_err_t jpg_handler(httpd_req_t *req) {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("JPG: camera_fb_get failed");
    httpd_resp_send_500(req);
    return ESP_FAIL;
  }

  esp_err_t res = ESP_OK;
  if (fb->format == PIXFORMAT_JPEG) {
    httpd_resp_set_type(req, "image/jpeg");
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    res = httpd_resp_send(req, (const char *)fb->buf, fb->len);
  } else {
    uint8_t *jpg_buf = NULL;
    size_t jpg_len = 0;
    bool ok = frame2jpg(fb, 15, &jpg_buf, &jpg_len);
    if (ok) {
      httpd_resp_set_type(req, "image/jpeg");
      httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
      res = httpd_resp_send(req, (const char *)jpg_buf, jpg_len);
      free(jpg_buf);
    } else {
      Serial.println("JPG: frame2jpg failed");
      httpd_resp_send_500(req);
      res = ESP_FAIL;
    }
  }

  esp_camera_fb_return(fb);
  return res;
}

static esp_err_t stream_handler(httpd_req_t *req) {
  camera_fb_t *fb = NULL;
  esp_err_t res = ESP_OK;
  char part_buf[64];
  uint32_t frame_count = 0;

  Serial.println("STREAM: client connected");

  res = httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
  if (res != ESP_OK)
    return res;
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");

  while (true) {
    size_t jpg_len = 0;
    uint8_t *jpg_buf = NULL;
    fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("STREAM: camera_fb_get failed");
      res = ESP_FAIL;
      break;
    }
    if (fb->format != PIXFORMAT_JPEG) {
      bool ok = frame2jpg(fb, 12, &jpg_buf, &jpg_len);
      esp_camera_fb_return(fb);
      fb = NULL;
      if (!ok) {
        res = ESP_FAIL;
        break;
      }
    } else {
      jpg_len = fb->len;
      jpg_buf = fb->buf;
    }

    if (res == ESP_OK)
      res = httpd_resp_send_chunk(req, _STREAM_BOUNDARY,
                                    strlen(_STREAM_BOUNDARY));
    if (res == ESP_OK) {
      size_t hlen =
          snprintf(part_buf, sizeof(part_buf), _STREAM_PART, (unsigned)jpg_len);
      res = httpd_resp_send_chunk(req, part_buf, hlen);
    }
    if (res == ESP_OK)
      res = httpd_resp_send_chunk(req, (const char *)jpg_buf, jpg_len);

    if (fb) {
      esp_camera_fb_return(fb);
      fb = NULL;
    } else if (jpg_buf) {
      free(jpg_buf);
      jpg_buf = NULL;
    }
    frame_count++;
    if (frame_count == 1 || frame_count % 100 == 0) {
      Serial.printf("STREAM: sent %u frames\n", (unsigned)frame_count);
    }
    if (res != ESP_OK)
      break;
    delay(STREAM_FRAME_DELAY_MS);
  }
  Serial.printf("STREAM: client disconnected, res=0x%x, frames=%u\n",
                (unsigned)res, (unsigned)frame_count);
  return res;
}

static esp_err_t start_stream_server() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 80;
  config.ctrl_port = 32768;
  config.stack_size = 8192;

  if (httpd_start(&stream_httpd, &config) != ESP_OK)
    return ESP_FAIL;

  httpd_uri_t index_uri = {.uri = "/",
                           .method = HTTP_GET,
                           .handler = index_handler,
                           .user_ctx = NULL};
  if (httpd_register_uri_handler(stream_httpd, &index_uri) != ESP_OK)
    return ESP_FAIL;

  httpd_uri_t stream_uri = {.uri = "/stream",
                            .method = HTTP_GET,
                            .handler = stream_handler,
                            .user_ctx = NULL};
  if (httpd_register_uri_handler(stream_httpd, &stream_uri) != ESP_OK)
    return ESP_FAIL;

  httpd_uri_t jpg_uri = {.uri = "/jpg",
                         .method = HTTP_GET,
                         .handler = jpg_handler,
                         .user_ctx = NULL};
  if (httpd_register_uri_handler(stream_httpd, &jpg_uri) != ESP_OK)
    return ESP_FAIL;
  return ESP_OK;
}

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(false);
  setCpuFrequencyMhz(160);
  delay(200);

  camera_config_t config = {};
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = CAMERA_FRAME_SIZE;
  config.jpeg_quality = CAMERA_JPEG_QUALITY;
  config.fb_count = 1;
  config.fb_location = psramFound() ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.sccb_i2c_port = 0;

  Serial.printf("Free heap: %u, free PSRAM: %u\n",
                (unsigned)ESP.getFreeHeap(),
                (unsigned)heap_caps_get_free_size(MALLOC_CAP_SPIRAM));
  Serial.println("Camera init...");
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed 0x%x\n", err);
    while (true)
      delay(1000);
  }
  Serial.println("Camera OK");
  if (!test_camera_capture("Camera self-test")) {
    Serial.println("Camera self-test failed");
    while (true)
      delay(1000);
  }
  delay(1000);

  Serial.println("WiFi mode...");
  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  configure_wifi_ip();
  WiFi.setSleep(false);
  WiFi.setTxPower(WIFI_POWER_2dBm);
  delay(500);
  if (strlen(WIFI_SSID) == 0) {
    Serial.println("WiFi credentials not configured; copy local-config.example.ini to local-config.ini");
    while (true)
      delay(1000);
  }
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("WiFi");
  unsigned long wifiStart = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - wifiStart < 30000) {
    delay(500);
    Serial.print(".");
  }
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println();
    Serial.println("WiFi connect timeout");
    while (true)
      delay(1000);
  }
  Serial.println();
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  char host[32];
  snprintf(host, sizeof(host), "traffic-cam-%s", CAM_DIRECTION);
  if (MDNS.begin(host)) {
    Serial.printf("mDNS: %s.local\n", host);
    MDNS.addService("http", "tcp", 80);
  }

  Serial.println("HTTP start...");
  if (start_stream_server() != ESP_OK) {
    Serial.println("HTTP start failed");
    while (true)
      delay(1000);
  }
  Serial.print("Open: http://");
  Serial.println(WiFi.localIP());
  Serial.print("MJPEG: http://");
  Serial.print(WiFi.localIP());
  Serial.println("/stream");
  Serial.print("JPG: http://");
  Serial.print(WiFi.localIP());
  Serial.println("/jpg");
}

void loop() { delay(1000); }
