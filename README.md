# Lituya Monitor

This is a python package for monitoring systems on Lituya.

# Configuration

Configuration is accomplished through the `/etc/lituyamon.json` config file, which enables setting general vessel parameters, as well as the list of sensors to expose, and logging parameters for the application.

## Auto start as systemd service

The lituyamon python entrypoint gets installed to `/usr/local/bin/lituyamon`, and that script runs the monitoring service. It is configured to start on boot from the systemd service. This is enabled through the configuration file located in `/lib/systemd/system/lituyamond.service`. An example of this configuration file is included in the package as `etc/systemd/lituyamond.service`. To start the service, use:

```sh
sudo systemctl start lituyamond
```

To enable the service to be started automatically on boot, use:

```sh
sudo systemctl enable lituyamond
```

To see the status of the service, use:

```sh
sudo systemctl status lituyamond
```

# Current Sensors

## DS18B20 temperature sensors

The DS18B20 temperature sensor is a digital sensor that uses the 1-wire protocol for transmitting data to a digital GPIO port on the RPI.  Each sensor has its own unique digital identifier which is used by the RPI kernel module to organize a set of device files to be read from, which are located in a file `/sys/bus/w1/devices/$DEVICE_ID/w1_slave`, where `$DEVICE_ID` is the identifier of the device used s the directory name.  For Lituya, the five sensors are placed as follows:

- 28-01192d61416d - Fwd Cabin
- 28-01192d3ee042 - Aft Cabin
- 28-01192d62eb82 - Engine Block
- 28-01192d67a561 - Engine Room
- 28-01192d4fffe6 - Lazarette

Calibrating sensors is done by testing the sensors in ice water and boiling water, and using the following formula:

- CorrectedValue = (((RawValue – RawLow) * ReferenceRange) / RawRange) + ReferenceLow
- example: (((20 - 2) * 100) / 99) + 0 = 18.18

See: https://learn.adafruit.com/calibrating-sensors/two-point-calibration

## DHT22 Humidity and Temperature sensors

The DHT22 sensor is a digital temperature and humidity sensor that can can be sampled every two seconds and read off of any GPIO pin. We have two DHT22 sensors that are configured to operate as follows:

- GPIO #27 - Salon
- GPIO #28 - Engine Room

## Raspberry Pi CPU temperature

The RPI has an internal CPU temperature sensor, which we expose.

## MCP3008 A2D Converter

The MCP3008 10-bit analog to digital converter is an IC that uses SPI to communicate with the Raspberry PI and provides 8 pins for analog input. In this project, I wired the chip to use the SPI hardware ports of the pi (although it could have also been set up with software SPI with other GPIO ports). The current analog channels are connected:

- Channel 0: Pin 1 (Channel 0) is connected to a voltage divider that takes the input voltage from the house battery bank and divides it to normalize a maximum voltage value of 18V DC down to a maximum 3.3V as input to channel 0.  This is accomplished using a voltage divider with two resistors: vin -> R1 (100 kohm) -> R2 (22.1 kohm) -> GND. The vout is connected between R1 and R2. with this setup, the voltage is divided as (R2 + R3) / (R1 + R2 + R3), which is (22.1)/(100+22.1), which equals 0.181 times vin.
    - After calibrating the readings with an accurate voltmeter, I determined that the binary level values from the MCP3008 could be converted through the following linear model to actual voltages:
        - volts_in = 0.019281*level - 0.001144
    - In lituyamon, this calibrated voltage is feeding to the signalk key `electrical.batteries.house.voltage`

# Hardware shutdown using a button

Based on the writeup by Matthijs Kooijman titled [Raspberry pi powerdown and
powerup button](https://www.stderr.nl/Hardware/RaspberryPi/PowerButton.html). By
connecting a momentary switch between GPIO3 and Ground as described below, we
can shutdown the pi (if it is up) and restart it (if it is down).

- If the PI is running, shorting GPIO3 to GND will shutdown the pi using systemctl as if `halt` had been called
- Once the pi has been shutdown, it still has power, so shorting GPIO3 to GND again will boot the pi
- If the power has been pulled from the pi, reconnecting it will boot the pi as normal

All of this is enabled by adding a line to the `/boot/config.txt` file with the following details, and then reboot:

```
# Enable hardware shutdown by shorting GPIO3 to GND
dtoverlay=gpio-shutdown,gpio_pin=3
```

For lituyamon, I am wiring in a momentary switch that has 5 pins arranged like so (wire colors in parens):
        --------
      /         \
     |           |  Pin 1 = (+) LED (Brown)
     | 1       5 |  Pin 5 = (-) LED (Orange)
      \  2 3 4  /   Pin 2 = NC1: Normally closed (not used)
       ---------    Pin 3 = NO1: Normally open (Green)
                    Pin 4 =  C1: Common (Blue)

By connecting C1 to Ground and NO1 to GPIO3, then when the button is pushed, the
circuit is completed and the pi will shutdown or boot up as appropriate.

In addition, by connecting Pin 1 (+) to another GPIO pin (like GPIO16), and Pin 5
(-) to GND, the LED can be lit by turning on GPIO16. This can also be configured
as the default in `/boot/config.txt` so that the LED lights up when the pi
boots, and then shuts off during shutdown. This can be configured by adding the
following line to `config.txt` and then rebooting:

```
gpio=16=op,dh
```

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

But see the Adafruit IO Python library: https://github.com/adafruit/Adafruit_IO_Python

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

# Accessing lituyamon via openvpn

To enable systemd to start an openvpn connection on boot, use:

```bash
sudo systemctl enable openvpn-client@lituyavps
```

Where `lituyavps` refers to the name of the client openvpn connection that should be started, and that corresponds to the configuration file in `/etc/openvpn/lituyavps.conf`. How to configure openvpn is described in its documentation.
