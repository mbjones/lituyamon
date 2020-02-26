import unittest
from lituyamon import Monitor
from lituyamon import CPUTemp

class TestStringMethods(unittest.TestCase):

    def test_status(self):
        monitor = Monitor()
        self.assertEqual(monitor._status, 'Stopped')

    def test_config(self):
        monitor = Monitor()
        self.assertTrue(isinstance(monitor.cfg, dict))
        self.assertEqual(monitor.cfg['vessel'], 'Lituya')
        self.assertEqual(monitor.cfg['sensors']['environment.inside.lituyamon.temperature']['class'], 'CPUTemp')

    def test_read_sensor(self):
        sensor = CPUTemp()
        value = sensor.read_sensor()
        self.assertTrue(value > 315)
        self.assertTrue(value < 335)

if __name__ == '__main__':
    unittest.main()