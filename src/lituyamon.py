import asyncio
#import glob
import json
import logging
import logging.config
import os
import signal
import socket
import sys
import time
import Adafruit_DHT
import spidev
import numpy as np
import paho.mqtt.client as mqtt

from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from gpiozero import CPUTemperature
from gpiozero import LED
#from watchgod import arun_process

class Monitor:
    _status = "Stopped"
    _config_file = '/etc/lituyamon.json'
    _sk_server = None
    _log = None
    _green_led = None
    _yellow_led = None
    _red_led = None
    _jobs = None
    cfg = None

    def exit_gracefully(self, signum, frame):
        raise SystemExit('Shutdown requested with signal %s' % signum)

    def __init__(self):
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        self._load_config()
        logging.config.dictConfig(self.cfg['logging'])
        #logging.basicConfig(level=logging.DEBUG)
        self._log = logging.getLogger("lituyamon.monitor")
        self._log.info('Started')
        self._sk_server = SignalK(self.cfg['signalk']['host'], self.cfg['signalk']['port'])
        green_led_gpio = self.cfg['leds']['green.led']['gpio']
        self._green_led = LED(green_led_gpio)
        yellow_led_gpio = self.cfg['leds']['yellow.led']['gpio']
        self._yellow_led = LED(yellow_led_gpio)
        red_led_gpio = self.cfg['leds']['red.led']['gpio']
        self._red_led = LED(red_led_gpio)
        self._jobs = set()

    def _load_config(self):
        try:
            with open(self._config_file) as cfg_file:
                self.cfg = json.load(cfg_file)
        except OSError as e:
            logging.error("Config file not opened: " + e.strerror + " " + e.filename)

    # TODO: incorporate this into start() to register the watchdog
    # async def main():
    #     await arun_process('/etc/lituyamon.json', self._reload, args=(1, 2, 3))

    # def _reload(self, a, b, c):
    #     self._log.debug("_reload called.")

    def start(self):
        scheduler = AsyncIOScheduler()
        self._status = "Running"
        for sensor_id in (self.cfg['sensors']).keys():
            sensor_class = self.cfg['sensors'][sensor_id]['class']
            sensor_interval = self.cfg['sensors'][sensor_id]['interval']
            sensor_gpio = self.cfg['sensors'][sensor_id].get('gpio', None)
            sensor_identifier = self.cfg['sensors'][sensor_id].get('identifier', None)
            sensor_keys = self.cfg['sensors'][sensor_id]['keys']
            sensor_enabled = self.cfg['sensors'][sensor_id]['enabled']
            if (sensor_enabled):
                self._log.info('Scheduling: %s (%s)' % (sensor_id, sensor_interval))
                job = scheduler.add_job(self.sample, 'interval', args = [sensor_id, sensor_class, sensor_keys, sensor_gpio, sensor_identifier], seconds=sensor_interval, max_instances=3, id = sensor_id)
                self._jobs.add(sensor_id)
            else:
                self._log.debug('Sensor disabled: %s (%s)' % (sensor_id, sensor_interval))
        #scheduler.print_jobs()
        self._log.debug(str(self._jobs))
        scheduler.start()
        self._log.info('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

        self._green_led.on()
        self._yellow_led.on()
        self._red_led.on()
        # Execution will block here until Ctrl+C (Ctrl+Break on Windows) is pressed.
        try:
            loop = asyncio.get_event_loop()
            # Event loop for code after python 3.10, but still deals with earlier versions
            # import sys
            # import asyncio
            # if sys.version_info < (3, 10):
            #     loop = asyncio.get_event_loop()
            # else:
            #     try:
            #         loop = asyncio.get_running_loop()
            #     except RuntimeError:
            #         loop = asyncio.new_event_loop()
            #     asyncio.set_event_loop(loop)
            self._red_led.off()
            loop.run_forever()
        except (KeyboardInterrupt, SystemExit):
            loop.stop()
            for job_id in self._jobs:
                scheduler.remove_job(job_id=job_id)
        finally:
            loop.close()
            self._green_led.off()
            self._yellow_led.off()
            self._red_led.off()
            self._log.info("Lituyamon shut down cleanly.")

    def sample(self, sensor_id, sensor_class, sensor_keys, sensor_gpio=None, sensor_identifier=None):
        self._red_led.off()
        self._yellow_led.on()
        current_module = sys.modules[__name__]
        SensorClass = getattr(current_module, sensor_class)
        sensor = SensorClass()
        try:
            values = sensor.read_sensor(sensor_gpio, sensor_identifier)
            if len(sensor_keys) == len(values):
                i = 0
                for key in sensor_keys:
                    self._log.debug('%s: %s (%s)' % (key, values[i], datetime.now()))
                    self._sk_server.send(key, values[i])
                    i = i + 1
            else:
                self._log.warning("Omitting {}: length of sensor keys does not match number of values returned from sensor. Check the configuration file.".format(sensor_id))
        except SensorNotFoundError as e:
            self._red_led.on()
            self._log.warning(e)
            
        self._yellow_led.off()

class SignalK:
    _host = None
    _port = None
    _log = None

    def __init__(self, host, port):
        self._host = host
        self._port = int(port)
        self._log = logging.getLogger("lituyamon.signalk")

    def send(self, path, value):
        sk_delta_msg='{"updates": [{"$source": "lituyamon","values":[ {"path":"'+ path +'","value":'+ str(value) + '}]}]}\n'
        self._log.debug(sk_delta_msg.encode())
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as _sock:
            _sock.sendto(sk_delta_msg.encode(), (self._host, self._port))

class Sensor:
    _status = "Unconfigured"

    def __init__(self):
        self.initialize()

    def initialize(self):
        self._status = "Initialized"

    def read_sensor(self, gpio=None, identifier=None):
        values = [1]  
        return(values)


class CPUTemp(Sensor):
    _status = "Unconfigured"
    cpu = None

    def initialize(self):
        self.cpu = CPUTemperature()
        self._status = "Initialized"

    def read_sensor(self, gpio=None, identifier=None): 
        temp_c = self.cpu.temperature
        temp_k = round(temp_c + 273.15, 1)
        return([temp_k])

class DHT22(Sensor):
    _status = "Unconfigured"
    _log = None
    _DHT_SENSOR = Adafruit_DHT.DHT22

    def initialize(self):
        self._log = logging.getLogger("lituyamon.DHT22")
        self._status = "Initialized"

    def read_sensor(self, gpio=None, identifier=None):
        self._log.debug("Reading from GPIO: {}".format(gpio))

        humidity, temp_c = Adafruit_DHT.read_retry(self._DHT_SENSOR, gpio, retries=2)

        if humidity is not None and temp_c is not None:
            temp_k = round(temp_c + 273.15, 1)
            hum_ratio = round(humidity/100, 3)
            return([temp_k, hum_ratio])
        else:
            self._log.error("Failed to retrieve data from DHT22 sensor")
            raise SensorNotFoundError("GPIO: {}".format(gpio))

class DS18B20(Sensor):
    _status = "Unconfigured"
    _base_dir = '/sys/bus/w1/devices/'
    _log = None
    _identifer = None

    def initialize(self):
        self._log = logging.getLogger("lituyamon.DS18B20")
        self._status = "Initialized"

    def read_sensor(self, gpio=None, identifier=None):
        device_file = self._base_dir + identifier + '/w1_slave'
        self._log.debug("Reading from: {}".format(identifier))
        try:
            temp_k = self._read_temp(device_file)
        except:
            raise SensorNotFoundError(identifier)
        return([temp_k])

    def _read_temp_raw(self, device_file):
        f = open(device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines

    def _read_temp(self, device_file):
        lines = self._read_temp_raw(device_file)
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self._read_temp_raw(device_file)
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            #temp_f = temp_c * 9.0 / 5.0 + 32.0
            temp_k = round(temp_c + 273.15, 1)
            return temp_k

class MCP3008(Sensor):
    _status = "Unconfigured"
    _log = None
    spi = None

    def initialize(self):
        self._log = logging.getLogger("lituyamon.MCP3008")
        self.spi = spidev.SpiDev()
        self.spi.open(0,0)
        self.spi.max_speed_hz=1000000
        self._status = "Initialized"

    def read_sensor(self, gpio=None, identifier=None): 
        channel = int(identifier)
        levels=[]
        for i in range(100):    
            level = self._read_channel(channel)
            #self._log.debug("Channel/Level: {}/{}".format(channel, level))
            levels.append(level)
        level_avg = np.mean(levels)
        self._log.debug("Level Average: {}".format(level_avg))
        self.spi.close()
        volts = self._convert_volts(level_avg, 2)
        return([volts])

    # Read SPI data from MCP3008
    # Channel indexed from 0-7
    # MCP3008 is 10-bit, so return value is 0-1023
    def _read_channel(self, channel):
        adc = self.spi.xfer2([1, (8+channel)<<4,0])
        data = ((adc[1]&3) << 8) + adc[2]
        return data

    # Convert binary reading to voltage, rounded to places
    def _convert_volts(self, level, places):
        # volts_out = (level*3.3)/float(1023)
        # volts_out is measured after a voltage divider, so adjust
        # using calibration based on actual resistance ratio
        # this is currently based on using a 100kohm and 22.1kohm resistors,
        # and the conversion below was determined experimentally
        #volts_in = 0.019281*level - 0.001144 # first calibration, a little low but ok
        #volts_in = 0.07897*level - 40.18013  # second calibration, too high, not right
        volts_in = 0.01803*level + 1.09664 # third calibration, closer
        volts = round(volts_in, places)
        return volts
    
class MQTT(Sensor):
    _status = "Unconfigured"
    _log = None
    _identifer = None
    _mqttc = None
    _sensor_vals = {}
    _msg_received = False

    def initialize(self):
        self._log = logging.getLogger("lituyamon.MQTT")
        self._status = "Initialized"

        self._mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._mqttc.on_connect = self.on_connect
        self._mqttc.on_disconnect = self.on_disconnect
        self._mqttc.on_message = self.on_message
        self._mqttc.connect("venus.local", 1883, 60)
        self._mqttc.loop_start()


    def read_sensor(self, gpio=None, identifier=None):
        self._log.debug("Reading from: {}".format(identifier))
        self._msg_received = False
        self._mqttc.publish('R/c0619ab56440/system/0/Dc/Battery', retain=False)
        self._mqttc.publish('R/c0619ab56440/vebus/276/Ac', retain=False)
        self._mqttc.publish('R/c0619ab56440/vebus/276/Dc/0', retain=False)
        # "identifier": "N/c0619ab56440/vebus/276/Ac/Out/L1/V",
	    # "identifier": "N/c0619ab56440/vebus/276/Ac/Out/L1/P",
	    # "identifier": "N/c0619ab56440/vebus/276/Ac/Out/L1/I",
        # "identifier": "N/c0619ab56440/vebus/276/Dc/0/Temperature",
        # "identifier": "N/c0619ab56440/vebus/276/Dc/0/Voltage",
        # "identifier": "N/c0619ab56440/vebus/276/Dc/0/Power",
        # "identifier": "N/c0619ab56440/vebus/276/Dc/0/Current",
        # "identifier": "N/c0619ab56440/system/0/Dc/Battery/Soc",
        try:
            counter = 0
            # Need to wait for the async on_message callback from the above callbacks
            # Check if _msg_received is True, at least for the first mesaage
            while self._msg_received != True and counter < 10:
                counter = counter+1
                time.sleep(1)
            
            if identifier in self._sensor_vals:
                value = self._sensor_vals[identifier]
            else:
                raise SensorNotFoundError(identifier)
        except:
            raise SensorNotFoundError(identifier)
        finally:
            self._mqttc.loop_stop() # Stop polling for new sensor values
            self._mqttc.disconnect()
        return([value])

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, reason_code, properties):
        self._log.debug(f"Connected to MQTT with result code {reason_code}")
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        #client.subscribe("$SYS/#")
        client.subscribe("N/c0619ab56440/#")

    # Callback if the MQTT connection is broken
    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        if reason_code != 0:
            try:
                self._log.warning("Unexpected disconnection with rc: " + str(reason_code) + " Datetime: " + datetime.now().isoformat())
                self._log.warning("Reconnecting, please wait...")
                time.sleep(3)
            except Exception as e:
                self._log.error("General exception in MQTT with rc: " + str(reason_code))
                self._log.error(e)
        else:
            self._log.debug("Normal disconnect with rc: " + str(reason_code) + " Datetime: " + datetime.now().isoformat())

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        self._log.debug(msg.topic+" "+str(msg.payload))
        payload = json.loads(msg.payload)
        self._sensor_vals[msg.topic] = payload["value"]
        self._msg_received = True


class SensorNotFoundError(Exception):
    """Raised when attempting to read from a sensor that can not be found.

    Attributes:
        sensor -- identifier or pin of the sensor that was not found
        message -- explanation of the error
    """

    def __init__(self,  sensor, message=None):
        self.sensor = sensor
        if message is None:
            message = "Sensor not found: {}. Please check that it is connected.".format(self.sensor)
        super(SensorNotFoundError, self).__init__(message)

def main():
    m = Monitor()
    m.start()

if __name__ == "__main__":
    main()

