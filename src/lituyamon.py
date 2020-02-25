import json
from gpiozero import CPUTemperature
import sys

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
        self._status = "Running"
        sensor = CPUTemp()
        print(sensor.read_sensor())
        for sensor_task in (self.cfg['sensors']).keys():
            print("Reading from sensor: " + sensor_task)
            sk_key = self.cfg['sensors'][sensor_task]['sk_key']
            current_module = sys.modules[__name__]
            SensorClass = getattr(current_module, self.cfg['sensors'][sensor_task]['class'])
            sensor = SensorClass()
            value = sensor.read_sensor()
            print(sk_key +": " + str(value))



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
