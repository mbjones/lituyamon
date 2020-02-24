import json
from Sensor import *

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

if __name__ == "__main__":
    m = Monitor()
    m.start()
