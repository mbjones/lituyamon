import unittest
from lituyamon.Monitor import Monitor
from lituyamon.Sensor import CPUTemp

class TestStringMethods(unittest.TestCase):

    def test_status(self):
        monitor = Monitor()
        monitor.start()
        self.assertEqual(monitor._status, 'Running')

    def test_config(self):
        monitor = Monitor()
        self.assertTrue(isinstance(monitor.cfg, dict))
        self.assertEqual(monitor.cfg['lituyamon']['version'], '0.2.0')
        self.assertEqual(monitor.cfg['sensors']['cputemp1']['class'], 'CPUTemperature')

    def test_read_sensor(self):
        sensor = CPUTemp()
        value = sensor.read_sensor()
        self.assertTrue(value > 315)
        self.assertTrue(value < 335)

if __name__ == '__main__':
    unittest.main()