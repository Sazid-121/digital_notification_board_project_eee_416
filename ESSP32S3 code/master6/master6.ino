#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <time.h>
#include <esp_wifi.h>

// ==== SPI Pin Assignments ====
#define PIN_MOSI   9
#define PIN_SCLK   10
#define PIN_CS     11
#define PIN_READY  12
#define PIN_ACK    13

// ==== Constants ====
#define CHUNK_SIZE     1024
#define TOTAL_CHUNKS   600
#define TOTAL_SIZE     (CHUNK_SIZE * TOTAL_CHUNKS)
#define WIFI_TIMEOUT   30000   // 30 seconds
#define CYCLE_DELAY    30000   // 30 seconds
#define DOWNLOAD_RETRY_DELAY 5000
#define MAX_DOWNLOAD_ATTEMPTS 3

const char* ssid = "Itel A70";
const char* password = "sourovbme";
// const char* ssid = "Horseman";
// const char* password = "bme.eee.buet.ac.bd";

// ==== GitHub Raw URLs ====
const char* versionURL = "https://raw.githubusercontent.com/Sazid-121/esp32-vga-notification-board/main/version.txt";
const char* binURL = "https://raw.githubusercontent.com/Sazid-121/esp32-vga-notification-board/main/display_image_rgb565.bin";

// ==== Globals ====
uint8_t* binData = nullptr;
int previous_version = -1;

// ==== Functions ====

void initSPIPins() {
  pinMode(PIN_READY, OUTPUT);
  pinMode(PIN_ACK, INPUT_PULLDOWN);
  pinMode(PIN_CS, OUTPUT);
  digitalWrite(PIN_READY, LOW);
  digitalWrite(PIN_CS, HIGH);
  SPI.begin(PIN_SCLK, -1, PIN_MOSI, PIN_CS);
  Serial.println("✅ SPI initialized");
}

void connectToWiFi() {
  WiFi.mode(WIFI_STA);
  esp_wifi_set_max_tx_power(80);

  WiFi.begin(ssid, password);
  Serial.print("📶 Connecting to Wi-Fi");

  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }

  Serial.println("\n✅ Connected to Wi-Fi.");
}

bool isWiFiConnected() {
  return WiFi.status() == WL_CONNECTED;
}

bool fetchVersion(int &version, String &renderTime) {
  Serial.println("⬇️ Downloading version.txt...");

  for (int attempt = 1; attempt <= MAX_DOWNLOAD_ATTEMPTS; attempt++) {
    if (!isWiFiConnected()) {
      Serial.println("🔁 Wi-Fi disconnected. Reconnecting...");
      connectToWiFi();
    }

    HTTPClient http;
    http.begin(versionURL);
    int httpCode = http.GET();

    if (httpCode == HTTP_CODE_OK) {
      String payload = http.getString();
      http.end();

      Serial.println("📄 version.txt content:");
      Serial.println(payload);

      payload.trim();
      int lineBreak = payload.indexOf('\n');
      if (lineBreak == -1) {
        Serial.println("❌ Malformed version.txt");
        return false;
      }

      version = payload.substring(0, lineBreak).toInt();
      renderTime = payload.substring(lineBreak + 1);
      renderTime.trim();

      Serial.printf("📄 version: %d | render_time: %s\n", version, renderTime.c_str());
      return true;
    }

    http.end();
    Serial.printf("❌ Attempt %d: Failed to download version.txt (code %d)\n", attempt, httpCode);
    if (attempt < MAX_DOWNLOAD_ATTEMPTS) delay(DOWNLOAD_RETRY_DELAY);
  }

  Serial.println("❌ Failed to fetch version.txt after retries. Skipping cycle.");
  return false;
}

bool downloadBinFile() {
  Serial.println("⬇️ Downloading .bin file...");

  for (int attempt = 1; attempt <= MAX_DOWNLOAD_ATTEMPTS; attempt++) {
    if (!isWiFiConnected()) {
      Serial.println("🔁 Wi-Fi disconnected. Reconnecting...");
      connectToWiFi();
    }

    HTTPClient http;
    http.begin(binURL);
    int httpCode = http.GET();

    if (httpCode == HTTP_CODE_OK) {
      int size = http.getSize();
      Serial.printf("📦 .bin file size: %d bytes\n", size);

      if (size != TOTAL_SIZE) {
        Serial.printf("⚠️ Expected %d bytes, got %d\n", TOTAL_SIZE, size);
      }

      binData = (uint8_t*)ps_malloc(TOTAL_SIZE);
      if (!binData) {
        Serial.println("❌ PSRAM allocation failed.");
        http.end();
        return false;
      }

      WiFiClient *stream = http.getStreamPtr();
      int index = 0;
      while (http.connected() && index < size) {
        if (stream->available()) {
          binData[index++] = stream->read();
        }
      }

      http.end();
      Serial.println("✅ .bin file download complete.");
      return true;
    }

    http.end();
    Serial.printf("❌ Attempt %d: Failed to download .bin file (code %d)\n", attempt, httpCode);
    if (attempt < MAX_DOWNLOAD_ATTEMPTS) delay(DOWNLOAD_RETRY_DELAY);
  }

  Serial.println("❌ Failed to fetch .bin file after retries. Skipping cycle.");
  return false;
}

void waitUntilRenderTime(const String& renderTimeStr) {
  if (renderTimeStr == "now") {
    Serial.println("🕒 Render time is NOW. Proceeding immediately.");
    return;
  }

  struct tm timeinfo;
  if (!strptime(renderTimeStr.c_str(), "%Y-%m-%dT%H:%M:%S", &timeinfo)) {
    Serial.println("❌ Failed to parse render time. Rendering now.");
    return;
  }

  time_t targetTime = mktime(&timeinfo);
  time_t now;
  time(&now);

  while (now < targetTime) {
    int remaining = targetTime - now;
    Serial.printf("⏳ Waiting %d seconds until render time...\n", remaining);
    delay(min(10000, remaining * 1000));
    time(&now);
  }

  Serial.println("✅ Render time reached. Proceeding...");
}

void sendRawFramebuffer() {
  Serial.println("🛄 Sending framebuffer to slave...");

  for (uint16_t chunk = 0; chunk < TOTAL_CHUNKS; chunk++) {
    digitalWrite(PIN_READY, HIGH);
    while (digitalRead(PIN_ACK) == LOW) delay(1);

    while (digitalRead(PIN_CS) == LOW) delay(1);  // wait for CS to be HIGH
    digitalWrite(PIN_CS, LOW);

    SPI.beginTransaction(SPISettings(100000, MSBFIRST, SPI_MODE0));
    for (int i = 0; i < CHUNK_SIZE; i++) {
      SPI.transfer(binData[chunk * CHUNK_SIZE + i]);
    }
    SPI.endTransaction();
    digitalWrite(PIN_CS, HIGH);

    while (digitalRead(PIN_ACK) == HIGH) delay(1);
    digitalWrite(PIN_READY, LOW);
    delay(2);
  }

  Serial.println("✅ Framebuffer sent.");
  free(binData);
  binData = nullptr;
}

// ==== SETUP ====
void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("👐 Booting ESP32-S3 MASTER...");

  initSPIPins();
  connectToWiFi();
  configTime(21600, 0, "pool.ntp.org");  // UTC+6
}

// ==== LOOP ====
void loop() {
  if (!isWiFiConnected()) {
    Serial.println("🔄 Wi-Fi disconnected. Reconnecting...");
    connectToWiFi();
  }

  Serial.println("🔄 Checking version.txt...");

  int currentVersion;
  String renderTime;

  if (fetchVersion(currentVersion, renderTime)) {
    if (currentVersion != previous_version) {
      Serial.println("🎲 New version detected. Downloading .bin...");

      if (downloadBinFile()) {
        waitUntilRenderTime(renderTime);
        sendRawFramebuffer();
        previous_version = currentVersion;
      }
    } else {
      Serial.println("⏸️ No update. Version unchanged.");
    }
  }

  Serial.println("⏳ Sleeping 30 seconds...\n");
  delay(CYCLE_DELAY);
}
