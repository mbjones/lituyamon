import json
from gpiozero import CPUTemperature

class Monitor:
    _version = "0.1.0"
    _status = "Stopped"
    _config_file = '/etc/lituyamon.conf'

    def __init__(self):
        self._load_config()

    def start(self):
        self._status = "Running"
        sensor = CPUTemp()
        print(sensor.read_sensor())

    def _load_config(self):
        self._config_file
        try:
            with open(self._config_file) as cfg_file:
                self.cfg = json.load(cfg_file)
        except OSError as e:
            print("Config file not opened: " + e.strerror + " " + e.filename)

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
