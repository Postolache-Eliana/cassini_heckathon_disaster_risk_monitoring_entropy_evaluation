# Cassini Project: Version History & Changelog

This document tracks the evolution of the Cassini photogrammetry rig using Semantic Versioning (SemVer).

---

## [1.0.0] - Raspberry Pi Coordinator Architecture

### Added
- `pi_coordinator.py`: Initial Python coordinator script for the Raspberry Pi Zero W.
  - Utilizes hardware UART (`/dev/serial0`) for stable 115200 baud communication.
  - Incorporates `RPi.GPIO` to manage the hardware trigger.
  - Implements a robust `readline()` parsing sequence to safely separate the custom text-based headers from the raw binary image data stream.

### Deprecated
- `esp8266_controller.ino` (Architecture pivoted to Raspberry Pi due to computational and serial buffer limitations).

---

## [0.3.0] - ESP8266 Controller Integration

### Added
- `esp8266_controller.ino`: Initial attempt at a central coordinator.
  - Configured D0 (GPIO 16) as the hardware output trigger.
  - Implemented `SoftwareSerial` on pins D1/D2 to receive the UART image stream while preserving the primary hardware serial for PC debugging.

### Known Issues
- `SoftwareSerial` at 115200 baud proved unstable for large binary transfers, leading to the v1.0.0 architecture pivot.

---

## [0.2.0] - UART Image Transmission

### Added
- Custom framing markers (`<<IMAGE_START:size>>` and `<<IMAGE_END>>`) to encapsulate the image payload.

### Changed
- `esp32cam_capture.ino`: Upgraded the firmware to stream the raw binary JPEG over the serial port using `Serial.write()` immediately after local SD card storage.

---

## [0.1.0] - Initial Camera Trigger Firmware

### Added
- `esp32cam_capture.ino`: Base firmware for the ESP32-CAM module.
- Hardware trigger setup on GPIO 14 (`INPUT_PULLDOWN`).
- Camera sensor initialization routines for the AI-Thinker module.
- Local MicroSD card saving mechanism utilizing 1-bit SD mode to prevent GPIO strapping conflicts.
