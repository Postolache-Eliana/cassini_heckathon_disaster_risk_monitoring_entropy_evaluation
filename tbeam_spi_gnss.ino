#include <Arduino.h>
#include <Wire.h>
#include <axp20x.h>        // Library for AXP192 PMIC
#include <TinyGPS++.h>     // Library for parsing NMEA from NEO-6M
#include "driver/spi_slave.h"

// T-Beam v1.1 Pins
#define I2C_SDA 21
#define I2C_SCL 22
#define GPS_RX_PIN 34
#define GPS_TX_PIN 12

// Hardware Trigger Pin (Connect to Pi Zero GPIO 17)
#define TRIGGER_PIN 14

// SPI Slave Pins (VSPI)
#define SPI_SCK 18
#define SPI_MISO 19
#define SPI_MOSI 23
#define SPI_CS 5

AXP20X_Class axp;
TinyGPSPlus gps;

// Struct to hold the GPS data we will send over SPI
struct __attribute__((packed, aligned(4))) GpsData {
  float latitude;
  float longitude;
  float altitude;
  uint8_t isValid;
  uint8_t padding[3];
};

GpsData latestGpsData = {0.0, 0.0, 0.0, 0, {0,0,0}};

// SPI Slave configuration
WORD_ALIGNED_ATTR uint8_t spi_tx_buf[sizeof(GpsData)];
WORD_ALIGNED_ATTR uint8_t spi_rx_buf[sizeof(GpsData)];

spi_slave_transaction_t t;
volatile bool triggerFired = false;

// Interrupt Service Routine for the Trigger Pin
void IRAM_ATTR triggerISR() {
  triggerFired = true;
}

void setup_spi_slave() {
  spi_bus_config_t buscfg = {};
  buscfg.mosi_io_num = SPI_MOSI;
  buscfg.miso_io_num = SPI_MISO;
  buscfg.sclk_io_num = SPI_SCK;
  buscfg.quadwp_io_num = -1;
  buscfg.quadhd_io_num = -1;

  spi_slave_interface_config_t slvcfg = {};
  slvcfg.mode = 0;
  slvcfg.spics_io_num = SPI_CS;
  slvcfg.queue_size = 1;
  slvcfg.flags = 0;

  // Initialize SPI slave interface
  esp_err_t ret = spi_slave_initialize(VSPI_HOST, &buscfg, &slvcfg, SPI_DMA_CH_AUTO);
  if(ret != ESP_OK) {
    Serial.printf("SPI Slave Init Failed! Error: %d\n", ret);
  } else {
    Serial.println("SPI Slave Initialized.");
  }
}

void setup() {
  Serial.begin(115200);
  Wire.begin(I2C_SDA, I2C_SCL);
  
  // Initialize AXP192 to power the GPS
  if (axp.begin(Wire, AXP192_SLAVE_ADDRESS) == AXP_PASS) {
    Serial.println("AXP192 Init Success");
    axp.setPowerOutPut(AXP192_LDO3, AXP202_ON); // Power GPS
    axp.setPowerOutPut(AXP192_EXTEN, AXP202_ON);
  } else {
    Serial.println("AXP192 Init Failed");
  }

  // Initialize GPS Serial
  Serial1.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
  
  // Set up Trigger Pin Interrupt
  pinMode(TRIGGER_PIN, INPUT_PULLDOWN);
  attachInterrupt(digitalPinToInterrupt(TRIGGER_PIN), triggerISR, RISING);

  // Initialize SPI Slave
  setup_spi_slave();
  
  // Prepare and queue the first SPI transaction
  memset(&t, 0, sizeof(t));
  t.length = sizeof(GpsData) * 8;
  t.tx_buffer = spi_tx_buf;
  t.rx_buffer = spi_rx_buf;
  spi_slave_queue_trans(VSPI_HOST, &t, portMAX_DELAY);
  
  Serial.println("T-Beam Ready. Waiting for hardware trigger from Pi...");
}

void loop() {
  // Continuously parse GPS data in the background
  while (Serial1.available() > 0) {
    if (gps.encode(Serial1.read())) {
      if (gps.location.isValid()) {
        latestGpsData.latitude = gps.location.lat();
        latestGpsData.longitude = gps.location.lng();
        latestGpsData.altitude = gps.altitude.isValid() ? gps.altitude.meters() : 0.0;
        latestGpsData.isValid = 1;
      } else {
        latestGpsData.isValid = 0;
      }
    }
  }

  // When the Pi pulls the trigger HIGH, snap the current GPS state into the SPI buffer
  if (triggerFired) {
    triggerFired = false;
    Serial.println("Hardware Trigger Detected! Snapping GPS data to SPI buffer.");
    
    // Copy the exact location at the moment of trigger into the SPI DMA buffer.
    // The Pi will read this buffer a few milliseconds later over SPI.
    memcpy(spi_tx_buf, &latestGpsData, sizeof(GpsData));
  }

  // Check if an SPI transaction was completed by the Pi reading it
  spi_slave_transaction_t* out_trans;
  esp_err_t ret = spi_slave_get_trans_result(VSPI_HOST, &out_trans, 0); 
  if (ret == ESP_OK) {
    Serial.println("SPI Buffer read by Pi. Resetting for next trigger.");
    // Queue the transaction again so it's ready for the next cycle
    spi_slave_queue_trans(VSPI_HOST, &t, portMAX_DELAY);
  }
}
