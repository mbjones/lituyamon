# Lituya Monitor

This is a python package for monitoring systems on Lituya.

# Configuration

Configuration is accomplished through the `/etc/lituyamon.json` config file, which enables setting general vessel parameters, as well as the list of sensors to expose, and logging parameters for the application.

# Current Sensors

## DS18B20 temperature sensors

The DS18B20 temperature sensor is a digital sensor that uses the 1-wire protocol for transmitting data to a digital GPIO port on the RPI.  Each sensor has its own unique digital identifier which is used by the RPI kernel module to organize a set of device files to be read from, which are located in a file `/sys/bus/w1/devices/$DEVICE_ID/w1_slave`, where `$DEVICE_ID` is the identifier of the device used s the directory name.  For Lituya, the five sensors are placed as follows:

- 28-01192d61416d - Fwd Cabin
- 28-01192d3ee042 - Aft Cabin
- 28-01192d62eb82 - Engine Block
- 28-01192d67a561 - Engine Exhaust Elbow
- 28-01192d4fffe6 - Lazarette

## DHT22 Humidity and Temperature sensors

The DHT22 sensor is a digital temperature and humidity sensor that can can be sampled every two seconds and read off of any GPIO pin. We have two DHT22 sensors that are configured to operate as follows:

- GPIO #27 - Salon
- GPIO #28 - Engine Room

## Raspberry Pi CPU temperature

The RPI has an internal CPU temperature sensor, which we expose.

# Future Sensors

## Bilge water level

- Need to determine the SignalK key for this

## Battery voltage

- /vessels/<RegExp>/electrical/batteries/<RegExp>/voltage
  - electrical.batteries.house.voltage
  - electrical.batteries.start.voltage
  - electrical.batteries.bowthruster.voltage
  - electrical.batteries.sternthruster.voltage
- Units: V (Volt)
- Description: Voltage measured at or as close as possible to the device

## Battery current

- /vessels/<RegExp>/electrical/batteries/<RegExp>/current
  - electrical.batteries.house.current
  - electrical.batteries.start.current
  - electrical.batteries.bowthruster.current
  - electrical.batteries.sternthruster.current
- Units: A (Ampere)
- Description: Current flowing out (+ve) or in (-ve) to the device

## Battery temperature

- /vessels/<RegExp>/electrical/batteries/<RegExp>/temperature
  - electrical.batteries.house.temperature
  - electrical.batteries.start.temperature
  - electrical.batteries.bowthruster.temperature
  - electrical.batteries.sternthruster.temperature
- Units: K (Kelvin)
- Description: Temperature measured within or on the device

# Adafruit.IO

Potential site for hosting feed data.

```bash
curl -H "Content-Type: application/json" -d '{"value": 42, "lat": 23.1, "lon": "-73.3"}'  -H "X-AIO-Key: {io_key}" https://io.adafruit.com/api/v2/{username}/feeds/{feed_key}/data
```

But see the Adafruit IO Pythin library: https://github.com/adafruit/Adafruit_IO_Python

    - `pip install adafruit-io`

Sending data to an IO feed:

```python
# Import library and create instance of REST client.
from Adafruit_IO import Client
aio = Client('YOUR ADAFRUIT IO USERNAME', 'YOUR ADAFRUIT IO KEY')

# Add the value 98.6 to the feed 'Temperature'.
test = aio.feeds('test')
aio.send_data(test.key, 98.6)
```

or in a batch:

```python
# Create a data items in the 'Test' feed.
data_list = [Data(value=10), Data(value=11)]
aio.create_data('Test', data)
```


# Raspberry Pi Pinout, from pinout.xyz

![](doc/img/raspberry-pi-pinout.png)
