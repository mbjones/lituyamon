import asyncio
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
    _version = "0.4.0"
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
            sensor_keys = self.cfg['sensors'][sensor_id]['keys']
            self._log.info('Scheduling: %s (%s)' % (sensor_id, sensor_interval))
            if (sensor_gpio is None):
                scheduler.add_job(self.sample, 'interval', args = [sensor_id, sensor_class, sensor_keys], seconds=sensor_interval, max_instances=3)
            else:
                scheduler.add_job(self.sample, 'interval', args = [sensor_id, sensor_class, sensor_keys, sensor_gpio], seconds=sensor_interval, max_instances=3)
        scheduler.print_jobs()
        scheduler.start()
        self._log.info('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

        # Execution will block here until Ctrl+C (Ctrl+Break on Windows) is pressed.
        try:
            asyncio.get_event_loop().run_forever()
        except (KeyboardInterrupt, SystemExit):
            pass

    def sample(self, sensor_id, sensor_class, sensor_keys, sensor_gpio=None):
        self._activity_led.on()
        current_module = sys.modules[__name__]
        SensorClass = getattr(current_module, sensor_class)
        sensor = SensorClass()
        values = sensor.read_sensor(sensor_gpio)
        if len(sensor_keys) == len(values):
            i = 0
            for key in sensor_keys:
                self._log.debug('%s: %s (%s)' % (key, values[i], datetime.now()))
                self._sk_server.send(key, values[i])
                i = i + 1
        else:
            self._log.warning("Omitting {}: length of sensor keys does not match number of values returned from sensor. Check the configuration file.".format(sensor_id))
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

    def read_sensor(self, gpio=None):
        values = [1]  
        return(values)


class CPUTemp(Sensor):
    _status = "Unconfigured"
    cpu = None

    def initialize(self):
        self.cpu = CPUTemperature()
        self._status = "Initialized"

    def read_sensor(self, gpio=None): 
        temp_c = self.cpu.temperature
        temp_k = round(temp_c + 273.15, 1)
        return([temp_k])

class DHT22(Sensor):
    _status = "Unconfigured"
    _log = None
    _DHT_SENSOR = Adafruit_DHT.DHT22
    cpu = None

    def initialize(self):
        self._log = logging.getLogger("lituyamon.DHT22")
        self.cpu = CPUTemperature()
        self._status = "Initialized"

    def read_sensor(self, gpio=None):
        self._log.debug("GPIO: {}".format(gpio))

        humidity, temp_c = Adafruit_DHT.read_retry(self._DHT_SENSOR, gpio)

        if humidity is not None and temp_c is not None:
            temp_k = round(temp_c + 273.15, 1)
            hum_ratio = round(humidity/100, 3)
            return([temp_k, hum_ratio])
        else:
            self._log.error("Failed to retrieve data from DHT22 sensor")
            return(-99999)


if __name__ == "__main__":
    m = Monitor()
    m.start()
