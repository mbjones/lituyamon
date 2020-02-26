import asyncio
import json
import os
import sys

from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from gpiozero import CPUTemperature

class Monitor:
    _version = "0.3.0"
    _status = "Stopped"
    _config_file = '/etc/lituyamon.conf'
    cfg = None

    def __init__(self):
        self._load_config()

    def _load_config(self):
        self._config_file
        try:
            with open(self._config_file) as cfg_file:
                self.cfg = json.load(cfg_file)
        except OSError as e:
            print("Config file not opened: " + e.strerror + " " + e.filename)
    
    def start(self):
        scheduler = AsyncIOScheduler()
        self._status = "Running"
        for sensor_key in (self.cfg['sensors']).keys():
            sensor_class = self.cfg['sensors'][sensor_key]['class']
            sensor_interval = self.cfg['sensors'][sensor_key]['interval']
            print('Scheduling: %s (%s)' % (sensor_key, sensor_interval))
            scheduler.add_job(lambda: self.sample(sensor_key, sensor_class), 'interval', seconds=sensor_interval)
        scheduler.print_jobs()
        scheduler.start()
        print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

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
        print('%s: %s (%s)' % (sensor_key, value, datetime.now()))


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
