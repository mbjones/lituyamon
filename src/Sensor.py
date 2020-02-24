from gpiozero import CPUTemperature

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
