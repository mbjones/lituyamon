import unittest
from lituyamon.Monitor import Monitor

class TestStringMethods(unittest.TestCase):

    def test_status(self):
        monitor = Monitor()
        monitor.start()
        self.assertEqual(monitor._status, 'Running')

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

if __name__ == '__main__':
    unittest.main()