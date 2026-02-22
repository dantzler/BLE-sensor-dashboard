import time
import board
import adafruit_bmp280
import adafruit_sht31d
from adafruit_ble import BLERadio
from adafruit_ble.advertising import Advertisement, LazyObjectField
from adafruit_ble.advertising.standard import ManufacturerData, ManufacturerDataField
import _bleio
import neopixel 

# --- CONFIGURATION ---
COMPANY_ID = 0x0822
MY_ID = 0xABCD

class IOTGAdvertisement(Advertisement):
    # Flags tell the Pi "I am a discoverable device"
    # 0x06 is the standard for "General Discoverable, No BR/EDR"
    @property
    def flags(self):
        return b"\x06"

    manufacturer_data = LazyObjectField(
        ManufacturerData,
        "manufacturer_data",
        advertising_data_type=0xFF,
        company_id=COMPANY_ID,
        key_encoding="<H",
    )
    md_field = ManufacturerDataField(
        MY_ID, 
        "<hHhH", 
        field_names=("t_bmp", "p_bmp", "t_sht", "h_sht")
    )

def main():
    # 1. Initialize I2C and Sensors
    i2c = board.I2C()
    bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
    sht31d = adafruit_sht31d.SHT31D(i2c)
    
    # 2. Initialize BLE
    ble = BLERadio()
    advertisement = IOTGAdvertisement()
    
    # Create Name: "IG" + last 4 hex of MAC address
    addr_bytes = _bleio.adapter.address.address_bytes
    name_suffix = "{:02X}{:02X}".format(addr_bytes[5], addr_bytes[4])
    ble.name = "IG" + name_suffix
    
    # 3. Setup NeoPixel
    pixels = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.1, auto_write=False)

    print(f"Starting Broadcast as: {ble.name}")

    while True:
        try:
            # Read Values
            temp_bmp = bmp280.temperature
            press_bmp = bmp280.pressure
            temp_sht = sht31d.temperature
            humid_sht = sht31d.relative_humidity

            # Encode Values for Struct
            # Temp * 10 allows 1 decimal place of precision (e.g. 22.5 -> 225)
            t_bmp_enc = int(temp_bmp * 10)
            p_bmp_enc = int(press_bmp)
            t_sht_enc = int(temp_sht * 10)
            h_sht_enc = int(humid_sht)

            print(f"BMP: {temp_bmp:.1f}C, {press_bmp:.0f}hPa | SHT: {temp_sht:.1f}C, {humid_sht:.0f}%")

            # Update Advertisement Data
            # Note: We stop and start advertising to ensure the data updates on the air
            ble.stop_advertising()
            advertisement.md_field = (t_bmp_enc, p_bmp_enc, t_sht_enc, h_sht_enc)
            ble.start_advertising(advertisement, interval=0.2)
            
            # Visual feedback (Blink Blue)
            pixels.fill((0, 0, 255))
            pixels.show()
            time.sleep(0.1)
            pixels.fill((0, 0, 0))
            pixels.show()

        except Exception as e:
            print(f"Sensor/BLE Error: {e}")

        # Broadcast interval
        time.sleep(2)

if __name__ == "__main__":
    main()