import sys
import os
import time
import pytest

# Add parent directory to path so we can import the coordinator script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import pi_coordinator
except ImportError:
    pytest.skip("pi_coordinator module not found", allow_module_level=True)

@pytest.fixture(scope="module")
def hardware_interfaces():
    """
    Fixture to initialize the hardware interfaces using the coordinator's setup function.
    This ensures we test the actual configuration used in production.
    """
    ser, spi = pi_coordinator.setup()
    
    if not ser or not spi:
        pytest.fail("Failed to initialize Serial or SPI hardware. Is the Pi configured correctly?")
        
    yield ser, spi
    
    # Teardown: ensure hardware connections are cleanly closed after tests
    ser.close()
    spi.close()
    pi_coordinator.GPIO.cleanup()

def test_hardware_trigger_and_gps_spi_response(hardware_interfaces):
    """
    Test that triggering the hardware results in a valid SPI payload from the T-Beam.
    """
    ser, spi = hardware_interfaces
    
    # Clear buffers
    ser.reset_input_buffer()
    
    # 1. Fire the hardware triggers simultaneously
    pi_coordinator.trigger_hardware()
    
    # 2. Immediately try to read SPI from T-Beam
    # The T-Beam's ISR should have snapped the GPS location into the SPI buffer
    gps_data = pi_coordinator.read_gps_data(spi)
    
    # 3. Assertions
    assert gps_data is not None, "SPI read failed entirely (No response from T-Beam)"
    assert "latitude" in gps_data, "SPI data malformed: Missing latitude"
    assert "longitude" in gps_data, "SPI data malformed: Missing longitude"
    
    # Even if there's no GPS fix indoors, the struct should parse to floats
    assert isinstance(gps_data["latitude"], float), "Parsed latitude is not a float"
    assert isinstance(gps_data["is_valid"], bool), "Parsed validity flag is not a boolean"

def test_hardware_uart_image_header_response(hardware_interfaces):
    """
    Test that the ESP32-CAM responds over UART with the custom header 
    after a hardware trigger.
    """
    ser, spi = hardware_interfaces
    
    # Clear buffers
    ser.reset_input_buffer()
    
    # Fire the hardware triggers
    pi_coordinator.trigger_hardware()
    
    # Wait for the image start marker
    start_time = time.time()
    header_found = False
    image_size = 0
    
    # Give the ESP32-CAM up to 5 seconds to take the picture and respond
    while time.time() - start_time < 5:
        if ser.in_waiting > 0:
            line = ser.readline()
            try:
                line_str = line.decode('utf-8', errors='ignore').strip()
                if line_str.startswith('<<IMAGE_START:'):
                    header_found = True
                    import re
                    match = re.search(r'<<IMAGE_START:(\d+)>>', line_str)
                    if match:
                        image_size = int(match.group(1))
                    break
            except Exception:
                pass # Ignore random noise
                
    assert header_found, "ESP32-CAM did not respond with IMAGE_START header over UART after trigger"
    assert image_size > 0, f"ESP32-CAM reported an invalid image size: {image_size}"
    
    # Clean up: Read the rest of the image to clear the buffer so subsequent runs don't fail
    print(f"Reading {image_size} bytes to clear buffer...")
    # Timeout will prevent hanging if size is incorrect
    ser.read(image_size) 
    time.sleep(0.5)
    ser.reset_input_buffer()

def test_hardware_uart_image_data_integrity(hardware_interfaces):
    """
    Test that the full image payload received over UART is a valid JPEG.
    """
    ser, spi = hardware_interfaces
    
    ser.reset_input_buffer()
    pi_coordinator.trigger_hardware()
    
    # Wait for the image start marker
    start_time = time.time()
    image_size = 0
    
    while time.time() - start_time < 5:
        if ser.in_waiting > 0:
            line = ser.readline()
            try:
                line_str = line.decode('utf-8', errors='ignore').strip()
                if line_str.startswith('<<IMAGE_START:'):
                    import re
                    match = re.search(r'<<IMAGE_START:(\d+)>>', line_str)
                    if match:
                        image_size = int(match.group(1))
                    break
            except Exception:
                pass
                
    if image_size == 0:
        pytest.fail("Failed to get image header for integrity test.")
        
    # Read the full image
    image_data = bytearray()
    start_time = time.time()
    while len(image_data) < image_size and (time.time() - start_time) < 15:
        if ser.in_waiting > 0:
            chunk = ser.read(min(ser.in_waiting, image_size - len(image_data)))
            image_data.extend(chunk)
            start_time = time.time() # reset timeout on successful read
            
    assert len(image_data) == image_size, f"Did not receive full image payload. Got {len(image_data)} of {image_size}"
    
    # Verify JPEG magic bytes (FF D8 FF)
    assert len(image_data) >= 3, "Payload too small to be an image"
    assert image_data[0] == 0xFF and image_data[1] == 0xD8 and image_data[2] == 0xFF, "Received data is not a valid JPEG"
    
    # Clear trailing buffer
    time.sleep(0.5)
    ser.reset_input_buffer()
