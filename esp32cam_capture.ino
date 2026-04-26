#include "esp_camera.h"
#include "Arduino.h"
#include "FS.h"                // SD Card ESP32
#include "SD_MMC.h"            // SD Card ESP32
#include "soc/soc.h"           // Disable brownout problems
#include "soc/rtc_cntl_reg.h"  // Disable brownout problems
#include "driver/rtc_io.h"

// Pin definition for CAMERA_MODEL_AI_THINKER
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// The pin you want to use as a trigger.
// GPIO 13, 14, 15 are generally available on the ESP32-CAM,
// but be mindful of strapping pin behaviors. GPIO 14 is safe.
#define TRIGGER_PIN 14

int pictureNumber = 0;

void setup() {
  // Disable brownout detector
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); 
 
  Serial.begin(115200);
  
  // Set the trigger pin as input with an internal pull-down resistor
  // so it stays LOW until explicitly connected to 3.3V (HIGH)
  pinMode(TRIGGER_PIN, INPUT_PULLDOWN);

  camera_config_t config;
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
  
  if(psramFound()){
    config.frame_size = FRAMESIZE_UXGA; // Large size
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_SVGA; // Smaller size
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }
  
  // Init Camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }
  
  // Init SD card
  // Start SD card in 1-bit mode (true) to avoid conflict with the flash LED (GPIO4)
  if(!SD_MMC.begin("/sdcard", true)){
    Serial.println("SD Card Mount Failed");
    return;
  }
  
  uint8_t cardType = SD_MMC.cardType();
  if(cardType == CARD_NONE){
    Serial.println("No SD Card attached");
    return;
  }
  
  Serial.println("Camera and SD Card Initialized. Waiting for trigger...");
}

void loop() {
  // Check if trigger pin is pulled HIGH
  if (digitalRead(TRIGGER_PIN) == HIGH) {
    Serial.println("Trigger detected! Taking picture...");
    
    // Take Picture with Camera
    camera_fb_t * fb = NULL;
    fb = esp_camera_fb_get();  
    if(!fb) {
      Serial.println("Camera capture failed");
      return;
    }
    
    // Path where new picture will be saved in SD Card
    String path = "/picture" + String(pictureNumber) + ".jpg";
    
    fs::FS &fs = SD_MMC; 
    
    File file = fs.open(path.c_str(), FILE_WRITE);
    if(!file){
      Serial.println("Failed to open file in writing mode");
    } 
    else {
      file.write(fb->buf, fb->len); // payload (image), payload length
      Serial.printf("Saved picture: %s\n", path.c_str());
    }
    file.close();
    
    // Send image over UART
    Serial.println();
    Serial.print("<<IMAGE_START:");
    Serial.print(fb->len);
    Serial.println(">>");
    
    // Write raw image bytes to Serial
    Serial.write(fb->buf, fb->len);
    
    Serial.println();
    Serial.println("<<IMAGE_END>>");
    
    // Return the frame buffer back to the driver for reuse
    esp_camera_fb_return(fb); 
    
    pictureNumber++;
    
    // Wait to prevent taking multiple pictures at once
    delay(500); 
    
    // Wait until the pin is released (goes back LOW) before arming for the next picture
    while (digitalRead(TRIGGER_PIN) == HIGH) {
      delay(50);
    }
    Serial.println("Ready for next trigger.");
  }
}
