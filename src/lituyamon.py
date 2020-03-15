import asyncio
import glob
import json
import logging
import logging.config
import os
import socket
import sys
import time
import Adafruit_DHT

from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from gpiozero import CPUTemperature
from gpiozero import LED

class Monitor:
    _version = "0.5.0"
    _status = "Stopped"
    _config_file = '/etc/lituyamon.json'
    _sk_server = None
    _log = None
    _activity_led = None
    cfg = None

    def __init__(self):
        self._load_config()
        logging.config.dictConfig(self.cfg['logging'])
        #logging.basicConfig(level=logging.DEBUG)
        self._log = logging.getLogger("lituyamon.monitor")
        self._log.info('Started')
        self._sk_server = SignalK(self.cfg['signalk']['host'], self.cfg['signalk']['port'])
        activity_led_gpio = self.cfg['leds']['activity.led']['gpio']
        self._activity_led = LED(activity_led_gpio)

    def _load_config(self):
        try:
            with open(self._config_file) as cfg_file:
                self.cfg = json.load(cfg_file)
        except OSError as e:
            logging.error("Config file not opened: " + e.strerror + " " + e.filename)
    
    def start(self):
        scheduler = AsyncIOScheduler()
        self._status = "Running"
        for sensor_id in (self.cfg['sensors']).keys():
            sensor_class = self.cfg['sensors'][sensor_id]['class']
            sensor_interval = self.cfg['sensors'][sensor_id]['interval']
            sensor_gpio = self.cfg['sensors'][sensor_id].get('gpio', None)
            sensor_identifier = self.cfg['sensors'][sensor_id].get('identifier', None)
            sensor_keys = self.cfg['sensors'][sensor_id]['keys']
            self._log.info('Scheduling: %s (%s)' % (sensor_id, sensor_interval))
            scheduler.add_job(self.sample, 'interval', args = [sensor_id, sensor_class, sensor_keys, sensor_gpio, sensor_identifier], seconds=sensor_interval, max_instances=3)
        scheduler.print_jobs()
        scheduler.start()
        self._log.info('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

        # Execution will block here until Ctrl+C (Ctrl+Break on Windows) is pressed.
        try:
            asyncio.get_event_loop().run_forever()
        except (KeyboardInterrupt, SystemExit):
            pass

    def sample(self, sensor_id, sensor_class, sensor_keys, sensor_gpio=None, sensor_identifier=None):
        self._activity_led.on()
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
            self._log.warning(e)
        self._activity_led.off()

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
        self._log.debug("Enter GPIO: {}".format(gpio))

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

if __name__ == "__main__":
    m = Monitor()
    m.start()
