# Monitor class

class Monitor:
    version = "0.1.0"
    status = "Stopped"

    #def __init__(self, status):
        #self.status = status

    def get_status(self):
        return(self.status)

    def set_status(self, new_status):
        self.status = new_status

    def start(self):
        print(self.get_status())


if __name__ == "__main__":
    print("Yowza")
    m = Monitor()
    m.start()
