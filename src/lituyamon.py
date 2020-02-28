import asyncio
import json
import logging
import logging.config
import os
import socket
import sys
import time

from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from gpiozero import CPUTemperature

class Monitor:
    _version = "0.4.0"
    _status = "Stopped"
    _config_file = '/etc/lituyamon.json'
    _sk_server = None
    _log = None
    cfg = None

    def __init__(self):
        self._load_config()
        logging.config.dictConfig(self.cfg['logging'])
        #logging.basicConfig(level=logging.DEBUG)
        self._log = logging.getLogger("lituyamon.monitor")
        self._log.info('Started')
        self._sk_server = SignalK(self.cfg['signalk']['host'], self.cfg['signalk']['port'])

    def _load_config(self):
        try:
            with open(self._config_file) as cfg_file:
                self.cfg = json.load(cfg_file)
        except OSError as e:
            logging.error("Config file not opened: " + e.strerror + " " + e.filename)
    
    def start(self):
        scheduler = AsyncIOScheduler()
        self._status = "Running"
        for sensor_key in (self.cfg['sensors']).keys():
            sensor_class = self.cfg['sensors'][sensor_key]['class']
            sensor_interval = self.cfg['sensors'][sensor_key]['interval']
            self._log.info('Scheduling: %s (%s)' % (sensor_key, sensor_interval))
            scheduler.add_job(self.sample, 'interval', args = [sensor_key, sensor_class], seconds=sensor_interval, max_instances=3)
        scheduler.print_jobs()
        scheduler.start()
        self._log.info('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

        # Execution will block here until Ctrl+C (Ctrl+Break on Windows) is pressed.
        try:
            asyncio.get_event_loop().run_forever()
        except (KeyboardInterrupt, SystemExit):
            pass


    def sample(self, sensor_key, sensor_class):
        current_module = sys.modules[__name__]
        SensorClass = getattr(current_module, sensor_class)
        sensor = SensorClass()
        value = sensor.read_sensor()
        self._log.debug('%s: %s (%s)' % (sensor_key, value, datetime.now()))
        self._sk_server.send(sensor_key, value)

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

    def read_sensor(self):
        value = 1  
        return(value)


class CPUTemp(Sensor):
    _status = "Unconfigured"
    cpu = None

    def initialize(self):
        self.cpu = CPUTemperature()
        self._status = "Initialized"

    def read_sensor(self):    
        temp_c = self.cpu.temperature
        temp_k = round(temp_c + 273.15, 1)
        return(temp_k)

if __name__ == "__main__":
    m = Monitor()
    m.start()
