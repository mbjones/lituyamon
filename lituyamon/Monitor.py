class Monitor:
    _version = "0.1.0"
    _status = "Stopped"

    #def __init__(self, status):
        #self._status = status

    def start(self):
        self._status = "Running"

    def _config(config_dir='/etc/lituyamon.conf'):
        print(config_dir)

if __name__ == "__main__":
    m = Monitor()
    m.start()
