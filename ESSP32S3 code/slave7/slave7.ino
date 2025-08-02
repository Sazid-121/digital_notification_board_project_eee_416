#include <Arduino.h>
#include <driver/spi_slave.h>
#include <esp_heap_caps.h>
#include "luniVGA.h"  // Bitluni VGA library

// ==== Pin Definitions ====
#define PIN_MOSI   42
#define PIN_SCLK   41
#define PIN_CS     40
#define PIN_READY  39  // Master → Slave
#define PIN_ACK    38  // Slave → Master

#define SPI_SLAVE_HOST SPI3_HOST
#define CHUNK_SIZE     1024
#define TOTAL_CHUNKS   600
#define FRAMEBUFFER_SIZE (CHUNK_SIZE * TOTAL_CHUNKS)
#define TIMEOUT_MS     3000

// VGA Pin config (Do NOT overlap with SPI)
const PinConfig pins(
  14, 13, 12, 11, 10,              // Red
  9, 8, 18, 17, 16, 15,      // Green
  21, 7, 6, 5, 4,         // Blue
  2, 1                        // HSYNC, VSYNC
);

uint8_t* framebuffer_psram = nullptr;
uint8_t* rx_buffer = nullptr;

void drawImageFromBuffer(uint8_t* buffer) {
  const int IMAGE_WIDTH = 640;
  const int IMAGE_HEIGHT = 480;

  for (int y = 0; y < IMAGE_HEIGHT; y++) {
    for (int x = 0; x < IMAGE_WIDTH; x++) {
      int i = y * IMAGE_WIDTH + x;
      uint16_t rgb565 = ((uint16_t*)buffer)[i];

      uint8_t r = ((rgb565 >> 11) & 0x1F) << 3;
      uint8_t g = ((rgb565 >> 5) & 0x3F) << 2;
      uint8_t b = (rgb565 & 0x1F) << 3;

      vgaDot(x, y, r, g, b);
    }
  }

  vgaShow();
  vgaStart();
 
}


void blankTask() {
  const int WIDTH = 640, HEIGHT = 480;

  for (int y = 0; y < HEIGHT; y++) {
    for (int x = 0; x < WIDTH; x++) {
      vgaDot(x, y, 0, 0, 0);
    }
  }

  vgaShow();
  vgaStart();
}


void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("🟢 Slave: Receiving 600 chunks without chunkID");

  pinMode(PIN_READY, INPUT_PULLDOWN);
  pinMode(PIN_ACK, OUTPUT);
  digitalWrite(PIN_ACK, LOW);

  // VGA init
  VGAMode mode = MODE_640x480x60;
  if (!vgaInit(pins, mode, 16)) {
    Serial.println("❌ VGA init failed");
    while (true);
  }
   vgaStart();
  framebuffer_psram = (uint8_t*)heap_caps_malloc(FRAMEBUFFER_SIZE, MALLOC_CAP_SPIRAM);
  rx_buffer = (uint8_t*)heap_caps_malloc(CHUNK_SIZE, MALLOC_CAP_DMA);

  if (!framebuffer_psram || !rx_buffer) {
    Serial.println("❌ Memory allocation failed");
    while (true);
  }

  memset(framebuffer_psram, 0, FRAMEBUFFER_SIZE);

  spi_bus_config_t buscfg = {
    .mosi_io_num = PIN_MOSI,
    .miso_io_num = -1,
    .sclk_io_num = PIN_SCLK,
    .quadwp_io_num = -1,
    .quadhd_io_num = -1,
    .max_transfer_sz = CHUNK_SIZE
  };

  spi_slave_interface_config_t slvcfg = {
    .spics_io_num = PIN_CS,
    .flags = 0,
    .queue_size = 1,
    .mode = 0,
    .post_setup_cb = NULL,
    .post_trans_cb = NULL
  };

  if (spi_slave_initialize(SPI_SLAVE_HOST, &buscfg, &slvcfg, SPI_DMA_CH_AUTO) != ESP_OK) {
    Serial.println("❌ SPI init failed");
    while (true);
  }

  Serial.println("✅ SPI initialized. Waiting for chunks...");
}

void loop() {
  static uint16_t receivedChunks = 0;
  static bool done = false;

  //if (done) return;

  if (digitalRead(PIN_READY) == LOW)
  { 
    return;
  }

  if (done) {
      if (digitalRead(PIN_READY) == HIGH) {
        ESP.restart();
  }
  }

  digitalWrite(PIN_ACK, HIGH);

  spi_slave_transaction_t t;
  memset(&t, 0, sizeof(t));
  t.length = CHUNK_SIZE * 8;
  t.rx_buffer = rx_buffer;

  esp_err_t ret = spi_slave_transmit(SPI_SLAVE_HOST, &t, pdMS_TO_TICKS(TIMEOUT_MS));

  digitalWrite(PIN_ACK, LOW);
  while (digitalRead(PIN_READY) == HIGH) delay(1);

  if (ret == ESP_OK) {
    // Store chunk by arrival order
    memcpy(&framebuffer_psram[receivedChunks * CHUNK_SIZE], rx_buffer, CHUNK_SIZE);
    Serial.printf("✅ Chunk %u received\n", receivedChunks);
    Serial.print("🔍 Received (first 8 bytes): ");
      for (int i = 0; i < 8; i++) {
      Serial.printf("%02X ", rx_buffer[i]);
      }
Serial.println();

    Serial.println();
    receivedChunks++;

    if (receivedChunks == TOTAL_CHUNKS) {
      Serial.println("🎉 All chunks received.");

      drawImageFromBuffer(framebuffer_psram);

      Serial.println("#### VGA DRAWN ####");
      //delay(10000);
      done = true;
    }
  } else {
    Serial.printf("⚠️ SPI error: %s\n", esp_err_to_name(ret));
  }
}
