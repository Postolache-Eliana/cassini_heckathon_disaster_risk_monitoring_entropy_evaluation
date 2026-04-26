import serial
import RPi.GPIO as GPIO
import time
import re
import os
import spidev
import struct
import json

# Configuration
CAMERA_TRIGGER_PIN = 17       # BCM GPIO 17 for ESP32-CAM
GNSS_TRIGGER_PIN = 27         # BCM GPIO 27 for T-Beam GNSS
SERIAL_PORT = '/dev/serial0'  # Default hardware UART on Pi Zero W
BAUD_RATE = 115200
TIMEOUT = 15                  # Serial timeout in seconds

def setup():
    # Setup GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(CAMERA_TRIGGER_PIN, GPIO.OUT)
    GPIO.setup(GNSS_TRIGGER_PIN, GPIO.OUT)
    GPIO.output(CAMERA_TRIGGER_PIN, GPIO.LOW)
    GPIO.output(GNSS_TRIGGER_PIN, GPIO.LOW)
    
    # Setup Serial
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
        ser.reset_input_buffer()
    except Exception as e:
        print(f"Error opening serial port {SERIAL_PORT}: {e}")
        return None, None
        
    # Setup SPI for T-Beam GNSS
    try:
        spi = spidev.SpiDev()
        spi.open(0, 0) # bus 0, device 0 (CE0)
        spi.max_speed_hz = 1000000 # 1 MHz
        spi.mode = 0
    except Exception as e:
        print(f"Error opening SPI: {e}. Make sure SPI is enabled in raspi-config.")
        spi = None

    return ser, spi

def trigger_hardware():
    print("\nTriggering ESP32-CAM and T-Beam simultaneously...")
    # Assert both high at the exact same time
    GPIO.output(CAMERA_TRIGGER_PIN, GPIO.HIGH)
    GPIO.output(GNSS_TRIGGER_PIN, GPIO.HIGH)
    time.sleep(0.2)  # Hold high for 200ms to ensure ESP32 registers it
    GPIO.output(CAMERA_TRIGGER_PIN, GPIO.LOW)
    GPIO.output(GNSS_TRIGGER_PIN, GPIO.LOW)

def read_gps_data(spi):
    if not spi:
        return None
        
    # We expect 16 bytes: 3 floats (lat, lon, alt), 1 uint8 (valid), 3 padding bytes
    # To read from SPI slave, we just transfer dummy bytes to clock the data out.
    dummy_bytes = [0x00] * 16
    try:
        response = spi.xfer2(dummy_bytes)
        
        # Unpack the struct: 'fffB3x' (little-endian: '<')
        data = struct.unpack('<fffB3x', bytearray(response))
        lat = data[0]
        lon = data[1]
        alt = data[2]
        is_valid = bool(data[3])
        
        gps_info = {
            "latitude": lat,
            "longitude": lon,
            "altitude": alt,
            "is_valid": is_valid,
            "timestamp": time.time()
        }
        
        if is_valid:
            print(f"[GPS] Lat: {lat:.6f}, Lon: {lon:.6f}, Alt: {alt:.2f}m")
        else:
            print("[GPS] No valid fix yet.")
            
        return gps_info
    except Exception as e:
        print(f"Error reading SPI: {e}")
        return None

def receive_image_and_gps(ser, spi, image_index):
    print("Waiting for image start marker...")
    start_time = time.time()
    
    # Read line by line until we find the start marker
    while time.time() - start_time < TIMEOUT:
        if ser.in_waiting > 0:
            line = ser.readline()
            try:
                line_str = line.decode('utf-8', errors='ignore').strip()
                if line_str.startswith('<<IMAGE_START:'):
                    match = re.search(r'<<IMAGE_START:(\d+)>>', line_str)
                    if match:
                        image_size = int(match.group(1))
                        print(f"[SUCCESS] Image start detected. Expected Size: {image_size} bytes")
                        
                        # At the moment the image capture starts transferring, fetch the GPS data
                        gps_data = read_gps_data(spi)
                        
                        return read_image_data(ser, image_size, image_index, gps_data)
            except Exception as e:
                pass 
                
    print("[ERROR] Timeout waiting for image start marker from ESP32-CAM.")
    return False

def read_image_data(ser, expected_size, image_index, gps_data):
    print("Receiving image data...")
    image_data = bytearray()
    
    start_time = time.time()
    last_print = 0
    
    while len(image_data) < expected_size and (time.time() - start_time) < TIMEOUT:
        if ser.in_waiting > 0:
            remaining = expected_size - len(image_data)
            chunk = ser.read(min(ser.in_waiting, remaining))
            image_data.extend(chunk)
            start_time = time.time()
            
            if len(image_data) - last_print > 5000:
                print(f"Received {len(image_data)} / {expected_size} bytes...")
                last_print = len(image_data)
                
    if len(image_data) >= expected_size:
        print(f"[SUCCESS] Full image received ({len(image_data)} bytes)!")
        
        os.makedirs('dataset', exist_ok=True)
        
        # Save the image
        img_filename = f"dataset/capture_{image_index}.jpg"
        with open(img_filename, 'wb') as f:
            f.write(image_data)
        
        # Save the GPS metadata
        if gps_data:
            meta_filename = f"dataset/capture_{image_index}.json"
            with open(meta_filename, 'w') as f:
                json.dump(gps_data, f, indent=4)
                
        print(f"Saved image to {img_filename} and metadata to json.")
        
        # Try to read the end marker to clear the buffer
        time.sleep(0.5)
        if ser.in_waiting > 0:
            ser.reset_input_buffer()
                
        return True
    else:
        print(f"[ERROR] Timeout during transfer. Received {len(image_data)} of {expected_size} bytes.")
        return False

def main():
    print("--- Pi Zero W Coordinator (Image + GNSS) ---")
    ser, spi = setup()
    if not ser:
        print("Failed to initialize Serial. Exiting...")
        return
        
    image_index = 0
    try:
        while True:
            trigger_hardware()
            success = receive_image_and_gps(ser, spi, image_index)
            if success:
                image_index += 1
                
            print("Waiting 10 seconds before next capture...")
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nExiting cleanly...")
    finally:
        GPIO.cleanup()
        if ser: ser.close()
        if spi: spi.close()

if __name__ == "__main__":
    main()
