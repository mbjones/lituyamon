import unittest
from lituyamon.Monitor import Monitor

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

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

if __name__ == '__main__':
    unittest.main()