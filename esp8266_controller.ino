#include <Arduino.h>
#include <SoftwareSerial.h>

// ESP8266 D0 is GPIO 16
#define TRIGGER_PIN 16 

// Using SoftwareSerial to talk to the ESP32-CAM.
// This leaves the main hardware Serial free for debugging to your PC via USB.
// Wiring:
// Connect ESP8266 D1 (GPIO 5) to ESP32-CAM U0TXD
// Connect ESP8266 D2 (GPIO 4) to ESP32-CAM U0RXD
// Connect GND of ESP8266 to GND of ESP32-CAM
SoftwareSerial camSerial(5, 4); 

void setup() {
  // Start the hardware serial for debugging output to the computer
  Serial.begin(115200);      
  
  // Start the software serial for communicating with the ESP32-CAM
  // Note: If you experience corrupted images, try lowering the baud rate 
  // on BOTH the ESP32-CAM and here (e.g., to 38400 or 57600) as SoftwareSerial 
  // can sometimes drop bytes at 115200 baud on large transfers.
  camSerial.begin(115200);   
  
  // Initialize the trigger pin
  pinMode(TRIGGER_PIN, OUTPUT);
  digitalWrite(TRIGGER_PIN, LOW); // Keep low by default
  
  Serial.println("\n--- ESP8266 Camera Controller Ready ---");
  Serial.println("Waiting 5 seconds before the first trigger...");
  delay(5000);
}

void loop() {
  Serial.println("\nTriggering ESP32-CAM...");
  
  // Pull D0 HIGH to trigger the ESP32-CAM
  digitalWrite(TRIGGER_PIN, HIGH);
  delay(200); // Hold high for 200ms to ensure the ESP32 registers it
  digitalWrite(TRIGGER_PIN, LOW);
  
  Serial.println("Waiting for image data...");
  
  bool receivingImage = false;
  uint32_t imageSize = 0;
  uint32_t bytesReceived = 0;
  String headerBuffer = "";

  // Wait for the image with a timeout
  unsigned long startTime = millis();
  while (millis() - startTime < 15000) { // 15 second timeout
    while (camSerial.available() > 0) {
      if (!receivingImage) {
        // Look for our custom start marker: <<IMAGE_START:size>>
        char c = camSerial.read();
        headerBuffer += c;
        
        if (headerBuffer.endsWith(">>")) {
          int startIdx = headerBuffer.indexOf("<<IMAGE_START:");
          if (startIdx != -1) {
            int endIdx = headerBuffer.indexOf(">>", startIdx);
            String sizeStr = headerBuffer.substring(startIdx + 14, endIdx);
            imageSize = sizeStr.toInt();
            receivingImage = true;
            bytesReceived = 0;
            Serial.printf("\n[SUCCESS] Image start detected. Expected Size: %d bytes\n", imageSize);
            Serial.println("Receiving image data...");
          } else {
             // Reset buffer if it gets too long without a valid header
             if(headerBuffer.length() > 100) {
               headerBuffer = "";
             }
          }
        }
      } else {
        // Receiving actual image data
        char c = camSerial.read();
        bytesReceived++;
        
        // Here you would normally save 'c' to an SD card, LittleFS, or send it via WiFi
        // (For example: file.write(c); )
        
        // Print progress every 2000 bytes so we know it's working
        if (bytesReceived % 2000 == 0) {
          Serial.print(".");
        }

        // Check if we've received the full expected image size
        if (bytesReceived >= imageSize) {
          Serial.println("\n[SUCCESS] Full image received!");
          
          // Try to catch the <<IMAGE_END>> marker to clear the buffer
          String endBuffer = "";
          unsigned long endWait = millis();
          while(millis() - endWait < 1000) {
            if(camSerial.available()) {
               endBuffer += (char)camSerial.read();
               if(endBuffer.indexOf("<<IMAGE_END>>") != -1) {
                 Serial.println("End marker verified.");
                 break;
               }
            }
          }
          
          Serial.println("Waiting 10 seconds before next capture...");
          delay(10000); 
          return; // Restart the main loop
        }
      }
      // Reset timeout as long as we are actively receiving data
      startTime = millis(); 
    }
  }
  
  // If we reach here, it means we timed out
  if (!receivingImage) {
    Serial.println("\n[ERROR] Timeout waiting for image start marker from ESP32-CAM.");
  } else {
    Serial.printf("\n[ERROR] Timeout during transfer. Received %d of %d bytes.\n", bytesReceived, imageSize);
  }
  
  Serial.println("Retrying in 5 seconds...");
  delay(5000); 
}
