# Cassini Project: Version History & Changelog

This document tracks the evolution of the Cassini photogrammetry rig using Semantic Versioning (SemVer).

---

## [1.2.0] - Split Trigger Hardware Constraint Resolution

### Added
- Defined separate output pins in `pi_coordinator.py` to accommodate Pi Zero hardware layout constraints: `CAMERA_TRIGGER_PIN = 17` and `GNSS_TRIGGER_PIN = 27`.
- Implemented `trigger_hardware()` function to assert both pins `HIGH` simultaneously in software, ensuring synchronous activation without requiring spliced wiring.

### Changed
- Refactored the coordinator's main execution loop to utilize the new dual-trigger system.

---

## [1.1.1] - Hardware-Level GNSS Synchronization

### Added
- Implemented a hardware interrupt (ISR) on GPIO 14 of the TTGO T-Beam.

### Changed
- Modified the SPI buffer population logic in `tbeam_spi_gnss.ino`. The GNSS state is no longer continuously piped to the SPI DMA buffer. Instead, the exact coordinate position is "snapped" into the buffer only when the ISR fires.
- This guarantees microsecond-level synchronization between the shutter firing on the ESP32-CAM and the spatial location recorded by the T-Beam.

---

## [1.1.0] - High-Speed SPI GNSS & GPU Acceleration

### Added
- `tbeam_spi_gnss.ino`: New Arduino firmware for the LilyGO TTGO T-Beam v1.1.
  - Initializes the AXP192 PMIC to route power to the onboard NEO-6M module.
  - Parses incoming NMEA sentences via UART1.
  - Configures the ESP32 as an SPI Slave serving a packed 16-byte `GpsData` struct (Latitude, Longitude, Altitude, Validity).
- `fast_shader.glsl`: Custom GLSL fragment shader performing a FAST-9 segment test.
- `gpu_fast_corners.py`: Proof-of-concept Python implementation utilizing `moderngl` (EGL) to execute the FAST corner shader on the Pi Zero's VideoCore IV GPU.

### Changed
- `pi_coordinator.py`: Integrated the `spidev` library. The Pi now acts as an SPI Master, clocking out the 16-byte GNSS payload at the exact moment a UART image transfer initiates, saving the metadata as a paired `.json` file.

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
